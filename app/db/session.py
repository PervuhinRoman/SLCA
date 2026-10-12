"""One explicit transaction per operation; schema is managed only by Alembic."""
from contextlib import contextmanager
from functools import lru_cache
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import get_settings


def build_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, hide_parameters=True,
                         connect_args={"connect_timeout": 5}, echo=False)


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings().require_database_url())


@contextmanager
def transaction(engine: Engine | None = None) -> Iterator[Session]:
    with Session(engine if engine is not None else get_engine()) as session:
        with session.begin():
            yield session
