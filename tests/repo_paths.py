"""Repo and test tree paths — single owner for pytest path literals."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UI_SRC_ROOT = REPO_ROOT / "src" / "maintenance_wizard" / "ui"
