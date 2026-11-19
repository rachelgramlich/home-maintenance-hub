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
            st.markdown("**Instructions**")
            st.write(t.instructions)
        if t.links:
            st.markdown("**Links**")
            for link in t.links:
                st.markdown(f"- [{link.label}]({link.url})")
        contractor = store.get_contractor(t.contractor_id) if t.contractor_id else None
        if contractor:
            st.markdown("**Contractor**")
            st.write(f"{contractor.name} · {contractor.trade}")
            if contractor.phone:
                st.markdown(f"[Call](tel:{contractor.phone})")
        if row.last_done_on:
            st.markdown(
                f"**Last done** {row.last_done_on.isoformat()}"
                + (f" — {row.last_done_notes}" if row.last_done_notes else "")
            )
        st.caption("Completion history is read-only here.")


def _edit_form(template: Template, store: TaskStore) -> None:
    name = st.text_input("Task name", value=template.name)
    area = st.text_input("Area", value=template.area)
    prios = ["High", "Medium", "Low"]
    priority = st.selectbox(
        "Priority",
        prios,
        index=prios.index(template.priority),
    )
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
            task_type=template.task_type,
            effort=template.effort,
            priority=priority,  # type: ignore[arg-type]
            season=template.season,
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
