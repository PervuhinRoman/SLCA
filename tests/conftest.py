import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.config import get_settings
from app.db.session import build_engine, get_engine


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    get_settings.cache_clear()
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def database(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")
    # Guard against accidentally truncating a shared application database.
    assert make_url(url).database.endswith("_test"), "Test database name must end in _test"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    engine = build_engine(url)
    from sqlalchemy import text
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE refresh_sessions, audit_logs, students, users"))
    yield engine
    engine.dispose()
