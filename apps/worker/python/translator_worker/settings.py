"""Worker settings (mirror of API settings for symmetry)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TRANSLATOR_", extra="ignore")

    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings