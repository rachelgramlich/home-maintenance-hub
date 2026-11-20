from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from maintenance_wizard.config import get_settings
from maintenance_wizard.domain.display import display_task_name
from maintenance_wizard.domain.schedule import board_period_for_task
from maintenance_wizard.models import Contractor, Template
from maintenance_wizard.store.base import TaskStore

TRADES = ["Plumber", "HVAC", "Electrician", "General", "Duct cleaning", "Other"]


def render_contractors_admin(store: TaskStore) -> None:
    st.header("Manage contractors")
    st.caption("Contact records linked from task details. Store: " + type(store).__name__)

    contractors = store.list_contractors(active_only=False)
    templates = store.list_templates()
    task_counts: dict[str, int] = {}
    tasks_by_contractor: dict[str, list[Template]] = {}
    for tmpl in templates:
        if tmpl.contractor_id:
            task_counts[tmpl.contractor_id] = task_counts.get(tmpl.contractor_id, 0) + 1
            tasks_by_contractor.setdefault(tmpl.contractor_id, []).append(tmpl)

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
            with st.expander(f"Edit {c.name}"):
                linked = tasks_by_contractor.get(c.contractor_id, [])
                if linked:
                    st.markdown(f"**Linked tasks ({len(linked)})**")
                    tz = ZoneInfo(get_settings().timezone)
                    today = datetime.now(tz).date()
                    for tmpl in sorted(linked, key=lambda t: t.name.lower()):
                        period = board_period_for_task(tmpl, today.year, today.month)
                        label = display_task_name(tmpl.name)
                        if st.button(
                            f"Open board · {label}",
                            key=f"ctr_task_{c.contractor_id}_{tmpl.task_id}",
                            use_container_width=True,
                        ):
                            st.session_state.page = "board"
                            st.session_state.drawer_task = (tmpl.task_id, period)
                            st.session_state.drawer_edit = False
                            st.rerun()
                    st.divider()
                _contractor_form(store, c)
            st.divider()
    else:
        st.info("No contractors yet.")

    with st.expander("Add contractor"):
        _contractor_form(store, None)


def _contractor_form(store: TaskStore, existing: Contractor | None) -> None:
    prefix = existing.contractor_id if existing else "new"
    name = st.text_input("Name", value=existing.name if existing else "", key=f"ctr_name_{prefix}")
    trade_choices = TRADES
    if existing and existing.trade in trade_choices:
        trade_idx = trade_choices.index(existing.trade)
    else:
        trade_idx = 0
    trade = st.selectbox("Trade", trade_choices, index=trade_idx, key=f"ctr_trade_{prefix}")
    phone = st.text_input(
        "Phone", value=existing.phone if existing else "", key=f"ctr_phone_{prefix}"
    )
    email = st.text_input(
        "Email", value=existing.email if existing else "", key=f"ctr_email_{prefix}"
    )
    website = st.text_input(
        "Website", value=existing.website if existing else "", key=f"ctr_web_{prefix}"
    )
    notes = st.text_area(
        "Notes", value=existing.notes if existing else "", key=f"ctr_notes_{prefix}"
    )
    active = (
        True
        if existing is None
        else st.checkbox("Active", value=existing.active, key=f"ctr_active_{prefix}")
    )

    label = "Save changes" if existing else "Save contractor"
    if st.button(label, type="primary", key=f"ctr_save_{prefix}"):
        if not name.strip():
            st.warning("Name is required.")
            return
        try:
            store.upsert_contractor(
                Contractor(
                    contractor_id=existing.contractor_id if existing else "",
                    name=name.strip(),
                    trade=trade,
                    phone=phone,
                    email=email,
                    website=website,
                    notes=notes,
                    active=active,
                )
            )
            st.success("Saved.")
            st.rerun()
        except NotImplementedError:
            st.warning("Contractor CRUD requires the Notion store.")
