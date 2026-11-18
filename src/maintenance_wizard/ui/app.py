"""Maintenance Wizard — monthly checklist."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

import streamlit as st

from maintenance_wizard.config import get_settings
from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.models import Urgency
from maintenance_wizard.store.factory import get_store
from maintenance_wizard.ui.styles import BADGE_CSS

st.set_page_config(page_title="Maintenance Wizard", page_icon="🏠", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)


def today_in_tz() -> date:
    tz = ZoneInfo(get_settings().timezone)
    from datetime import datetime

    return datetime.now(tz).date()


def urgency_badge(urgency: Urgency) -> str:
    if urgency == Urgency.OVERDUE:
        return '<span class="mw-badge mw-badge-overdue">Overdue</span>'
    if urgency == Urgency.DUE_SOON:
        return '<span class="mw-badge mw-badge-soon">Due soon</span>'
    return ""


def card_class(urgency: Urgency) -> str:
    return {
        Urgency.OVERDUE: "mw-card mw-overdue",
        Urgency.DUE_SOON: "mw-card mw-soon",
        Urgency.NORMAL: "mw-card mw-normal",
        Urgency.DONE: "mw-card mw-done",
        Urgency.WONT_DO: "mw-card mw-wont",
    }[urgency]


@st.cache_data(ttl=30)
def load_board(year: int, month: int, show_closed: bool) -> list:
    settings = get_settings()
    store = get_store()
    templates = store.list_templates()
    completions = store.list_completions()
    today = today_in_tz()
    board = build_month_board(
        templates, completions, year, month, today, settings.due_soon_days
    )
    if not show_closed:
        board = [r for r in board if r.urgency not in (Urgency.DONE, Urgency.WONT_DO)]
    return board


def main() -> None:
    settings = get_settings()
    today = today_in_tz()

    st.title("Maintenance Wizard")
    st.caption("This month's home maintenance · data: " + settings.store)

    with st.sidebar:
        st.header("Month")
        year = st.number_input("Year", min_value=2020, max_value=2035, value=today.year)
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            format_func=lambda m: date(year, m, 1).strftime("%B"),
            index=today.month - 1,
        )
        show_closed = st.toggle("Show done & won't do", value=False)
        area_filter = st.multiselect(
            "Area",
            options=sorted(
                {
                    t.area
                    for t in get_store().list_templates()
                }
            ),
        )
        if st.button("Refresh"):
            load_board.clear()
            st.rerun()

    try:
        board = load_board(year, month, show_closed)
    except Exception as exc:
        st.error(f"Could not load tasks: {exc}")
        st.info("Local mode: run `just init-local-data` then `just ui`.")
        return

    if area_filter:
        board = [r for r in board if r.template.area in area_filter]

    overdue_n = sum(1 for r in board if r.urgency == Urgency.OVERDUE)
    soon_n = sum(1 for r in board if r.urgency == Urgency.DUE_SOON)
    col1, col2, col3 = st.columns(3)
    col1.metric("Overdue", overdue_n)
    col2.metric("Due soon", soon_n)
    col3.metric("Open", len(board) - overdue_n - soon_n)

    if not board:
        st.success("Nothing open for this month — or all tasks are complete.")
        return

    store = get_store()
    for row in board:
        t = row.template
        badge = urgency_badge(row.urgency)
        last = ""
        if row.last_done_on:
            last = f"Last done {row.last_done_on.isoformat()}"
            if row.last_done_notes:
                last += f" — {row.last_done_notes}"

        st.markdown(
            f'<div class="{card_class(row.urgency)}">'
            f"{badge}<strong>{t.name}</strong>"
            f'<div class="mw-meta">{t.area} · {t.cadence} · period {row.period}</div>'
            f'<div class="mw-meta">{last}</div></div>',
            unsafe_allow_html=True,
        )

        if row.urgency in (Urgency.DONE, Urgency.WONT_DO):
            continue

        c1, c2, c3 = st.columns([1, 1, 3])
        notes_key = f"notes_{t.task_id}_{row.period}"
        with c3:
            notes = st.text_input("Notes (optional)", key=notes_key, label_visibility="collapsed")
        with c1:
            if st.button("Done", key=f"done_{t.task_id}_{row.period}", type="primary"):
                try:
                    store.add_completion(
                        t.task_id, row.period, "done", today, notes or ""
                    )
                    load_board.clear()
                    st.rerun()
                except ValueError as err:
                    st.warning(str(err))
        with c2:
            if st.button("Won't do", key=f"wont_{t.task_id}_{row.period}"):
                try:
                    store.add_completion(
                        t.task_id, row.period, "wont_do", today, notes or ""
                    )
                    load_board.clear()
                    st.rerun()
                except ValueError as err:
                    st.warning(str(err))

        st.divider()


if __name__ == "__main__":
    main()