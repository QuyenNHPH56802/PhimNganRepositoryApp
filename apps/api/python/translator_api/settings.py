"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TRANSLATOR_", extra="ignore")

    env: str = "dev"
    database_url: str = Field(
        default="postgresql+psycopg://translator:translator@localhost:5432/translator",
    )
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"

    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "translator"
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")

    storage_provider_id: str = "s3_compatible"
    local_storage_root: str = "./.local-storage"

    auth_stub_enabled: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
