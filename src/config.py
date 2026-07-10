"""Environment-only configuration (12-factor). Secrets never live in code or the repo."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""  # pooled (app + ingestion)
    database_url_direct: str = ""  # direct (alembic migrations only)
    gemini_api_key: str = ""
    groq_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
