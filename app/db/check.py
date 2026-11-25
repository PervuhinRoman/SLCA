"""Private operational check: python -m app.db.check; no public data endpoint."""
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import ConfigurationError
from app.db.session import get_engine
from app.logging import log_failure


def main() -> int:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, ConfigurationError) as error:
        log_failure("database_check_failed", error)
        print("Не удалось подключиться к БД. Проверьте настройки и доступность PostgreSQL.")
        return 1
    print("Подключение к PostgreSQL успешно.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
