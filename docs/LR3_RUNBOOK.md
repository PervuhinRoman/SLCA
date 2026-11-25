# LR3_RUNBOOK — контейнеризация StudentLedger

Рабочая инструкция для ЛР3: три ВМ, Docker, Docker Compose, PostgreSQL
с постоянным томом и проверка сохранности данных.

## 1. Стенды

| Стенд | ВМ VirtualBox | Hostname | Внутренний IP | SSH с хоста |
|---|---|---|---|---|
| TEST | `studentledger-test` | studentledger-test | 192.168.56.11 | 127.0.0.1:2221 |
| STAGE | `studentledger-stage` | studentledger-stage | 192.168.56.12 | 127.0.0.1:2222 |
| PROD | `studentledger-prod` | studentledger-prod | 192.168.56.13 | 127.0.0.1:2223 |

Параметры: Ubuntu Server 24.04 LTS, 2 vCPU, 3 ГБ RAM, диск 20 ГБ,
`nic1` NAT, `nic2` host-only `192.168.56.0/24`, MAC `08:00:27:51:a0:01..03`.
Пользователь `student`. Статический адрес задаётся netplan по MAC
(`scripts/lr02/netplan-192.168.56.1x-*.yaml`), DHCP в host-only сегменте выключен.

## 2. Создание ВМ на хосте

Образ: `ubuntu-24.04.5-live-server-amd64.iso` (проверить SHA256 по
`SHA256SUMS` с releases.ubuntu.com).

```powershell
# один раз: host-only адаптер
VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.56.1 --netmask 255.255.255.0
VBoxManage dhcpserver modify --ifname "VirtualBox Host-Only Ethernet Adapter" --disable

# для каждого стенда (пример TEST)
VBoxManage createvm --name studentledger-test --ostype Ubuntu24_LTS_64 --register
VBoxManage modifyvm studentledger-test --memory 3072 --cpus 2 --vram 64 --nic1 nat --nic2 hostonly --hostonlyadapter2 "VirtualBox Host-Only Ethernet Adapter" --macaddress2 08002751a001 --natpf1 "ssh,tcp,127.0.0.1,2221,,22" --audio none
VBoxManage createmedium disk --filename "$env:USERPROFILE\VirtualBox VMs\studentledger-test\studentledger-test.vdi" --size 20480 --format VDI
VBoxManage storagectl studentledger-test --name SATA --add sata --controller IntelAhci
VBoxManage storageattach studentledger-test --storagectl SATA --port 0 --device 0 --type hdd --medium "...\studentledger-test.vdi"
VBoxManage unattended install studentledger-test --iso=...\ubuntu-24.04.5-live-server-amd64.iso --user=student --password=... --full-user-name="Student" --hostname=studentledger-test --locale=en_US --country=RU --time-zone=Europe/Moscow --install-additions --start-vm=headless
```

Повторить для STAGE (`...a002`, порт 2222) и PROD (`...a003`, порт 2223).

## 3. Docker на каждой ВМ

Скрипт `scripts/lr03/install-docker.sh` (запуск с `sudo bash`):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker student
```

Проверка на каждой ВМ:

```bash
docker --version
docker compose version
sudo docker run --rm hello-world
```

Если `hello-world` не загружается, проверить доступ к Docker Hub и повторить
позже; без этого ЛР4 (push/pull) невозможна.

## 4. Развёртывание на TEST

```bash
git clone --branch feature/lr3-docker-and-app https://github.com/PervuhinRoman/SLCA.git
cd SLCA
cp .env.example .env
# задать POSTGRES_PASSWORD и JWT_SECRET (>= 32 символов), остальное можно оставить
docker compose up -d --build
docker compose ps
```

Создание администратора:

```bash
docker compose exec -e ADMIN_PASSWORD='<пароль>' app python -m app.cli create-admin --login admin
```

Проверка: `http://192.168.56.11:8000/login` (с хоста — после настройки
host-only адаптера), вход `admin`, добавление студента.

## 5. Демонстрация сохранности данных (DATA-04)

1. Войти администратором, добавить студента (например, «Петров Пётр,
   2024, очная, 241-3211»), убедиться, что запись в списке.
2. Проверить запись в БД:

```bash
docker compose exec db psql -U studentledger -d studentledger -c "select last_name, first_name, group_name from students;"
```

3. Остановить и удалить контейнеры, **не удаляя том**:

```bash
docker compose down
docker volume ls
```

4. Поднять заново:

```bash
docker compose up -d
docker compose ps
```

5. Обновить страницу `/students`: запись на месте. Повторить SQL-запрос.

## 6. Evidence (скриншоты)

1. Менеджер VirtualBox с тремя работающими ВМ.
2. `hostnamectl`/IP на каждой ВМ (или `docker --version` на трёх).
3. `docker compose ps` на TEST: `app` и `db` в состоянии `running/healthy`.
4. Страница входа и список студентов после добавления.
5. SQL-запрос к таблице `students` внутри контейнера `db`.
6. `docker compose down`, `docker volume ls`, `docker compose up -d`.
7. Список студентов после перезапуска — запись сохранена.
8. `docker volume inspect studentledger_pgdata` (точка монтирования).

## 7. Ограничения и типовые ошибки

- Порт 8000 публикуется только у приложения; порт PostgreSQL наружу не
  публикуется (SEC-02).
- `.env` не коммитится; в репозитории только `.env.example`.
- Если `docker compose up` не стартует app: `docker compose logs app` —
  приложение ждёт PostgreSQL и повторяет миграции до 30 раз.
- При смене пароля БД после первого запуска том нужно пересоздать
  (`docker compose down -v`) либо менять пароль внутри PostgreSQL.
- Для ЛР4 образ должен быть опубликован в Docker Hub; тег задаётся при сборке.

## 8. Связь с требованиями

FR-01/FR-02 — список и добавление студента; FR-11/FR-12 — вход, обновление
сессии и выход; SEC-01/07/08/09/10 — аутентификация, JWT, хеши, RBAC, аудит;
SEC-02 — БД без публикации порта; DATA-04 — сохранность после перезапуска.
