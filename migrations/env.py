from alembic import context
from alembic.util import CommandError
from sqlalchemy.exc import SQLAlchemyError

from app.config import ConfigurationError, get_settings
from app.db.models import Base
from app.db.session import build_engine
from app.logging import log_failure


def run_migrations():
    url = get_settings().require_database_url()
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = build_engine(url)
        try:
            with engine.connect() as connection:
                context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
                with context.begin_transaction():
                    context.run_migrations()
        finally:
            engine.dispose()


try:
    run_migrations()
except (SQLAlchemyError, ConfigurationError) as error:
    log_failure("migration_failed", error)
    raise CommandError("Миграция не выполнена. Проверьте настройки и состояние БД.") from None
