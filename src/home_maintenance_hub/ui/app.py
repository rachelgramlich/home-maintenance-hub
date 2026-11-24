"""Home Maintenance Hub — monthly checklist (mockup C v4)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.domain.board import build_month_board
from home_maintenance_hub.domain.display import display_task_name
from home_maintenance_hub.domain.schedule import period_full_month_year_label
from home_maintenance_hub.models import BoardTask, Priority, Urgency
from home_maintenance_hub.store.factory import get_store
from home_maintenance_hub.ui.access_gate import enforce_access_gate
from home_maintenance_hub.ui.components.feedback import render_feedback_controls
from home_maintenance_hub.ui.session_log import (
    BoardSessionTrace,
    build_session_log,
    latest_session_log_path,
    write_session_log,
)
from home_maintenance_hub.ui.styles import inject_app_styles
from home_maintenance_hub.ui.views.contractors import render_contractors_admin
from home_maintenance_hub.ui.views.drawer import render_drawer
from home_maintenance_hub.ui.views.settings import render_settings_page


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


def urgency_badge(urgency: Urgency, *, period: str | None = None) -> str:
    if urgency == Urgency.OVERDUE:
        if period:
            month_label = period_full_month_year_label(period)
            text = f"Overdue: {month_label}"
        else:
            text = "Overdue"
        return f'<span class="mw-badge mw-badge-overdue">{text}</span>'
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


def _open_task_drawer(task_id: str, period: str) -> None:
    st.session_state.drawer_task = (task_id, period)
    st.session_state.drawer_edit = False
    st.rerun()


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


APP_DISPLAY_NAME = "B & R Home Maintenance"


def _render_main_hero(month_label_long: str) -> None:
    st.markdown(
        '<div class="mw-hero">'
        f"<h1>{APP_DISPLAY_NAME}</h1>"
        f'<p class="mw-hero-month mw-board-month">{month_label_long}</p>'
        "</div>",
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
        initial_sidebar_state="expanded",
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
    if "mw_area_filter" not in st.session_state:
        st.session_state.mw_area_filter = []
    if "mw_sidebar_collapsed" not in st.session_state:
        st.session_state.mw_sidebar_collapsed = False
    if "mw_board_year" not in st.session_state:
        st.session_state.mw_board_year = today.year
    if "mw_board_month" not in st.session_state:
        st.session_state.mw_board_month = today.month
    if "mw_show_closed" not in st.session_state:
        st.session_state.mw_show_closed = False
    if "mw_type_filter" not in st.session_state:
        st.session_state.mw_type_filter = []
    if "mw_season_filter" not in st.session_state:
        st.session_state.mw_season_filter = []

    if st.session_state.drawer_task and st.session_state.mw_sidebar_collapsed:
        st.session_state.mw_sidebar_collapsed = False

    collapsed = st.session_state.mw_sidebar_collapsed
    layout_marker = "mw-layout-sidebar-collapsed" if collapsed else "mw-layout-sidebar-expanded"
    st.markdown(
        f'<span class="{layout_marker}" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        if collapsed:
            st.markdown(
                '<span class="mw-sidebar-rail" aria-hidden="true"></span>',
                unsafe_allow_html=True,
            )
            if st.button(
                "▶",
                key="mw_sidebar_expand",
                help="Expand navigation",
                type="secondary",
            ):
                st.session_state.mw_sidebar_collapsed = False
                st.rerun()
        else:
            _, collapse_col = st.columns([5, 1])
            with collapse_col:
                if st.button(
                    "◀",
                    key="mw_sidebar_collapse",
                    help="Collapse navigation",
                    type="secondary",
                ):
                    st.session_state.mw_sidebar_collapsed = True
                    st.rerun()
            st.divider()

        if not collapsed:
            if st.button(
                "Monthly board",
                use_container_width=True,
                type="primary" if st.session_state.page == "board" else "secondary",
            ):
                st.session_state.page = "board"
                st.rerun()

            if st.button(
                "⚙️  Settings",
                use_container_width=True,
                type="primary" if st.session_state.page == "settings" else "secondary",
                key="settings_nav",
            ):
                st.session_state.page = "settings"
                st.rerun()

        if st.session_state.page == "board" and not collapsed:
            st.markdown("**Filter by month**")
            year = st.number_input(
                "Year",
                min_value=2020,
                max_value=2035,
                key="mw_board_year",
            )
            month = st.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda m: date(year, m, 1).strftime("%B"),
                key="mw_board_month",
            )
            month_label = date(year, month, 1).strftime("%b %Y")
            _render_month_chip(month_label)

            show_closed = st.toggle("Show done & won't do", key="mw_show_closed")
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
                selected_areas = set(st.session_state.mw_area_filter)
                for area in areas:
                    icon = area_icons.get(area, "⚙️")
                    active = area in selected_areas
                    if st.button(
                        f"{icon}  {area}",
                        key=f"cat_{area}",
                        use_container_width=True,
                        type="primary" if active else "secondary",
                    ):
                        if active:
                            selected_areas.discard(area)
                        else:
                            selected_areas.add(area)
                        st.session_state.mw_area_filter = sorted(selected_areas)
                        load_board.clear()
                        st.rerun()
                if selected_areas and st.button("Clear category filters", use_container_width=True):
                    st.session_state.mw_area_filter = []
                    load_board.clear()
                    st.rerun()
                st.markdown("---")
                area_filter = list(st.session_state.mw_area_filter)
            else:
                area_filter = []
            type_filter = st.multiselect("Type", options=types, key="mw_type_filter")
            season_filter = st.multiselect("Season", options=seasons, key="mw_season_filter")
            if st.button("Refresh", use_container_width=True):
                load_board.clear()
                st.session_state.drawer_task = None
                st.session_state.mw_area_filter = []
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
        elif st.session_state.page == "board":
            year = int(st.session_state.mw_board_year)
            month = int(st.session_state.mw_board_month)
            show_closed = bool(st.session_state.mw_show_closed)
            area_filter = list(st.session_state.mw_area_filter)
            type_filter = list(st.session_state.mw_type_filter)
            season_filter = list(st.session_state.mw_season_filter)
        else:
            year = today.year
            month = today.month
            show_closed = False
            area_filter = []
            type_filter = []
            season_filter = []

        if not collapsed:
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

    if st.session_state.page == "settings":
        render_settings_page(settings)
        return

    month_label_long = date(year, month, 1).strftime("%B %Y")

    _render_main_hero(month_label_long)
    _fb_pad, _fb_col = st.columns([3, 2])
    with _fb_col:
        st.markdown(
            '<span class="mw-feedback-anchor" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
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

    if not board:
        st.success("Nothing open for this month — or all tasks are complete.")
    else:
        store = get_store()
        for row in board:
            t = row.template
            badge = urgency_badge(row.urgency, period=row.period)
            prio = priority_badge(t.priority)
            glyph = status_glyph(row.urgency)
            last_html = format_last_done_html(row)

            task_name = display_task_name(t.name)
            title_html = (
                f'<div class="mw-card-title-block">'
                f"{glyph}"
                f'<span class="mw-task-title">{task_name}</span>'
                f"</div>"
                f"{last_html}"
            )
            meta_badges_html = f'<span class="mw-card-meta-badges">{prio}{badge}</span>'

            if row.urgency in (Urgency.DONE, Urgency.WONT_DO):
                closed_html = (
                    f"{title_html}"
                    f'<div class="mw-card-meta-row mw-card-meta-row--closed">'
                    f"{meta_badges_html}</div>"
                )
                st.markdown(
                    f'<div class="mw-task-card {urgency_class(row.urgency)}">{closed_html}</div>',
                    unsafe_allow_html=True,
                )
                continue

            with st.container(border=True):
                uclass = urgency_class(row.urgency)
                st.markdown(
                    f'<span class="mw-task-shell {uclass} mw-task--open" aria-hidden="true"></span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"{title_html}{last_html}", unsafe_allow_html=True)
                det_key = f"det_{t.task_id}_{row.period}"
                with st.container(
                    horizontal=True,
                    gap="small",
                    vertical_alignment="center",
                    wrap=False,
                    key=f"det_row_{t.task_id}_{row.period}",
                ):
                    st.markdown(
                        f'<div class="mw-card-meta-row mw-card-meta-row--open">'
                        f"{meta_badges_html}</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Details",
                        key=det_key,
                        type="tertiary",
                        help=f"Open details for {task_name}",
                    ):
                        _open_task_drawer(t.task_id, row.period)
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

    if st.session_state.drawer_task:
        st.markdown(
            '<span class="mw-drawer-backdrop-anchor" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Close details overlay",
            key="mw_drawer_backdrop",
            type="secondary",
            help="Click the dimmed board area to close",
        ):
            st.session_state.drawer_task = None
            st.session_state.drawer_edit = False
            st.rerun()

        with st.container():
            st.markdown(
                '<span class="mw-drawer-overlay-mount" aria-hidden="true"></span>',
                unsafe_allow_html=True,
            )
            close_col, title_col = st.columns([1, 5], vertical_alignment="center")
            with close_col:
                if st.button("←", key="mw_drawer_close", help="Close details", type="secondary"):
                    st.session_state.drawer_task = None
                    st.session_state.drawer_edit = False
                    st.rerun()
            with title_col:
                st.markdown("**Details**")
            tid, period = st.session_state.drawer_task
            match = next(
                (r for r in board if r.template.task_id == tid and r.period == period),
                None,
            )
            if match:
                edit = st.toggle("Edit mode", value=st.session_state.drawer_edit)
                st.session_state.drawer_edit = edit
                render_drawer(match, get_store(), editing=edit)
            else:
                st.caption("Task not found in the current board view.")
                if st.button("← Back", key="mw_drawer_close_empty", type="secondary"):
                    st.session_state.drawer_task = None
                    st.rerun()


if __name__ == "__main__":
    main()
