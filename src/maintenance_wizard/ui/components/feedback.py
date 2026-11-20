"""Send feedback popover for the monthly board."""

from __future__ import annotations

from typing import Any

import streamlit as st

from maintenance_wizard.integrations.feedback_session_log import (
    enrich_feedback_with_session_debug_log,
)
from maintenance_wizard.integrations.feedback_submit import submit_feedback

_FEEDBACK_NOTE_KEY = "mw_feedback_note"
_FEEDBACK_FLASH_OK = "mw_feedback_flash_ok"
_FEEDBACK_WARN_EMPTY = "mw_feedback_warn_empty"
_FEEDBACK_ERROR_KEY = "mw_feedback_error"
_FEEDBACK_SUBMIT_KEY = "mw_feedback_submit"


def _latest_session_debug_from_state() -> tuple[dict[str, Any] | None, str | None]:
    raw = st.session_state.get("mw_session_debug_log")
    debug_log = raw if isinstance(raw, dict) else None
    url = st.session_state.get("mw_session_debug_notion_url")
    notion_url = str(url).strip() if url else None
    return debug_log, notion_url


def _submit_feedback(*, surface: str | None) -> None:
    text = st.session_state.get(_FEEDBACK_NOTE_KEY, "").strip()
    if not text:
        st.session_state[_FEEDBACK_WARN_EMPTY] = True
        return

    debug_log, notion_url = _latest_session_debug_from_state()
    text = enrich_feedback_with_session_debug_log(text, debug_log=debug_log, notion_url=notion_url)

    try:
        outcome = submit_feedback(text, surface=surface)
    except (RuntimeError, ValueError) as exc:
        st.session_state[_FEEDBACK_ERROR_KEY] = str(exc)
        return

    st.session_state[_FEEDBACK_FLASH_OK] = outcome
    st.session_state[_FEEDBACK_NOTE_KEY] = ""


def _render_feedback_form(*, surface: str | None) -> None:
    flash = st.session_state.pop(_FEEDBACK_FLASH_OK, False)
    if flash:
        st.success(f"Thanks — your note was filed ({flash}).")
        st.toast("Feedback submitted", icon="✅")
    if st.session_state.pop(_FEEDBACK_WARN_EMPTY, False):
        st.warning("Please enter a short note before submitting.")
    if err := st.session_state.pop(_FEEDBACK_ERROR_KEY, None):
        st.error(err)

    st.text_area(
        "Your note",
        key=_FEEDBACK_NOTE_KEY,
        height=100,
        max_chars=4000,
        label_visibility="collapsed",
        placeholder="Describe a bug, feature request, idea, or question...",
    )
    st.button(
        "Submit feedback",
        key=_FEEDBACK_SUBMIT_KEY,
        type="secondary",
        on_click=_submit_feedback,
        kwargs={"surface": surface},
    )


def render_feedback_controls(*, surface: str | None = None) -> None:
    with st.popover("Send feedback", type="secondary"):
        _render_feedback_form(surface=surface)
