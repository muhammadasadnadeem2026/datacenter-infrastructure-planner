"""Application settings from environment variables (never hard-code secrets)."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    # Local default: SQLite file next to the backend package. Docker / production set DATABASE_URL.
    # On Vercel the code directory is read-only, so the default database lives in /tmp (a demo: it resets
    # when the function instance is recycled; set DATABASE_URL to a PostgreSQL URL to keep projects).
    database_url: str = (
        "sqlite:////tmp/hallplan.db"
        if os.environ.get("VERCEL")
        else f"sqlite:///{(Path(__file__).resolve().parents[1] / 'hallplan.db').as_posix()}"
    )
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_per_minute: int = 240
    log_level: str = "info"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
