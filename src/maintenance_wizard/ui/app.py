"""Maintenance Wizard — monthly checklist (mockup C v4)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from maintenance_wizard.config import get_settings
from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.domain.display import display_task_name
from maintenance_wizard.models import BoardTask, Priority, Template, Urgency
from maintenance_wizard.store.factory import get_store
from maintenance_wizard.ui.access_gate import enforce_access_gate
from maintenance_wizard.ui.components.feedback import render_feedback_controls
from maintenance_wizard.ui.session_log import (
    BoardSessionTrace,
    build_session_log,
    latest_session_log_path,
    write_session_log,
)
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


def priority_badge(priority: Priority) -> str:
    css = {
        "High": "mw-priority-high",
        "Medium": "mw-priority-medium",
        "Low": "mw-priority-low",
    }.get(priority, "mw-priority-medium")
    return f'<span class="mw-priority-badge {css}">{priority}</span>'


def status_glyph(urgency: Urgency) -> str:
    if urgency == Urgency.OVERDUE:
        return '<span class="mw-status-icon mw-status-overdue" aria-hidden="true">!</span>'
    if urgency == Urgency.IN_PROGRESS:
        return '<span class="mw-status-icon mw-status-progress" aria-hidden="true">↻</span>'
    return '<span class="mw-status-icon mw-status-open" aria-hidden="true">◎</span>'


def format_card_meta(template: Template, period: str) -> str:
    """Mockup C v4 subline: area · type · effort · priority · Period YYYY-MM."""
    parts: list[str] = []
    if template.area:
        parts.append(template.area)
    if template.task_type:
        parts.append(template.task_type)
    if template.effort:
        parts.append(template.effort)
    if template.priority:
        parts.append(f"{template.priority} priority")
    parts.append(f"Period {period}")
    return " · ".join(parts)


def format_last_done_html(row: BoardTask) -> str:
    if not row.last_done_on:
        return ""
    d = row.last_done_on
    # Mockup format: "Last done Oct 12"
    label = d.strftime("%b %d")
    return f'<p class="mw-last">Last done {label}</p>'


def stats_pills_html(*, overdue: int, in_progress: int, open_count: int) -> str:
    return (
        '<div class="mw-stats-row">'
        f'<span class="mw-stat-pill mw-stat-overdue">'
        f'<span class="mw-stat-dot" aria-hidden="true">!</span> {overdue} overdue</span>'
        f'<span class="mw-stat-pill mw-stat-progress">'
        f'<span class="mw-stat-dot" aria-hidden="true">●</span> {in_progress} in progress</span>'
        f'<span class="mw-stat-pill mw-stat-open">'
        f'<span class="mw-stat-dot" aria-hidden="true">○</span> {open_count} open</span>'
        "</div>"
    )


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


def _render_sidebar_brand() -> None:
    st.markdown(
        '<div class="mw-sidebar-brand">'
        '<span class="mw-brand-icon" aria-hidden="true">🏠</span> '
        "<span>B &amp; R Home Maintenance</span></div>",
        unsafe_allow_html=True,
    )


def _render_month_chip(month_label: str) -> None:
    st.markdown(
        f'<div class="mw-month-chip" title="Selected month">'
        f'<span aria-hidden="true">📅</span> {month_label}</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="B & R Home Maintenance",
        page_icon="🏠",
        layout="wide",
    )
    enforce_access_gate()
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
        _render_sidebar_brand()
        st.divider()

        if st.button(
            "Monthly board",
            use_container_width=True,
            type="primary" if st.session_state.page == "board" else "secondary",
        ):
            st.session_state.page = "board"
            st.rerun()

        if st.session_state.page == "board":
            st.markdown("**Filter by month**")
            year = st.number_input("Year", min_value=2020, max_value=2035, value=today.year)
            month = st.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda m: date(year, m, 1).strftime("%B"),
                index=today.month - 1,
            )
            month_label = date(year, month, 1).strftime("%b %Y")
            _render_month_chip(month_label)

            show_closed = st.toggle("Show done & won't do", value=False)
            try:
                templates = get_store().list_templates()
                areas = sorted({t.area for t in templates})
                types = sorted({t.task_type for t in templates if t.task_type})
                seasons = sorted({t.season for t in templates if t.season})
            except Exception:
                areas = []
                types = []
                seasons = []
            # Category buttons with icons (mockup C v4)
            area_icons = {
                "HVAC": "❄️",
                "Plumbing": "💧",
                "Electrical": "⚡",
                "Laundry": "🧺",
                "Settings": "⚙️",
            }
            if areas:
                st.markdown("#### Categories")
                for area in areas:
                    icon = area_icons.get(area, "⚙️")
                    st.button(
                        f"{icon}  {area}",
                        key=f"cat_{area}",
                        use_container_width=True,
                        type="secondary",
                    )
                st.markdown("---")
                area_filter = st.multiselect("Area", options=areas)
            else:
                area_filter = []
            type_filter = st.multiselect("Type", options=types)
            season_filter = st.multiselect("Season", options=seasons)
            if st.button("Refresh", use_container_width=True):
                load_board.clear()
                st.session_state.drawer_task = None
                st.rerun()
            latest = latest_session_log_path()
            with st.expander("Session debug", expanded=False):
                if latest and latest.is_file():
                    st.caption(f"Latest log: `{latest.name}`")
                    st.download_button(
                        "Download debug JSON",
                        data=latest.read_text(encoding="utf-8"),
                        file_name=latest.name,
                        mime="application/json",
                        use_container_width=True,
                    )
                else:
                    st.caption("No session log yet — open the monthly board.")
        else:
            year = today.year
            month = today.month
            show_closed = False
            area_filter = []
            type_filter = []
            season_filter = []

        st.divider()
        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        if st.button(
            "👥  Manage contractors",
            use_container_width=True,
            type="primary" if st.session_state.page == "contractors" else "secondary",
        ):
            st.session_state.page = "contractors"
            st.rerun()

    if st.session_state.page == "contractors":
        render_contractors_admin(get_store())
        return

    month_label_long = date(year, month, 1).strftime("%B %Y")
    main_col, drawer_col = st.columns([2, 1], gap="large")

    with main_col:
        title_col, fb_col = st.columns([5, 1])
        with title_col:
            st.markdown(
                f'<h2 class="mw-board-month">{month_label_long}</h2>',
                unsafe_allow_html=True,
            )
            st.caption(f"Data source: {settings.store}")
        with fb_col:
            render_feedback_controls(surface="monthly")

        try:
            board = load_board(year, month, show_closed)
        except Exception as exc:
            st.error(f"Could not load tasks: {exc}")
            st.info("Local mode: run `just init-local-data` then `just ui`.")
            return

        if area_filter:
            board = [r for r in board if r.template.area in area_filter]
        if type_filter:
            board = [r for r in board if r.template.task_type in type_filter]
        if season_filter:
            board = [r for r in board if r.template.season in season_filter]

        trace = BoardSessionTrace(
            month_key=f"{year:04d}-{month:02d}",
            store_mode=settings.store,
            filters={
                "areas": area_filter,
                "types": type_filter,
                "seasons": season_filter,
            },
        )
        trace.record_board(board)
        session_log = build_session_log(trace)
        log_path = write_session_log(session_log)
        st.session_state.mw_session_debug_log = session_log
        st.session_state.mw_session_debug_path = str(log_path) if log_path else None

        overdue_n = sum(1 for r in board if r.urgency == Urgency.OVERDUE)
        inprog_n = sum(1 for r in board if r.urgency == Urgency.IN_PROGRESS)
        open_n = sum(1 for r in board if r.urgency == Urgency.NORMAL)

        pill_row, sort_col = st.columns([3, 1])
        with pill_row:
            st.markdown(
                stats_pills_html(
                    overdue=overdue_n,
                    in_progress=inprog_n,
                    open_count=open_n,
                ),
                unsafe_allow_html=True,
            )
        with sort_col:
            st.selectbox(
                "Sorted by",
                ["Priority (High → Low)"],
                index=0,
                label_visibility="visible",
            )

        st.markdown(
            '<p class="mw-sort-caption">Urgency first, then priority, area, and name.</p>',
            unsafe_allow_html=True,
        )

        if not board:
            st.success("Nothing open for this month — or all tasks are complete.")
        else:
            store = get_store()
            for row in board:
                t = row.template
                badge = urgency_badge(row.urgency)
                prio = priority_badge(t.priority)
                glyph = status_glyph(row.urgency)
                meta = format_card_meta(t, row.period)
                last_html = format_last_done_html(row)

                head_html = (
                    f'<div class="mw-card-head">'
                    f"{glyph}"
                    f'<div class="mw-card-head-text">'
                    f'<div class="mw-title-row">'
                    f'<span class="mw-task-title">{display_task_name(t.name)}</span>{badge}</div>'
                    f'<div class="mw-meta-row">'
                    f'<p class="mw-meta">{meta}</p>{prio}</div>'
                    f"{last_html}"
                    f"</div></div>"
                )

                if row.urgency in (Urgency.DONE, Urgency.WONT_DO):
                    st.markdown(
                        f'<div class="mw-task-card {urgency_class(row.urgency)}">{head_html}</div>',
                        unsafe_allow_html=True,
                    )
                    continue

                with st.container(border=True):
                    uclass = urgency_class(row.urgency)
                    head_col, det_col = st.columns([6, 1], vertical_alignment="top")
                    with head_col:
                        st.markdown(
                            f'<div class="mw-task-shell {uclass} mw-task--open">{head_html}</div>',
                            unsafe_allow_html=True,
                        )
                    with det_col:
                        st.markdown(
                            '<span class="mw-card-details-anchor" aria-hidden="true"></span>',
                            unsafe_allow_html=True,
                        )
                        det_key = f"det_{t.task_id}_{row.period}"
                        if st.button("Details", key=det_key, type="secondary"):
                            st.session_state.drawer_task = (t.task_id, row.period)
                            st.session_state.drawer_edit = False
                            st.rerun()
                    notes_key = f"notes_{t.task_id}_{row.period}"
                    notes = st.text_input(
                        "Completion note",
                        key=notes_key,
                        placeholder="Add note for this completion (optional)",
                        label_visibility="collapsed",
                    )
                    b1, b2, b3 = st.columns(3)
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
                        wont_key = f"wont_{t.task_id}_{row.period}"
                        if st.button("Won't do", key=wont_key, use_container_width=True):
                            try:
                                store.upsert_completion(
                                    t.task_id, row.period, "wont_do", today, notes or ""
                                )
                                load_board.clear()
                                st.rerun()
                            except Exception as err:
                                st.warning(str(err))
                    with b3:
                        done_key = f"done_{t.task_id}_{row.period}"
                        if st.button(
                            "Done",
                            key=done_key,
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

    with drawer_col:
        st.markdown(
            '<span class="mw-drawer-root" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
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
