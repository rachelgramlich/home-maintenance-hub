from __future__ import annotations

import streamlit as st

from maintenance_wizard.models import BoardTask, Template
from maintenance_wizard.store.base import TaskStore


def render_drawer(row: BoardTask, store: TaskStore, *, editing: bool) -> None:
    t = row.template
    st.markdown(f"### {t.name}")
    st.caption(f"{t.area} · {t.month_name or t.due_month} · {row.period}")
    if t.notion_url:
        st.link_button("Open in Notion", t.notion_url)

    if editing:
        _edit_form(t, store)
    else:
        if t.instructions:
            st.markdown('<div class="mw-drawer-section">', unsafe_allow_html=True)
            st.markdown("**Instructions**")
            st.write(t.instructions)
            st.markdown("</div>", unsafe_allow_html=True)
        if t.links:
            st.markdown('<div class="mw-drawer-section">', unsafe_allow_html=True)
            st.markdown("**Links**")
            for link in t.links:
                st.markdown(f"- [{link.label}]({link.url})")
            st.markdown("</div>", unsafe_allow_html=True)
        contractor = store.get_contractor(t.contractor_id) if t.contractor_id else None
        if contractor:
            st.markdown('<div class="mw-drawer-section">', unsafe_allow_html=True)
            st.markdown("**Contractor**")
            st.write(f"{contractor.name} · {contractor.trade}")
            if contractor.phone:
                st.markdown(f"[Call](tel:{contractor.phone})")
            if contractor.email:
                st.markdown(f"[Email](mailto:{contractor.email})")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Manage contractors", key=f"mwc_{t.task_id}"):
            st.session_state.page = "contractors"
            st.rerun()
        if row.last_done_on:
            st.markdown(
                f"**Last done** {row.last_done_on.isoformat()}"
                + (f" — {row.last_done_notes}" if row.last_done_notes else "")
            )
        st.caption("Completion history is read-only here.")


def _edit_form(template: Template, store: TaskStore) -> None:
    name = st.text_input("Task name", value=template.name)
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
    instructions = st.text_area("Instructions", value=template.instructions, height=120)
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
            due_month=template.due_month,
            area=area,
            active=template.active,
            month_name=template.month_name,
            task_type=task_type,
            effort=effort,
            priority=priority,  # type: ignore[arg-type]
            season=season,
            instructions=instructions,
            links=template.links,
            contractor_id=ctr_id,
            stable_key=template.stable_key,
            notion_url=template.notion_url,
        )
        try:
            store.update_task(updated)
            st.success("Saved.")
        except NotImplementedError:
            st.warning("Task edit requires the Notion store.")
