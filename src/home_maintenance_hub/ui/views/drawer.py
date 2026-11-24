from __future__ import annotations

import html
from datetime import date

import streamlit as st

from home_maintenance_hub.domain.display import display_task_name
from home_maintenance_hub.domain.schedule import period_full_month_year_label
from home_maintenance_hub.models import BoardTask, Template, Urgency
from home_maintenance_hub.store.base import TaskStore


def task_context_fields(template: Template, period: str) -> list[tuple[str, str]]:
    """Labeled task metadata shown in the drawer view (not on board cards)."""
    month_slot = template.month_name or str(template.due_month)
    fields: list[tuple[str, str]] = [
        ("Area", template.area or "—"),
        ("Type", template.task_type or "—"),
        ("Effort", template.effort or "—"),
        ("Priority", template.priority or "—"),
        ("Season", template.season or "—"),
        ("Month slot", month_slot),
        ("Period", period),
    ]
    cadence_label = "Monthly" if template.cadence == "monthly" else "Annual"
    fields.append(("Cadence", cadence_label))
    return fields


def format_drawer_task_meta(template: Template, period: str) -> str:
    """Compact meta line (legacy helper for tests and quick scans)."""
    return " · ".join(f"{label}: {value}" for label, value in task_context_fields(template, period))


def _status_badge_html(urgency: Urgency, *, period: str | None = None) -> str:
    if urgency == Urgency.OVERDUE:
        if period:
            text = f"Overdue: {period_full_month_year_label(period)}"
        else:
            text = "Overdue"
        return f'<span class="mw-badge mw-badge-overdue">{text}</span>'
    if urgency == Urgency.IN_PROGRESS:
        return '<span class="mw-badge mw-badge-progress">In progress</span>'
    if urgency == Urgency.DONE:
        return '<span class="mw-badge mw-badge-done">Done</span>'
    if urgency == Urgency.WONT_DO:
        return '<span class="mw-badge mw-badge-wont">Won\'t do</span>'
    return '<span class="mw-badge mw-badge-open">Open</span>'


def _section_title(label: str, *, first: bool = False) -> None:
    extra = " mw-drawer-section-title--first" if first else ""
    st.markdown(
        f'<p class="mw-drawer-section-title{extra}"><strong>{label}</strong></p>',
        unsafe_allow_html=True,
    )


