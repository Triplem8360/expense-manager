from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(
        default="Expense Manager API",
        validation_alias="APP_NAME",
    )
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")


@lru_cache
def get_settings() -> Settings:
    return Settings()
