"""Maintenance Wizard — monthly checklist."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from maintenance_wizard.config import get_settings
from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.models import Urgency
from maintenance_wizard.store.factory import get_store
from maintenance_wizard.ui.styles import inject_app_styles


def today_in_tz() -> date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


def urgency_class(urgency: Urgency) -> str:
    return {
        Urgency.OVERDUE: "mw-task mw-overdue",
        Urgency.DUE_SOON: "mw-task mw-soon",
        Urgency.NORMAL: "mw-task",
        Urgency.DONE: "mw-task mw-done",
        Urgency.WONT_DO: "mw-task mw-wont",
    }[urgency]


def urgency_badge(urgency: Urgency) -> str:
    if urgency == Urgency.OVERDUE:
        return '<span class="mw-badge mw-badge-overdue">Overdue</span>'
    if urgency == Urgency.DUE_SOON:
        return '<span class="mw-badge mw-badge-soon">Due soon</span>'
    return ""


@st.cache_data(ttl=30)
def load_board(year: int, month: int, show_closed: bool) -> list:
    settings = get_settings()
    store = get_store()
    templates = store.list_templates()
    completions = store.list_completions()
    today = today_in_tz()
    board = build_month_board(templates, completions, year, month, today, settings.due_soon_days)
    if not show_closed:
        board = [r for r in board if r.urgency not in (Urgency.DONE, Urgency.WONT_DO)]
    return board


def _render_hero(month_label: str, store_label: str) -> None:
    st.markdown(
        f'<div class="mw-hero">'
        f"<h1>B &amp; R Home Maintenance</h1>"
        f'<p class="mw-hero-month">{month_label}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Data source: {store_label}")


def main() -> None:
    st.set_page_config(
        page_title="B & R Home Maintenance",
        page_icon="🏠",
        layout="centered",
    )
    inject_app_styles()

    settings = get_settings()
    today = today_in_tz()

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
        areas = sorted({t.area for t in get_store().list_templates()})
        area_filter = st.multiselect("Area", options=areas)
        if st.button("Refresh", use_container_width=True):
            load_board.clear()
            st.rerun()

    month_label = date(year, month, 1).strftime("%B %Y")
    _render_hero(month_label, settings.store)

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
    open_n = len(board) - overdue_n - soon_n

    m1, m2, m3 = st.columns(3)
    m1.metric("Overdue", overdue_n)
    m2.metric("Due soon", soon_n)
    m3.metric("Open", max(open_n, 0))

    if not board:
        st.success("Nothing open for this month — or all tasks are complete.")
        return

    store = get_store()

    for row in board:
        t = row.template
        badge = urgency_badge(row.urgency)
        last_html = ""
        if row.last_done_on:
            last_html = f'<p class="mw-last">Last done {row.last_done_on.isoformat()}'
            if row.last_done_notes:
                last_html += f" — {row.last_done_notes}"
            last_html += "</p>"

        card_html = (
            f"{badge}"
            f'<p class="mw-task-title">{t.name}</p>'
            f'<p class="mw-meta">{t.area} · {t.cadence} · {row.period}</p>'
            f"{last_html}"
        )

        if row.urgency in (Urgency.DONE, Urgency.WONT_DO):
            st.markdown(
                f'<div class="mw-task-card {urgency_class(row.urgency)}">{card_html}</div>',
                unsafe_allow_html=True,
            )
            continue

        with st.container(border=True):
            st.markdown(
                '<span class="mw-task-shell" aria-hidden="true"></span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="{urgency_class(row.urgency)} mw-task--open">{card_html}</div>',
                unsafe_allow_html=True,
            )
            notes_key = f"notes_{t.task_id}_{row.period}"
            notes = st.text_input(
                "Notes",
                key=notes_key,
                placeholder="Optional notes",
                label_visibility="collapsed",
            )
            done_col, skip_col = st.columns(2)
            with done_col:
                if st.button(
                    "Done",
                    key=f"done_{t.task_id}_{row.period}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        store.add_completion(t.task_id, row.period, "done", today, notes or "")
                        load_board.clear()
                        st.rerun()
                    except ValueError as err:
                        st.warning(str(err))
            with skip_col:
                if st.button(
                    "Won't do",
                    key=f"wont_{t.task_id}_{row.period}",
                    type="secondary",
                    use_container_width=True,
                ):
                    try:
                        store.add_completion(t.task_id, row.period, "wont_do", today, notes or "")
                        load_board.clear()
                        st.rerun()
                    except ValueError as err:
                        st.warning(str(err))


if __name__ == "__main__":
    main()
