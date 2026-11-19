"""Maintenance Wizard — monthly checklist (mockup C)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from maintenance_wizard.config import get_settings
from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.models import BoardTask, Urgency
from maintenance_wizard.store.factory import get_store
from maintenance_wizard.ui.styles import inject_app_styles
from maintenance_wizard.ui.views.contractors import render_contractors_admin
from maintenance_wizard.ui.views.drawer import render_drawer


def today_in_tz() -> date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


def urgency_class(urgency: Urgency) -> str:
    return {
        Urgency.OVERDUE: "mw-task mw-overdue",
        Urgency.IN_PROGRESS: "mw-task mw-in-progress",
        Urgency.NORMAL: "mw-task",
        Urgency.DONE: "mw-task mw-done",
        Urgency.WONT_DO: "mw-task mw-wont",
    }[urgency]


def urgency_badge(urgency: Urgency) -> str:
    if urgency == Urgency.OVERDUE:
        return '<span class="mw-badge mw-badge-overdue">Overdue</span>'
    if urgency == Urgency.IN_PROGRESS:
        return '<span class="mw-badge mw-badge-progress">In progress</span>'
    return ""


@st.cache_data(ttl=30)
def load_board(year: int, month: int, show_closed: bool) -> list[BoardTask]:
    store = get_store()
    templates = store.list_templates()
    completions = store.list_completions()
    today = today_in_tz()
    board = build_month_board(templates, completions, year, month, today)
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
        layout="wide",
    )
    inject_app_styles()

    settings = get_settings()
    today = today_in_tz()

    if "page" not in st.session_state:
        st.session_state.page = "board"
    if "drawer_task" not in st.session_state:
        st.session_state.drawer_task = None
    if "drawer_edit" not in st.session_state:
        st.session_state.drawer_edit = False

    with st.sidebar:
        st.header("Navigation")
        nav = st.radio(
            "View",
            ["Monthly board", "Manage contractors"],
            index=0 if st.session_state.page == "board" else 1,
            label_visibility="collapsed",
        )
        st.session_state.page = "board" if nav == "Monthly board" else "contractors"

        if st.session_state.page == "board":
            st.header("Month")
            year = st.number_input("Year", min_value=2020, max_value=2035, value=today.year)
            month = st.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda m: date(year, m, 1).strftime("%B"),
                index=today.month - 1,
            )
            show_closed = st.toggle("Show done & won't do", value=False)
            try:
                areas = sorted({t.area for t in get_store().list_templates()})
            except Exception:
                areas = []
            area_filter = st.multiselect("Area", options=areas)
            if st.button("Refresh", use_container_width=True):
                load_board.clear()
                st.session_state.drawer_task = None
                st.rerun()
        else:
            year = today.year
            month = today.month
            show_closed = False
            area_filter = []

    if st.session_state.page == "contractors":
        render_contractors_admin(get_store())
        return

    month_label = date(year, month, 1).strftime("%B %Y")
    main_col, drawer_col = st.columns([2, 1], gap="large")

    with main_col:
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
        inprog_n = sum(1 for r in board if r.urgency == Urgency.IN_PROGRESS)
        open_n = sum(1 for r in board if r.urgency == Urgency.NORMAL)

        s1, s2, s3 = st.columns(3)
        s1.metric("Overdue", overdue_n)
        s2.metric("In progress", inprog_n)
        s3.metric("Open", open_n)

        if not board:
            st.success("Nothing open for this month — or all tasks are complete.")
        else:
            store = get_store()
            for row in board:
                t = row.template
                badge = urgency_badge(row.urgency)
                meta = f"{t.area} · {t.priority} priority · {row.period}"
                last_html = ""
                if row.last_done_on:
                    last_html = f'<p class="mw-last">Last done {row.last_done_on.isoformat()}'
                    if row.last_done_notes:
                        last_html += f" — {row.last_done_notes}"
                    last_html += "</p>"

                card_html = (
                    f"{badge}"
                    f'<p class="mw-task-title">{t.name}</p>'
                    f'<p class="mw-meta">{meta}</p>'
                    f"{last_html}"
                )

                if row.urgency in (Urgency.DONE, Urgency.WONT_DO):
                    st.markdown(
                        f'<div class="mw-task-card {urgency_class(row.urgency)}">{card_html}</div>',
                        unsafe_allow_html=True,
                    )
                    continue

                with st.container(border=True):
                    uclass = urgency_class(row.urgency)
                    st.markdown(
                        f'<div class="{uclass} mw-task--open">{card_html}</div>',
                        unsafe_allow_html=True,
                    )
                    notes_key = f"notes_{t.task_id}_{row.period}"
                    notes = st.text_input(
                        "Completion note",
                        key=notes_key,
                        placeholder="Optional — saved on Done / Won't do",
                        label_visibility="collapsed",
                    )
                    b1, b2, b3, b4 = st.columns(4)
                    prog_key = f"prog_{t.task_id}_{row.period}"
                    with b1:
                        if st.button("In progress", key=prog_key, use_container_width=True):
                            try:
                                store.upsert_completion(
                                    t.task_id, row.period, "in_progress", today, notes or ""
                                )
                                load_board.clear()
                                st.rerun()
                            except Exception as err:
                                st.warning(str(err))
                    with b2:
                        if st.button(
                            "Done",
                            key=f"done_{t.task_id}_{row.period}",
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                store.upsert_completion(
                                    t.task_id, row.period, "done", today, notes or ""
                                )
                                load_board.clear()
                                st.rerun()
                            except Exception as err:
                                st.warning(str(err))
                    with b3:
                        if st.button(
                            "Won't do",
                            key=f"wont_{t.task_id}_{row.period}",
                            use_container_width=True,
                        ):
                            try:
                                store.upsert_completion(
                                    t.task_id, row.period, "wont_do", today, notes or ""
                                )
                                load_board.clear()
                                st.rerun()
                            except Exception as err:
                                st.warning(str(err))
                    det_key = f"det_{t.task_id}_{row.period}"
                    with b4:
                        if st.button("Details", key=det_key, use_container_width=True):
                            st.session_state.drawer_task = (t.task_id, row.period)
                            st.session_state.drawer_edit = False
                            st.rerun()

    with drawer_col:
        st.markdown("#### Details")
        if st.session_state.drawer_task:
            tid, period = st.session_state.drawer_task
            match = next(
                (r for r in board if r.template.task_id == tid and r.period == period),
                None,
            )
            if match:
                edit = st.toggle("Edit mode", value=st.session_state.drawer_edit)
                st.session_state.drawer_edit = edit
                render_drawer(match, get_store(), editing=edit)
                if st.button("Close drawer"):
                    st.session_state.drawer_task = None
                    st.rerun()
            else:
                st.caption("Select a task card.")
        else:
            st.caption("Choose **Details** on a task to open instructions, links, and contractor.")


if __name__ == "__main__":
    main()
