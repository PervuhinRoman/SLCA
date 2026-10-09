# REQUIREMENTS_MAP — StudentLedger

Файл связывает требования ТЗ с будущей реализацией и тестами.

> `TBD` означает отсутствие реализации. Прототип ЛР2 не закрывает
> функциональные требования или финальную приёмку.

## Подготовка инфраструктуры ЛР2

| ID | Реализация / подготовка | Проверка и ограничение |
|---|---|---|
| SYS-01, SW-01 | `app/main.py`, `requirements.txt`, `README.md` | HTTP-прототип; локальный smoke в `docs/evidence/lr02/agent-local-check.txt`; полного запуска продукта с БД пока нет |
| SW-03, AC-01 | Исходники и документы опубликованы в `PervuhinRoman/SLCA`, ветка `master`, начальный коммит `603852f` | Push успешен; доступ команды и clone на TEST ещё не подтверждены |
| HW-01 | Ubuntu и схема трёх ВМ в `docs/LR2_RUNBOOK.md` | Фактическое создание ВМ ожидается |
| SEC-03, SW-04 | `.gitignore` исключает `.env`, ключи | Только подготовка; управление секретами приложения ещё не реализовано |
| G-05, AC-02 | `/health` проверяет HTTP-процесс | Проверка подключения к PostgreSQL отсутствует; требования не закрыты |

## Functional requirements

| ID | Кратко | Implementation | Tests |
|---|---|---|---|
| FR-01 | Просмотр списка студентов | TBD | TBD |
| FR-02 | Добавление студента | TBD | TBD |
| FR-03 | Изменение студента | TBD | TBD |
| FR-04 | Подсчёт студентов по форме обучения | TBD | TBD |
| FR-05 | Просмотр учебного плана | TBD | TBD |
| FR-06 | Добавление/изменение учебного плана | TBD | TBD |
| FR-07 | Часы и форма отчётности дисциплины | TBD | TBD |
| FR-08 | Просмотр журнала успеваемости | TBD | TBD |
| FR-09 | Добавление оценки | TBD | TBD |
| FR-10 | Изменение оценки | TBD | TBD |
| FR-11 | Вход по логину/паролю + JWT | TBD | TBD |
| FR-12 | Refresh/logout | TBD | TBD |
| FR-13 | RBAC | TBD | TBD |
| FR-14 | Управление пользователями | TBD | TBD |

## Security requirements

| ID | Кратко | Implementation | Tests |
|---|---|---|---|
| SEC-01 | Обязательная аутентификация | TBD | TBD |
| SEC-02 | БД не публикуется наружу | TBD | TBD |
| SEC-03 | Секреты вне репозитория | TBD | TBD |
| SEC-04 | Валидация + ORM/parameterized queries | TBD | TBD |
| SEC-05 | Безопасное журналирование ошибок | TBD | TBD |
| SEC-06 | Backup перед изменением схемы | TBD | TBD |
| SEC-07 | JWT access/refresh | TBD | TBD |
| SEC-08 | Hash passwords | TBD | TBD |
| SEC-09 | RBAC enforcement | TBD | TBD |
| SEC-10 | Audit log | TBD | TBD |

## Data requirements

| ID | Кратко | Implementation | Tests |
|---|---|---|---|
| DATA-01 | PK/FK | TBD | TBD |
| DATA-02 | Grade только для существующих Student/Discipline | TBD | TBD |
| DATA-03 | Ссылочная целостность | TBD | TBD |
| DATA-04 | Persistence после рестарта | TBD | TBD |

## Acceptance

К моменту финальной приёмки должны быть выполнены `AC-01`—`AC-09`.
