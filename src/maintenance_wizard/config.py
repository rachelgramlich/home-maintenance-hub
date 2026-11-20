from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _notion_ds_id(env_name: str) -> str:
    raw = os.environ.get(env_name, "")
    return raw.replace("collection://", "").strip()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _REPO_ROOT / ".streamlit" / "secrets.toml"),
        env_file_encoding="utf-8",
        env_prefix="MAINTENANCE_WIZARD_",
        extra="ignore",
    )

    store: Literal["local", "notion"] = "local"
    timezone: str = "America/New_York"
    local_data_path: Path = Field(
        default_factory=lambda: _REPO_ROOT / ".local" / "maintenance_wizard" / "data.json"
    )
    notion_api_key: str = Field(default_factory=lambda: os.environ.get("NOTION_API_KEY", ""))
    notion_tasks_ds_id: str = Field(
        default_factory=lambda: _notion_ds_id("MAINTENANCE_WIZARD_NOTION_TASKS_DS_ID")
    )
    notion_contractors_ds_id: str = Field(
        default_factory=lambda: _notion_ds_id("MAINTENANCE_WIZARD_NOTION_CONTRACTORS_DS_ID")
    )
    notion_completions_ds_id: str = Field(
        default_factory=lambda: _notion_ds_id("MAINTENANCE_WIZARD_NOTION_COMPLETIONS_DS_ID")
    )
    xlsx_path: Path | None = None
    github_feedback_token: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_FEEDBACK_TOKEN", "")
    )
    github_feedback_repository: str = Field(
        default_factory=lambda: os.environ.get(
            "GITHUB_FEEDBACK_REPOSITORY",
            "rachelgramlich/maintenance-wizard",
        )
    )
    require_auth: bool = False
    auth_email_allowlist: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
