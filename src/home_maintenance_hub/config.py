from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _REPO_ROOT / ".streamlit" / "secrets.toml"),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    store: Literal["local", "notion"] = "local"
    timezone: str = "America/New_York"
    local_data_path: Path = Field(
        default_factory=lambda: _REPO_ROOT / ".local" / "home_maintenance_hub" / "data.json",
        validation_alias="LOCAL_DATA_PATH",
    )
    notion_api_key: str = Field(default="", validation_alias="NOTION_API_KEY")
    notion_tasks_ds_id: str = Field(default="", validation_alias="TASKS_DS_ID")
    notion_contractors_ds_id: str = Field(default="", validation_alias="CONTRACTORS_DS_ID")
    notion_completions_ds_id: str = Field(default="", validation_alias="COMPLETIONS_DS_ID")
    xlsx_path: Path | None = Field(default=None, validation_alias="XLSX_PATH")
    github_feedback_token: str = Field(default="", validation_alias="GITHUB_FEEDBACK_TOKEN")
    github_feedback_repository: str = Field(
        default="rachelgramlich/home-maintenance-hub",
        validation_alias="GITHUB_FEEDBACK_REPOSITORY",
    )
    require_auth: bool = False
    auth_email_allowlist: str = ""

    @field_validator(
        "notion_tasks_ds_id",
        "notion_contractors_ds_id",
        "notion_completions_ds_id",
        mode="before",
    )
    @classmethod
    def _strip_notion_collection_prefix(cls, value: object) -> object:
        if isinstance(value, str):
            return value.replace("collection://", "").strip()
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
