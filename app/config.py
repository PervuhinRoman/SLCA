"""Environment configuration; never include secret values in diagnostics."""
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class ConfigurationError(ValueError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore",
        hide_input_in_errors=True,
    )
    app_env: Literal["test", "stage", "prod"] = "test"
    database_url: SecretStr | None = None

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return value
        try:
            url = make_url(value.get_secret_value())
            if url.drivername != "postgresql+psycopg" or not url.database:
                raise ValueError
        except (ArgumentError, ValueError):
            raise ValueError("DATABASE_URL: требуется URL postgresql+psycopg с именем БД") from None
        return value

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise ConfigurationError("Задайте DATABASE_URL для подключения к PostgreSQL")
        return self.database_url.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError:
        raise ConfigurationError("Проверьте APP_ENV и DATABASE_URL в окружении или .env") from None
