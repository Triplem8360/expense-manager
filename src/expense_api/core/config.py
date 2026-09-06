from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(min_length=1, validation_alias="DATABASE_URL")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")

    @field_validator("database_url")
    @classmethod
    def require_async_postgresql_url(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg scheme")
        return value


class Settings(DatabaseSettings):
    app_name: str = Field(
        default="Expense Manager API",
        validation_alias="APP_NAME",
    )
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")

    jwt_secret_key: SecretStr = Field(
        min_length=32,
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: Literal["HS256"] = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    jwt_issuer: str = Field(
        default="expense-manager",
        min_length=1,
        validation_alias="JWT_ISSUER",
    )
    jwt_audience: str = Field(
        default="expense-manager-api",
        min_length=1,
        validation_alias="JWT_AUDIENCE",
    )
    access_token_ttl_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        validation_alias="ACCESS_TOKEN_TTL_MINUTES",
    )
    refresh_token_ttl_days: int = Field(
        default=7,
        ge=1,
        le=30,
        validation_alias="REFRESH_TOKEN_TTL_DAYS",
    )
    jwt_clock_skew_seconds: int = Field(
        default=30,
        ge=0,
        le=300,
        validation_alias="JWT_CLOCK_SKEW_SECONDS",
    )
    cookie_secure: bool = Field(
        default=True,
        validation_alias="COOKIE_SECURE",
    )
    cookie_samesite: Literal["lax", "strict"] = Field(
        default="lax",
        validation_alias="COOKIE_SAMESITE",
    )
    access_token_cookie_name: str = "__Host-expense_access"
    refresh_token_cookie_name: str = "__Host-expense_refresh"
    csrf_token_cookie_name: str = "__Host-expense_csrf"
    csrf_token_header_name: str = "X-CSRF-Token"
    
    @field_validator("cookie_secure")
    @classmethod
    def require_secure_cookies(cls, value: bool) -> bool:
        if not value:
            raise ValueError("COOKIE_SECURE must be true for __Host- cookies")
        return value


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings.model_validate({})


@lru_cache
def get_settings() -> Settings:
    return Settings.model_validate({})
