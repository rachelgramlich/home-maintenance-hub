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
    assert "mw-hero" in markdown_blob, "Main hero must show app name and month"
    assert (
        "B &amp; R Home Maintenance" in markdown_blob or "B & R Home Maintenance" in markdown_blob
    )
    assert "mw-board-month" in markdown_blob, "Month subheader must render in main hero"
    assert "mw-card-meta-badges" in markdown_blob, (
        "Open task cards must render priority/overdue after Details row"
    )

    refresh_buttons = [b for b in at.button if b.label == "Refresh"]
    assert refresh_buttons, "Sidebar Refresh button missing"

    done_buttons = [b for b in at.button if b.label == "Done"]
    assert done_buttons, "Expected at least one open task with a Done button"

    assert "mw-task-title" in markdown_blob, "Task cards must expose mw-task-title"
    assert "mw-meta-row" not in markdown_blob, "Board cards must not render subheader meta row"
    assert "Period 20" not in markdown_blob, (
        "Period detail belongs in the drawer, not on card faces"
    )
    assert "HVAC filter" in markdown_blob or "Electrical" in markdown_blob, (
        "Expected seeded task name text on open cards"
    )
    assert "Data source:" not in markdown_blob, "Store mode label must not appear on the board"

    details_buttons = [b for b in at.button if b.label == "Details"]
    assert details_buttons, "Expected Details button on an open task card"
    details_buttons[0].click().run(timeout=120)
    apptest_assert_no_exception(at, context="details drawer open")

    drawer_blob = " ".join(m.value or "" for m in at.markdown)
    assert "mw-drawer-fields" in drawer_blob, "Drawer must render task context field grid"
    assert "Task details" in drawer_blob
    assert "Area" in drawer_blob, "Drawer should label area when Details is opened"
    assert "HVAC" in drawer_blob, "Drawer should show task area value"

    app_src = (APP_PATH.parent / "app.py").read_text(encoding="utf-8")
    feedback_src = (APP_PATH.parent / "components" / "feedback.py").read_text(encoding="utf-8")
    assert "render_feedback_controls" in app_src
    assert "Send feedback" in feedback_src

    settings_btn = [b for b in at.button if "Settings" in (b.label or "")]
    assert settings_btn, "Settings nav button should be enabled"
    settings_btn[0].click().run(timeout=120)
    apptest_assert_no_exception(at, context="settings page")
    settings_blob = " ".join(m.value or "" for m in at.markdown) + " ".join(
        i.label or "" for i in at.text_input
    )
    assert "Timezone" in settings_blob
    assert "Store mode" in settings_blob