def _render_task_context(template: Template, period: str) -> None:
    rows = task_context_fields(template, period)
    parts = [
        '<div class="mw-drawer-fields">',
    ]
    for label, value in rows:
        safe_label = html.escape(label)
        safe_value = html.escape(value)
        parts.append(
            f'<div class="mw-drawer-field">'
            f'<span class="mw-drawer-field-label">{safe_label}</span>'
            f'<span class="mw-drawer-field-value">{safe_value}</span>'
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _empty_value() -> None:
    st.markdown('<p class="mw-drawer-empty">—</p>', unsafe_allow_html=True)


def render_drawer(row: BoardTask, store: TaskStore, *, editing: bool) -> None:
    t = row.template
    title = html.escape(display_task_name(t.name))
    badge = _status_badge_html(row.urgency, period=row.period)
    st.markdown(
        f'<div class="mw-drawer-header"><h3 class="mw-drawer-task-title">{title}</h3>{badge}</div>',
        unsafe_allow_html=True,
    )

    if editing:
        _section_title("Edit task", first=True)
        _edit_form(t, store)
        if t.notion_url:
            st.link_button("Open in Notion", t.notion_url)
        return

    _section_title("Task details", first=True)
    _render_task_context(t, row.period)

    if t.notion_url:
        st.link_button("Open in Notion", t.notion_url)

    _section_title("Instructions")
    if t.instructions:
        st.write(t.instructions)
    else:
        _empty_value()

    contractor = store.get_contractor(t.contractor_id) if t.contractor_id else None
    _section_title("Contractor")
    if contractor:
        st.write(f"**{contractor.name}** · {contractor.trade or '—'}")
        if contractor.phone:
            st.markdown(f"Phone: [{contractor.phone}](tel:{contractor.phone})")
        else:
            st.caption("Phone: —")
        if contractor.email:
            st.markdown(f"Email: [{contractor.email}](mailto:{contractor.email})")
        else:
            st.caption("Email: —")
    else:
        _empty_value()

    if st.button("Manage contractors", key=f"mwc_{t.task_id}"):
        st.session_state.page = "contractors"
        st.rerun()

    _section_title("Last done")
    if row.last_done_on:
        st.write(
            f"{row.last_done_on.isoformat()}"
            + (f" — {row.last_done_notes}" if row.last_done_notes else "")
        )
    else:
        _empty_value()
    st.caption("Completion history is read-only here.")


def _edit_form(template: Template, store: TaskStore) -> None:
    name = st.text_input("Task name", value=template.name)
    instructions = st.text_area(
        "Instructions",
        value=template.instructions,
        height=120,
        help="How to do the task. Paste URLs here if you need reference links.",
    )
    areas = [
        "HVAC",
        "Plumbing",
        "Exterior",
        "Laundry",
        "Appliances",
        "Safety",
        "Pest",
        "Electrical",
        "Other",
    ]
    area_idx = areas.index(template.area) if template.area in areas else len(areas) - 1
    area = st.selectbox("Area", areas, index=area_idx)
    prios = ["High", "Medium", "Low"]
    priority = st.selectbox(
        "Priority",
        prios,
        index=prios.index(template.priority),
    )
    types = ["Replace", "Service", "Clean", "Inspect/Test", ""]
    type_idx = types.index(template.task_type) if template.task_type in types else len(types) - 1
    task_type = st.selectbox("Type", types, index=type_idx)
    efforts = ["XS", "S", "M", ""]
    effort_idx = efforts.index(template.effort) if template.effort in efforts else len(efforts) - 1
    effort = st.selectbox("Effort", efforts, index=effort_idx)
    seasons = ["", "Winter", "Spring", "Summer", "Fall"]
    season_idx = seasons.index(template.season) if template.season in seasons else 0
    season = st.selectbox("Season", seasons, index=season_idx)
    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    due_month = st.selectbox(
        "Due month",
        list(range(1, 13)),
        index=max(0, template.due_month - 1),
        format_func=lambda m: date(2000, m, 1).strftime("%B"),
    )
    month_name = st.selectbox(
        "Month label",
        month_names,
        index=month_names.index(template.month_name) if template.month_name in month_names else 0,
    )
    cadence_options = ["annual", "monthly"]
    cadence = st.selectbox(
        "Cadence",
        cadence_options,
        index=cadence_options.index(template.cadence),
    )
    active = st.toggle("Active", value=template.active)
    contractors = store.list_contractors()
    ctr_names = ["— none —"] + [c.name for c in contractors]
    ctr_ids = [None] + [c.contractor_id for c in contractors]
    sel = 0
    if template.contractor_id in ctr_ids:
        sel = ctr_ids.index(template.contractor_id)
    ctr_pick = st.selectbox("Contractor", ctr_names, index=sel)
    ctr_id = ctr_ids[ctr_names.index(ctr_pick)] if ctr_pick != "— none —" else None

    if st.button("Save task", type="primary"):
        updated = Template(
            task_id=template.task_id,
            name=name,
            due_month=due_month,
            area=area,
            active=active,
            month_name=month_name,
            task_type=task_type,
            effort=effort,
            priority=priority,  # type: ignore[arg-type]
            season=season,
            instructions=instructions,
            contractor_id=ctr_id,
            stable_key=template.stable_key,
            notion_url=template.notion_url,
            cadence=cadence,  # type: ignore[arg-type]
        )
        try:
            store.update_task(updated)
            st.success("Saved.")
        except NotImplementedError:
            st.warning("Task edit requires the Notion store.")
