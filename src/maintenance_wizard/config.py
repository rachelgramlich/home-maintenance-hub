from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _REPO_ROOT / "secrets.toml"),
        env_file_encoding="utf-8",
        env_prefix="MAINTENANCE_WIZARD_",
        extra="ignore",
    )

    store: Literal["local", "google_sheets"] = "local"
    sheet_id: str = ""
    timezone: str = "America/New_York"
    due_soon_days: int = Field(default=7, ge=1, le=31)
    local_data_path: Path = Field(
        default_factory=lambda: _REPO_ROOT / ".local" / "maintenance_wizard" / "data.json"
    )
    google_token_path: Path = Field(
        default_factory=lambda: _REPO_ROOT / ".local" / "maintenance_wizard" / "token.json"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
