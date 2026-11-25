# Evidence — ЛР3 (контейнеризация)

Дата выполнения: 26.11.2026. Хост: Windows, VirtualBox 7.1.10.
Стенды: Ubuntu 24.04.5 LTS, 2 vCPU, 3 ГБ RAM, диск 20 ГБ.

| Стенд | Hostname | IP | SSH | Docker |
|---|---|---|---|---|
| TEST | studentledger-test | 192.168.56.11 | 127.0.0.1:2221 | 29.10.1 |
| STAGE | studentledger-stage | 192.168.56.12 | 127.0.0.1:2222 | 29.10.1 |
| PROD | studentledger-prod | 192.168.56.13 | 127.0.0.1:2223 | 29.10.1 |

Docker Compose v5.8.0. Проект развёрнут на TEST из ветки
`feature/lr3-docker-and-app`, commit `d026728`.

## Скриншоты

| Файл | Что подтверждает |
|---|---|
| `01-login.png` | Страница входа на русском языке |
| `02-students-admin.png` | Список студентов у администратора |
| `03-student-form.png` | Форма добавления с подписями полей |
| `04-student-form-filled.png` | Заполненная форма до сохранения |
| `05-student-created.png` | Запись сохранена и видна в списке |
| `06-student-own-record.png` | Студент видит только собственную запись |
| `07-forbidden.png` | Отказ в доступе к добавлению для роли student |
| `08-after-restart.png` | Данные на месте после `docker compose down/up` |
| `09-console-compose-ps.png` | Консоль TEST: контейнеры запущены |
| `10-console-data.png` | Консоль TEST: том, статусы и строки БД после перезапуска |

## Текстовые подтверждения

| Файл | Что подтверждает |
|---|---|
| `01-test-system.txt` | ОС, ядро, IP, версии Docker и Compose на TEST |
| `02-compose-ps-before.txt` | Состояние контейнеров до перезапуска |
| `03-db-rows-before.txt` | Две записи студентов в PostgreSQL |
| `04-compose-down.txt` | Контейнеры остановлены и удалены |
| `05-volume-after-down.txt` | Том `studentledger_pgdata` сохранился |
| `06-compose-up.txt` | Повторный запуск стека |
| `07-compose-ps-after.txt` | Контейнеры снова работают |
| `08-db-rows-after.txt` | Те же две записи после перезапуска |
| `09-volume-inspect.txt` | Параметры постоянного тома |
| `10-health.txt` | `GET /health` → HTTP 200 `{"status":"ok"}` |
| `11-audit.txt` | Записи аудита `student.create` |
| `12-after-vm-reboot.txt` | После перезагрузки ВМ контейнеры и данные восстановились |
| `13-stage-system.txt`, `14-prod-system.txt` | Docker установлен на STAGE и PROD |

## Проверки, выполненные локально

- `pytest`: 44 теста пройдено на PostgreSQL 17 (локальный одноразовый кластер).
- `pip check`: `No broken requirements found`.
- Сценарии: вход, неверный пароль, блокировка, RBAC, добавление студента,
  валидация формы, аудит, отзыв refresh при выходе, ротация refresh.

## Ограничения

- Пароли стенда (`StudentLedger2026!`, `StudentLedgerDB2026`,
  `AdminPass2026!`) являются учебными и находятся только в `.env` на ВМ,
  не в Git; для реального проекта они недопустимы.
- TEST загружается медленно при одновременно запущенных трёх ВМ на хосте;
  это ограничение ресурсов хоста, а не приложения.
- Порты PostgreSQL наружу не публикуются (SEC-02).
- Отчёт ЛР3 создаётся отдельно; до его проверки статус — READY_FOR_REPORT.
