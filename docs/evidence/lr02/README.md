# ЛР2 — фактические подтверждения

Статус: **реальные ВМ созданы и проверены на хосте текущего исполнителя
2026-10-09/10**. Ниже — только то, что подтверждено выполнением команд.
Пункты, требующие ручных скриншотов человека, отмечены отдельно.

2026-10-09: текущий исполнитель подтвердил доступность локального
`http://127.0.0.1:8000/health` сообщением «есть» после повторного запуска.
Скриншот не предоставлен. Это подтверждение локального просмотра,
не выполнение пунктов clone/запуск/health на TEST.

## Итог проверки трёх стендов (2026-10-10)

| Стенд | Hostname | Внутренний IP | MAC внутренней сети | ОС / ядро |
|---|---|---|---|---|
| TEST | `studentledger-test` | 192.168.56.11/24 | 08:00:27:51:a0:01 | Ubuntu 24.04.5 LTS / 6.8.0-146 |
| STAGE | `studentledger-stage` | 192.168.56.12/24 | 08:00:27:51:a0:02 | Ubuntu 24.04.5 LTS / 6.8.0-146 |
| PROD | `studentledger-prod` | 192.168.56.13/24 | 08:00:27:51:a0:03 | Ubuntu 24.04.5 LTS / 6.8.0-146 |

- Гипервизор: Oracle VirtualBox 7.2.20 на Windows 10 Pro 22H2 (ADR-013).
- Ресурсы каждой ВМ: 2 vCPU, 3 ГБ RAM, диск 25 ГБ, видеопамять 64 МБ (ADR-014).
- Графический интерфейс: `xubuntu-desktop-minimal` + `lightdm` (ADR-016).
- Приложение: служба `studentledger.service` (`enabled`, `active`) на всех трёх
  ВМ; на TEST она отвечает на `http://192.168.56.11:8000/health` (пункт
  методички), на STAGE/PROD развёрнута тем же способом.
- Клон репозитория на всех трёх ВМ: `origin` = SLCA, ветка `master`,
  commit `816ac3eca4fcf73d2de12a65b907916a97fcaeee`; Python 3.12.3;
  `.venv` + `pip check` → `No broken requirements found`.

## Файлы подтверждений

| Файл | Что подтверждает |
|---|---|
| `iso-sha256-host.txt` | SHA256 образа совпадает с официальным SHA256SUMS Ubuntu |
| `host-view.txt` | вид с хоста: версия VirtualBox, три работающие ВМ, адреса, ping хост→ВМ, HTTP 200 с каждой ВМ, netplan гостей |
| `test-full.txt`, `stage-full.txt`, `prod-full.txt` | система, инструменты, GUI, память, сеть, служба и `/health`, клон, **шесть ping** (4 пакета, 0% потерь) |
| `01-test-console.png` | консоль TEST |
| `02-test-gui.png`, `03-stage-gui.png`, `04-prod-gui.png` | экраны входа Xubuntu с hostname соответствующей ВМ |
| `unattended-install-test.log` | автоматическая установка TEST |
| `install-wait-test.log`, `install-wait-stage-prod.log`, `install-memory-watch.log`, `progress-stage-prod.log` | ход установки и контроль памяти |
| `provision-test-watch.log`, `provision-stage-prod-watch.log` | ход настройки стендов |
| `vbox-test-installer-crash.png` + `install-memory-watch.log` | факт и причина сбоя первой установки (ADR-019) |
| `agent-local-check.txt` | прежняя локальная проверка прототипа (не ВМ) |

## Checklist

- [x] `01-vms` — три включённые ВМ и версия гипервизора: `host-view.txt`
      (список running VMs, версия 7.2.20) + три PNG-экрана консолей.
- [x] `02-test-system` — ОС, архитектура, hostname, IP: `test-full.txt`.
- [x] `03-stage-system` — ОС, архитектура, hostname, IP: `stage-full.txt`.
- [x] `04-prod-system` — ОС, архитектура, hostname, IP: `prod-full.txt`.
- [x] `05-07-tools` — Git, Python, venv на всех стендах: в тех же трёх файлах.
- [x] `08-test-ping` — TEST → STAGE и PROD: `test-full.txt`.
- [x] `09-stage-ping` — STAGE → TEST и PROD: `stage-full.txt`.
- [x] `10-prod-ping` — PROD → TEST и STAGE: `prod-full.txt`.
- [x] `11-test-clone` — реальный git clone, ветка, commit SHA: `test-full.txt`.
- [x] `12-test-start` — зависимости, `pip check`, служба и запуск: `test-full.txt`.
- [x] `13-health` — HTTP 200 и JSON: `test-full.txt` и `host-view.txt`.

Отличие от исходного плана: установка ОС выполнялась автоматически
(`VBoxManage unattended install`), поэтому кадров ручного установщика нет.
Вместо них — лог установки и экраны консоли. Если методичка требует именно
кадры ручной установки, их должен снять человек при повторной установке.

## Данные о стендах

```text
Дата выполнения: 2026-10-09 — 2026-10-10
Хост (ОС, архитектура, RAM): Windows 10 Pro 22H2, amd64, 8 логических ядер, 16 ГБ
Гипервизор и версия: Oracle VirtualBox 7.2.20 r175154
Образ ОС и версия: ubuntu-24.04.5-live-server-amd64.iso (SHA256 сверен)
Сетевая схема, имя сегмента: NAT + VirtualBox Host-Only, 192.168.56.0/24
TEST hostname / IP / ресурсы: studentledger-test / 192.168.56.11 / 2 vCPU, 3 ГБ, 25 ГБ
STAGE hostname / IP / ресурсы: studentledger-stage / 192.168.56.12 / 2 vCPU, 3 ГБ, 25 ГБ
PROD hostname / IP / ресурсы: studentledger-prod / 192.168.56.13 / 2 vCPU, 3 ГБ, 25 ГБ
Remote URL (без секретов): https://github.com/PervuhinRoman/SLCA.git
Branch / commit SHA: master / 816ac3eca4fcf73d2de12a65b907916a97fcaeee
Environment: Ubuntu 24.04.5 LTS, Python 3.12.3, XFCE + LightDM
Commands executed: docs/LR2_RUNBOOK.md, scripts/lr02/*
Result: 6/6 ping успешны; инструменты на 3 ВМ; clone и pip check на 3 ВМ;
        служба studentledger.service активна; /health = HTTP 200 {"status":"ok"}
Problems: первая автоматическая установка TEST упала из-за нехватки памяти
        хоста (ADR-019); проброс порта приложения через 127.0.0.1 сбрасывается
        из-за VPN-адаптера на хосте — используется прямой внутренний адрес
Screenshots: PNG консолей ВМ (01-04) + текстовые подтверждения команд
```

После получения данных агент фиксирует их здесь и в `HANDOFF.md`, проверяет
все пункты ЛР2, затем готовит отчёт. Незавершённые пункты не отмечать готовыми.

## Что осталось до отчёта

1. Решение человека: достаточно ли машинных подтверждений вместо ручных
   скриншотов установки, или требуется повторная ручная установка.
2. Проверка Human DoD по `LABS_PLAN.md` и подготовка DOCX-отчёта ЛР2.
