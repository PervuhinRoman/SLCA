# DECISIONS — StudentLedger

Здесь фиксируются решения, которые нельзя заставлять следующего агента угадывать.

## ADR-001 — Backend: FastAPI
**Status:** accepted  
**Decision:** серверная часть реализуется на FastAPI.  
**Source:** актуальное ТЗ ЛР1.

## ADR-002 — Database: PostgreSQL 16+
**Status:** accepted  
**Decision:** используется PostgreSQL версии 16 или выше; минимальная версия — 16.  
**Reason:** версия находится в официальном цикле поддержки и получает исправления ошибок и безопасности.  
**Source:** актуальное ТЗ ЛР1.

## ADR-003 — ORM and migrations
**Status:** accepted  
**Decision:** SQLAlchemy используется как ORM, Alembic — для миграций схемы.  
**Source:** актуальное ТЗ ЛР1.

## ADR-004 — Authentication
**Status:** accepted  
**Decision:** логин + пароль, JWT access/refresh.  
**Passwords:** Argon2id или bcrypt.  
**Source:** актуальное ТЗ ЛР1.

## ADR-005 — Authorization
**Status:** accepted  
**Decision:** RBAC с ролями:
- `student`
- `teacher`
- `administrator`

**Source:** актуальное ТЗ ЛР1.

## ADR-006 — Runtime environments
**Status:** accepted  
**Decision:** три окружения:
- TEST
- STAGE
- PROD

**Source:** актуальное ТЗ ЛР1 и методика ЛР2.

## ADR-007 — Containerization
**Status:** accepted  
**Decision:** Docker + Docker Compose.  
**Source:** актуальное ТЗ ЛР1; потребуется в ЛР3.

## ADR-008 — CI/CD engine
**Status:** accepted  
**Decision:** TeamCity.  
**Source:** методические материалы ЛР4–ЛР8.

## ADR-009 — Branch strategy
**Status:** OPEN / needs reconciliation before LR4

В текущем ТЗ:
- `main` → prod
- `release/*` → stage
- `develop` → test

В методике последующих ЛР используются:
- feature/fix
- dev
- prod

Перед ЛР4 необходимо выбрать один вариант, привести ТЗ/реализацию к единой схеме и зафиксировать окончательное решение здесь.

**Сверка 2026-10-09:** расхождение подтверждено по SW-09 и методичке.
Минимальное предложение: согласовать сохранение SW-09 с отображением
терминов методички на `develop` / `release/*` / `main`. Если преподаватель
требует буквальные имена `dev` / `prod`, отдельно изменить SW-09 после
решения человека. Сейчас ни один вариант не принят; ЛР2 этим не блокируется.

## ADR-010 — Граница прототипа ЛР2
**Status:** accepted  
**Date:** 2026-10-09  
**Decision:** по LABS_PLAN реализуется только FastAPI `GET /health`,
возвращающий HTTP 200 и `{"status":"ok"}`. Роут проверяет жизнь процесса;
продуктовых данных не раскрывает, защищённых функций пока нет.
OpenAPI/Swagger/ReDoc отключены как ненужные для этого этапа.
БД, JWT, роли и бизнес-функции остаются требованиями последующих этапов.
**Trace:** SYS-01, SW-01 частично; G-05 и AC-02 не закрыты.

## ADR-011 — Базовая ОС для инструкции ЛР2
**Status:** accepted for runbook; deployment not verified  
**Date:** 2026-10-09  
**Decision:** Ubuntu Server 24.04 LTS / Python 3.12 на трёх ВМ;
архитектура образа соответствует хосту. Одинаковая ОС упрощает воспроизводимость.
Git/Python/venv устанавливаются на всех стендах согласно пункту 5 методички.
**Network proposal:** NAT для внешнего доступа плюс общий внутренний сегмент;
hostname и пример адресов приведены в LR2_RUNBOOK, фактические IP неизвестны.
**Pending:** гипервизор, ресурсы хоста и remote URL уточняются у человека.

## ADR-012 — Одна рабочая ветка master на текущем этапе
**Status:** accepted by user  
**Date:** 2026-10-09  
**Decision:** текущая совместная работа и первая публикация ведутся в `master`;
дополнительные ветки сейчас не создаются. Remote, указанный пользователем:
`https://github.com/PervuhinRoman/SLCA.git`.
**Scope:** организация текущей работы. Назначение веток окружениям из SW-09
ещё не пересмотрено; `master` не назначается автоматически PROD.
ADR-009 остаётся открытым до ЛР4; требуемые методичкой ветки и PR будут
согласованы перед соответствующим этапом. Исходное ТЗ не редактировалось.
