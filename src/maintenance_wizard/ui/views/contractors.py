from __future__ import annotations

import streamlit as st

from maintenance_wizard.models import Contractor
from maintenance_wizard.store.base import TaskStore


def render_contractors_admin(store: TaskStore) -> None:
    st.header("Manage contractors")
    st.caption("Contact records linked from task details. Store: " + type(store).__name__)

    contractors = store.list_contractors(active_only=False)
    task_counts: dict[str, int] = {}
    for tmpl in store.list_templates():
        if tmpl.contractor_id:
            task_counts[tmpl.contractor_id] = task_counts.get(tmpl.contractor_id, 0) + 1

    if contractors:
        for c in contractors:
            n = task_counts.get(c.contractor_id, 0)
            status = "active" if c.active else "inactive"
            st.markdown(f"**{c.name}** · {c.trade} · {status} · used by **{n}** tasks")
            cols = st.columns(3)
            if c.phone:
                cols[0].markdown(f"[{c.phone}](tel:{c.phone})")
            if c.email:
                cols[1].markdown(f"[{c.email}](mailto:{c.email})")
            if c.website:
                cols[2].markdown(f"[Website]({c.website})")
            if c.notes:
                st.caption(c.notes)
            st.divider()
    else:
        st.info("No contractors yet.")

    with st.expander("Add contractor"):
        name = st.text_input("Name", key="new_ctr_name")
        trade = st.selectbox(
            "Trade",
            ["Plumber", "HVAC", "Electrician", "General", "Duct cleaning", "Other"],
            key="new_ctr_trade",
        )
        phone = st.text_input("Phone", key="new_ctr_phone")
        email = st.text_input("Email", key="new_ctr_email")
        website = st.text_input("Website", key="new_ctr_web")
        notes = st.text_area("Notes", key="new_ctr_notes")
        if st.button("Save contractor", type="primary"):
            try:
                store.upsert_contractor(
                    Contractor(
                        contractor_id="",
                        name=name,
                        trade=trade,
                        phone=phone,
                        email=email,
                        website=website,
                        notes=notes,
                        active=True,
                    )
                )
                st.success("Saved.")
                st.rerun()
            except NotImplementedError:
                st.warning("Contractor CRUD requires the Notion store.")
