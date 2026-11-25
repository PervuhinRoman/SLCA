#!/bin/sh
# Wait for PostgreSQL, apply Alembic migrations, then start the application.
set -eu

if [ -z "${JWT_SECRET:-}" ]; then
    echo "Ошибка: не задан JWT_SECRET (не менее 32 символов)." >&2
    exit 1
fi

attempt=1
until alembic upgrade head; do
    if [ "$attempt" -ge 30 ]; then
        echo "Не удалось применить миграции: PostgreSQL недоступен." >&2
        exit 1
    fi
    echo "Ожидание PostgreSQL (попытка ${attempt} из 30)..."
    attempt=$((attempt + 1))
    sleep 2
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
