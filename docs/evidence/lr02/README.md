# ЛР2 — фактические подтверждения

Статус: **реальные ВМ созданы и проверены на хосте текущего исполнителя
2026-10-09/10; повторная проверка со скриншотами выполнена 17.10.2026,
параметры ВМ подтверждены выводом `VBoxManage` 22.10.2026**.
Ниже — только то, что подтверждено выполнением команд.

2026-10-09: текущий исполнитель подтвердил доступность локального
`http://127.0.0.1:8000/health` сообщением «есть» после повторного запуска.
Это подтверждение локального просмотра, не выполнение пунктов clone/запуск/
health на TEST; сами пункты по ВМ подтверждены файлами ниже.

## Итог проверки трёх стендов (2026-10-10)

| Стенд | Hostname | Внутренний IP | MAC внутренней сети | ОС / ядро |
|---|---|---|---|---|
| TEST | `studentledger-test` | 192.168.56.11/24 | 08:00:27:51:a0:01 | Ubuntu 24.04.5 LTS / 6.8.0-146 |
| STAGE | `studentledger-stage` | 192.168.56.12/24 | 08:00:27:51:a0:02 | Ubuntu 24.04.5 LTS / 6.8.0-146 |
| PROD | `studentledger-prod` | 192.168.56.13/24 | 08:00:27:51:a0:03 | Ubuntu 24.04.5 LTS / 6.8.0-146 |

- Гипервизор: Oracle VirtualBox 7.2.20 на Windows 10 Pro 22H2 (ADR-016).
- Ресурсы каждой ВМ: 2 vCPU, 3072 МБ RAM, 20 ГБ диска, видеопамять 64 МБ
  (ADR-017; вывод `VBoxManage` — `vm-params.txt`).
- Графический интерфейс: `xubuntu-desktop-minimal` + `lightdm` (ADR-019).
- Приложение: служба `studentledger.service` (`enabled`, `active`) на всех трёх
  ВМ; на TEST она отвечает на `http://192.168.56.11:8000/health` (пункт
  методички), на STAGE/PROD развёрнута тем же способом.
- Клон репозитория на всех трёх ВМ: `origin` = SLCA, ветка `master`,
  commit `816ac3eca4fcf73d2de12a65b907916a97fcaeee`; Python 3.12.3;
  `.venv` + `pip check` → `No broken requirements found`.

## Скриншоты проверки 17.10.2026

Снимки сделаны в графических сессиях гостевых систем (`VBoxManage controlvm
screenshotpng`) при выполнении команд в терминале; все три ВМ сняты одинаковым
способом. Даты на снимках — 17.10.2026.

| Файл | Что подтверждает |
|---|---|
| `00-vms-manager.png` | менеджер VirtualBox: три ВМ в состоянии «Работает», версия 7.2.20 и параметры выбранной машины |
| `05-test-system.png` | TEST: hostname, Ubuntu 24.04.5 LTS, ядро 6.8.0-146, x86-64, адрес 192.168.56.11/24, Git 2.43.0, Python 3.12.3 |
| `06-stage-system.png` | STAGE: то же для адреса 192.168.56.12 |
| `07-prod-system.png` | PROD: то же для адреса 192.168.56.13 |
| `08-test-ping.png` | 4/4 пакета, 0 % потерь: TEST → STAGE и TEST → PROD |
| `09-stage-ping.png` | STAGE → TEST и STAGE → PROD |
| `10-prod-ping.png` | PROD → TEST и PROD → STAGE |
| `11-test-clone.png` | `git remote -v`, ветка `master`, commit `816ac3e…` на TEST |
| `12-test-service.png` | `pip check` → `No broken requirements found`; служба `enabled`, `active` |
| `13-test-health.png` | `curl -i http://192.168.56.11:8000/health` → HTTP/1.1 200 OK, `{"status":"ok"}` |

## Файлы подтверждений

