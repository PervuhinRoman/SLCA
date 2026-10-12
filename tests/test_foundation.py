import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from starlette.routing import Route

from app.config import Settings, ConfigurationError, get_settings
from app.main import app


def test_health_without_database(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/health").status_code == 200
        for path in ("/docs", "/redoc", "/openapi.json", "/students", "/users"):
            assert client.get(path).status_code == 404


@pytest.mark.parametrize("url", ["secret-invalid", "sqlite:///secret", "postgresql://u:secret@localhost/db"])
def test_invalid_configuration_is_redacted(url):
    with pytest.raises(ValidationError) as error:
        Settings(database_url=url, _env_file=None)
    assert url not in str(error.value)
    assert "secret" not in str(error.value)


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_ENV=stage\nDATABASE_URL=postgresql+psycopg://u:secret@localhost/db\n")
    settings = Settings(_env_file=env)
    assert settings.app_env == "test"
    assert "secret" not in repr(settings)
    assert "secret" in settings.require_database_url()


def test_missing_database_configuration():
    with pytest.raises(ConfigurationError):
        Settings(_env_file=None).require_database_url()


@pytest.mark.parametrize("error,status", [
    (OperationalError("SQL secret", {"password": "secret"}, Exception("secret")), 503),
    (ValueError("secret"), 500),
])
def test_errors_do_not_leak(error, status, caplog):
    async def broken(request):
        raise error
    route = Route("/test-error", broken)
    app.router.routes.append(route)
    try:
        with caplog.at_level(logging.INFO, logger="studentledger"), TestClient(app) as client:
            response = client.get("/test-error?password=secret")
        assert response.status_code == status
        assert "secret" not in response.text + caplog.text
        assert "sqlstate=" in caplog.text
        assert "Обратитесь" in response.text or "обратитесь" in response.text
    finally:
        app.router.routes.remove(route)


def test_invalid_environment_safe_message(monkeypatch):
    monkeypatch.setenv("APP_ENV", "secret-invalid")
    with pytest.raises(ConfigurationError) as error:
        get_settings()
    assert "secret" not in str(error.value)
