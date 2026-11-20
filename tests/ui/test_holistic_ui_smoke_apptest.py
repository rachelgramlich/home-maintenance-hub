"""Holistic headless smoke: app load and primary shell (CI-safe, local JSON store)."""

from __future__ import annotations

import importlib.util

import pytest

from tests.ui.ui_source import (
    APP_PATH,
    apptest_assert_no_exception,
    apptest_start_app,
)

pytestmark = pytest.mark.holistic_ui_smoke


def test_app_py_imports_without_module_level_error() -> None:
    """Streamlit Cloud loads ``app.py`` as the main module — no ImportError at import time."""
    spec = importlib.util.spec_from_file_location("mw_app_smoke_import", APP_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_holistic_first_run_renders_board_shell() -> None:
    """Cold open: hero, metrics, Refresh, and at least one open task card."""
    at = apptest_start_app(timeout=120)
    apptest_assert_no_exception(at, context="board shell")

    markdown_blob = " ".join(m.value or "" for m in at.markdown)
    assert (
        "B &amp; R Home Maintenance" in markdown_blob
        or "B & R Home Maintenance" in markdown_blob
        or "mw-board-month" in markdown_blob
        or "mw-sidebar-brand" in markdown_blob
    )

    refresh_buttons = [b for b in at.button if b.label == "Refresh"]
    assert refresh_buttons, "Sidebar Refresh button missing"

    done_buttons = [b for b in at.button if b.label == "Done"]
    assert done_buttons, "Expected at least one open task with a Done button"

    assert "mw-task-title" in markdown_blob, "Task cards must expose mw-task-title"
    assert "HVAC filter" in markdown_blob or "Electrical" in markdown_blob, (
        "Expected seeded task name text on open cards"
    )

    app_src = (APP_PATH.parent / "app.py").read_text(encoding="utf-8")
    feedback_src = (APP_PATH.parent / "components" / "feedback.py").read_text(encoding="utf-8")
    assert "render_feedback_controls" in app_src
    assert "Send feedback" in feedback_src