| Файл | Что подтверждает |
|---|---|
| `iso-sha256-host.txt` | SHA256 образа совпадает с официальным SHA256SUMS Ubuntu |
| `host-view.txt` | вид с хоста: версия VirtualBox, три работающие ВМ, адреса, ping хост→ВМ, HTTP 200 с каждой ВМ, netplan гостей |
| `vm-params.txt` | фактические параметры из `VBoxManage`: 3072 МБ RAM, 64 МБ видео, VDI 20480 МБ у каждой ВМ, адаптеры NAT + host-only и MAC |
| `test-full.txt`, `stage-full.txt`, `prod-full.txt` | система, инструменты, GUI, память, сеть, служба и `/health`, клон, **шесть ping** (4 пакета, 0 % потерь) |
| `01-test-console.png` | консоль TEST |
| `02-test-gui.png`, `03-stage-gui.png`, `04-prod-gui.png` | экраны входа Xubuntu с hostname соответствующей ВМ |
| `00-vms-manager.png`, `05-…13-….png` | скриншоты повторной проверки (таблица выше) |
| `unattended-install-test.log` | автоматическая установка TEST |
| `install-wait-test.log`, `install-wait-stage-prod.log`, `install-memory-watch.log`, `progress-stage-prod.log` | ход установки и контроль памяти |
| `provision-test-watch.log`, `provision-stage-prod-watch.log` | ход настройки стендов |
| `agent-local-check.txt` | прежняя локальная проверка прототипа (не ВМ) |

## Checklist

- [x] `01-vms` — три включённые ВМ и версия гипервизора:
      `00-vms-manager.png` и `host-view.txt`.
- [x] `02-test-system` — ОС, архитектура, hostname, IP:
      `05-test-system.png` и `test-full.txt`.
- [x] `03-stage-system` — `06-stage-system.png` и `stage-full.txt`.
- [x] `04-prod-system` — `07-prod-system.png` и `prod-full.txt`.
- [x] `05-07-tools` — Git, Python, venv на всех стендах:
      `05-…07-system.png` и те же три текстовых файла.
- [x] `08-test-ping` — TEST → STAGE и PROD: `08-test-ping.png`.
- [x] `09-stage-ping` — STAGE → TEST и PROD: `09-stage-ping.png`.
- [x] `10-prod-ping` — PROD → TEST и STAGE: `10-prod-ping.png`.
- [x] `11-test-clone` — реальный git clone, ветка, commit SHA:
      `11-test-clone.png` и `test-full.txt`.
- [x] `12-test-start` — зависимости, `pip check`, служба и запуск:
      `12-test-service.png`.
- [x] `13-health` — HTTP 200 и JSON: `13-test-health.png`, `test-full.txt`
      и `host-view.txt`.

Отличие от исходного плана: установка ОС выполнялась автоматически
(`VBoxManage unattended install`), поэтому кадров ручного установщика нет.
Вместо них — лог установки и экраны консоли. Если методичка требует именно
кадры ручной установки, их должен снять человек при повторной установке.

## Данные о стендах

```text
Дата выполнения: 2026-10-09 — 2026-10-10; повторная проверка 17.10.2026
Хост (ОС, архитектура, RAM): Windows 10 Pro 22H2, amd64, 8 логических ядер, 16 ГБ
Гипервизор и версия: Oracle VirtualBox 7.2.20 r175154
Образ ОС и версия: ubuntu-24.04.5-live-server-amd64.iso (SHA256 сверен)
Сетевая схема, имя сегмента: NAT + VirtualBox Host-Only, 192.168.56.0/24
TEST hostname / IP / ресурсы: studentledger-test / 192.168.56.11 / 2 vCPU, 3072 МБ, 20 ГБ
STAGE hostname / IP / ресурсы: studentledger-stage / 192.168.56.12 / 2 vCPU, 3072 МБ, 20 ГБ
PROD hostname / IP / ресурсы: studentledger-prod / 192.168.56.13 / 2 vCPU, 3072 МБ, 20 ГБ
Remote URL (без секретов): https://github.com/PervuhinRoman/SLCA.git
Branch / commit SHA: master / 816ac3eca4fcf73d2de12a65b907916a97fcaeee
Environment: Ubuntu 24.04.5 LTS, Python 3.12.3, XFCE + LightDM
Commands executed: docs/LR2_RUNBOOK.md, scripts/lr02/*
Result: 6/6 ping успешны; инструменты на 3 ВМ; clone и pip check на 3 ВМ;
        служба studentledger.service активна; /health = HTTP 200 {"status":"ok"}
Problems: не зафиксированы; приложение проверяется по прямому внутреннему
        адресу, проброс порта на хост не используется
Screenshots: 00-vms-manager.png, 05-…13-….png, 01-…04-….png
```

## Отчёт

Отчёт ЛР2 создан: `docs/reports/ЛР2, Первухин Роман, 241-3211.docx`
и его PDF-представление. Скриншоты проверки 17.10.2026 встроены в отчёт как
рисунки 1–10. Перед сдачей человеку нужно просмотреть документ и подтвердить
Human DoD по `LABS_PLAN.md`.
