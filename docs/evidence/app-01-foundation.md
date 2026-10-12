# APP-01 — локальная проверка 2026-10-12

## Область

Ветка `feature/app-01-foundation`, база `origin/dev` на
`db1ef17` (PR #2 слит). Изменения приложения, без стендов и CI/CD.
ЛР2 сохраняет прототип `816ac3eca4fcf73d2de12a65b907916a97fcaeee`.

Среда: macOS arm64, Python 3.12.10, Docker Engine 29.5.2,
изолированный PostgreSQL **16.14** (`postgres:16-alpine`). Контейнер
`studentledger-app01-check`, порт опубликован только на 127.0.0.1;
случайный пароль в локальном файле с правами 600, в Git не включён.
Созданы отдельные базы основной проверки, интеграционных тестов и restore.
Проверка не использовала данные пользователей или общие базы.

## Результаты

```text
alembic upgrade head: exit 0, revision 0001
python -m app.db.check: Подключение к PostgreSQL успешно.
alembic check: No new upgrade operations detected.
python -m pytest -q: 28 passed, 1 warning in 1.10s (нет skipped)
python -m pip check: No broken requirements found.
```

Предупреждение: Starlette сообщает о deprecated поддержке httpx в TestClient
и рекомендует httpx2. Текущий закреплённый httpx 0.28.1 работает; предупреждение
не скрывается. Замена тестового транспорта не входит в APP-01.

Тесты проверяют реальные PostgreSQL PK/FK/UNIQUE/CHECK, User–Student 1:1,
запрет удаления связанного User, невозможность частичного сохранения
Student/User/AuditLog при ошибке, последующую успешную транзакцию,
параметризацию SQL, хранение digest/отзыва refresh, ограничения полей,
upgrade → downgrade → upgrade на пустой одноразовой БД и соответствие моделей.
Также проверены env/.env, отсутствие секретов в repr/ошибках/HTTP-ответах,
обработка ошибок 500/503, неизменный `/health`, отсутствие публичных CRUD/docs.

## Реальный backup/restore и smoke

До первоначального изменения пустой схемы выполнен `pg_dump -Fc`.
После миграции записаны синтетические User, Student, AuditLog, RefreshSession.
Повторный `pg_dump -Fc` восстановлен через
`pg_restore --no-owner --no-privileges --exit-on-error` в отдельную пустую БД.
Сравнены **все поля всех строк** четырёх таблиц и `alembic_version`:
UUID, FK, timestamps, digest и значения совпали.

```text
Backup/restore: all 4 tables, UUIDs, fields, timestamps and revision match
After PostgreSQL restart: original and restored data match
Real Uvicorn HTTP /health: 200 {"status":"ok"}
DB unavailable: check exits 1, sanitized diagnostic, /health remains 200
```

При первой проверке restart Docker сменил автоматически выделенный порт;
скрипт получил Connection refused на старом порту. После повторного получения
порта данные исходной БД совпали с восстановленной; это уточнение тестового
окружения, а не исправление/восстановление данных приложения.

Uvicorn запущен отдельно на loopback, проверен реальным HTTP-запросом.
При остановленном контейнере CLI подключения завершилась с кодом 1,
журнал содержал OperationalError без DSN/пароля; HTTP liveness остался 200.
Проверочный HTTP-процесс остановлен. Backup содержит только синтетические
данные и находится вне Git. Изолированный контейнер после проверок удалён.

## Границы подтверждения

Это локальный Agent work. CI, UI, JWT, права пользователей и реальные
TEST/STAGE/PROD не проверялись и не объявляются готовыми. DATA-04 и AC
требуют дальнейшего продуктового сценария/тома/стендов. Отчёт ЛР не создаётся.
Скриншоты UI не нужны: UI в APP-01 отсутствует. Для ЛР2 остаётся прежний
список `docs/evidence/lr02/README.md`.

Перед публикацией проверяются diff, состав файлов, исключение `.env`/окружения
и backup. SHA и URL PR фиксируются в передаче после успешного ответа GitHub.


## Публикация

Коммит реализации `c9c5aa6` отправлен в `origin/feature/app-01-foundation`.
[PR #3](https://github.com/PervuhinRoman/SLCA/pull/3): base `dev`, head
`feature/app-01-foundation`, состояние OPEN. Remote SHA проверен, upstream
настроен. Commit/push финальной записи передачи выполняется в ту же ветку;
финальный SHA сообщается в ответе. CI и merge отсутствуют.
