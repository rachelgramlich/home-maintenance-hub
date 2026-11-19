"""Shared pytest fixtures for local store + settings cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from maintenance_wizard.config import get_settings
from maintenance_wizard.scripts.seed_local_data import SAMPLE


@pytest.fixture(autouse=True)
def _local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every test at an isolated local JSON store with sample templates."""
    data_path = tmp_path / "maintenance_wizard" / "data.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(SAMPLE, indent=2), encoding="utf-8")
    monkeypatch.setenv("MAINTENANCE_WIZARD_STORE", "local")
    monkeypatch.setenv("MAINTENANCE_WIZARD_LOCAL_DATA_PATH", str(data_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
