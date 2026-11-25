# LR4_RUNBOOK — непрерывная интеграция StudentLedger

Инструкция для ЛР4: TeamCity Server на TEST, сборка Docker-образа для всех
веток, публикация образа в Docker Hub для `dev` и `prod`.

## 1. Что должно быть готово

- TEST: Ubuntu 24.04.5, Docker 29.x, Compose v5.x, IP `192.168.56.11`.
- Аккаунт Docker Hub и access token с правом записи.
- Репозиторий `https://github.com/PervuhinRoman/SLCA.git` (публичный).
- Свободно не менее 10 ГБ на диске TEST: образ TeamCity Server занимает
  около 4,6 ГБ, агент — около 2 ГБ.

## 2. TeamCity Server

```bash
docker run -d --name teamcity-server --restart unless-stopped \
  -p 8111:8111 \
  -v teamcity_data:/data/teamcity_server/datadir \
  -v teamcity_logs:/opt/teamcity/logs \
  jetbrains/teamcity-server:latest
```

Первый запуск: открыть `http://192.168.56.11:8111`, пройти мастер
(Data Directory → Internal HSQLDB → лицензия → администратор).
Для стенда используется внутренняя БД; для промышленной эксплуатации
нужен внешний PostgreSQL.

Проверка: `http://192.168.56.11:8111/app/rest/server` с учётными данными
администратора возвращает версию сервера.

## 3. Постоянный токен для REST

Basic-auth POST в TeamCity защищён от CSRF, поэтому для настройки нужен
Bearer-токен суперпользователя:

```bash
TOKEN=$(openssl rand -hex 24)
printf '%s' "$TOKEN" > /tmp/superuser.token
docker cp /tmp/superuser.token teamcity-server:/data/teamcity_server/datadir/config/superUser.token
docker restart teamcity-server
```

Токен хранится только на стенде и передаётся скрипту через переменную
`TEAMCITY_TOKEN`; в Git он не попадает.

## 4. Создание проекта и конфигурации

```bash
TEAMCITY_URL=http://192.168.56.11:8111 \
TEAMCITY_TOKEN=$TOKEN \
DOCKERHUB_USER=<login> \
DOCKERHUB_TOKEN=<access token> \
python3 ci/teamcity/bootstrap.py
```

Скрипт создаёт:

- проект `StudentLedger`;
- VCS-корень `SLCA_GitHub` на публичный репозиторий, branch spec
  `+:refs/heads/*`, ветка по умолчанию `dev`;
- конфигурацию `Build and push image` с двумя шагами;
- параметры `DOCKERHUB_USER`, `DOCKERHUB_TOKEN` (пароль) и
  `env.DOCKER_BUILDKIT=1`;
- VCS-триггер на все ветки.

Шаг «Build image» собирает образ
`<login>/studentledger:<build number>` и тег ветки. Шаг «Push image»
выполняет `docker login` и `docker push` только для веток `dev` и `prod`;
для feature-веток шаг завершается сообщением без публикации.

## 5. Агент сборки

Образ агента: `ci/teamcity/Dockerfile.agent` — официальный
`jetbrains/teamcity-agent` с Docker CLI и SSH-клиентом.

```bash
git clone --branch feature/lr4-teamcity-ci https://github.com/PervuhinRoman/SLCA.git
cd SLCA
docker build -f ci/teamcity/Dockerfile.agent -t studentledger-teamcity-agent .

docker run -d --name teamcity-agent --restart unless-stopped \
  -e SERVER_URL=http://192.168.56.11:8111 \
  -e AGENT_NAME=test-agent \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v teamcity_agent_conf:/data/teamcity_agent/conf \
  studentledger-teamcity-agent
```

В TeamCity: Agents → `test-agent` → Authorize. Требование к агенту —
наличие Docker CLI; проверяется шагом сборки.

## 6. Проверка ЛР4

1. Ветка `dev`: VCS-триггер запускает сборку, оба шага зелёные, образ
   появляется в Docker Hub с тегами `<build number>` и `dev`.
2. Ветка `prod`: сборка и push с тегом `prod`.
3. Feature-ветка: сборка зелёная, push не выполняется (сообщение в логе).
4. В Docker Hub видны теги `dev`, `prod` и номер сборки.

## 7. Evidence

- скриншот TeamCity: проект, конфигурация, список агентов;
- лог успешной сборки `dev` с шагами build/push;
- лог feature-сборки без push;
- страница Docker Hub с тегами образа;
- `docker pull <login>/studentledger:dev` на отдельной машине.

## 8. Ограничения

- Внутренняя HSQLDB TeamCity подходит для учебного стенда; для production
  нужен PostgreSQL и резервное копирование.
- Агент получает доступ к Docker хоста через смонтированный сокет; это
  эквивалентно root-доступу к TEST и недопустимо в production без
  отдельного изолированного агента.
- Токен Docker Hub и токен TeamCity не коммитятся; при утечке токен
  отзывается в Docker Hub.
