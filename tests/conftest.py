"""Shared pytest fixtures for local store + settings cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.scripts.seed_local_data import SAMPLE


@pytest.fixture(autouse=True)
def _local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every test at an isolated local JSON store with sample templates."""
    data_path = tmp_path / "home_maintenance_hub" / "data.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(SAMPLE, indent=2), encoding="utf-8")
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_STORE", "local")
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_LOCAL_DATA_PATH", str(data_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
