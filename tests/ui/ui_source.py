"""Concatenated Streamlit UI sources for regression string checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.repo_paths import UI_SRC_ROOT

if TYPE_CHECKING:
    from streamlit.testing.v1 import AppTest

UI_ROOT = UI_SRC_ROOT
APP_PATH = UI_ROOT / "app.py"

_UI_MODULE_PATHS = (
    "app.py",
    "styles.py",
    "theme.py",
)


def ui_source() -> str:
    chunks = [(UI_ROOT / rel).read_text(encoding="utf-8") for rel in _UI_MODULE_PATHS]
    return "\n\n".join(chunks)


def apptest_start_app(*, timeout: int = 60) -> AppTest:
    """Load ``app.py`` headless, run it once, and fail on any exception."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP_PATH), default_timeout=timeout)
    at.run(timeout=timeout)
    apptest_assert_no_exception(at, context="first run")
    return at


def apptest_assert_no_exception(at: AppTest, *, context: str = "AppTest run") -> None:
    assert not at.exception, f"{context}: {[str(e.value) for e in at.exception]}"
