"""Environment-only configuration (12-factor). Secrets never live in code or the repo."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""  # pooled (app + ingestion)
    database_url_direct: str = ""  # direct (alembic migrations only)
    gemini_api_key: str = ""
    # Pinned; override deliberately, never "latest". 2.5-flash is closed to new accounts
    # (404 "no longer available to new users"); 3.1-flash-lite is the stable non-preview.
    gemini_model: str = "gemini-3.1-flash-lite"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"  # pinned fallback


@lru_cache
def get_settings() -> Settings:
    return Settings()
