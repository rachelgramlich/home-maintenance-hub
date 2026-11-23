"""Read-only household settings (no secrets in UI)."""

from __future__ import annotations

import streamlit as st

from home_maintenance_hub.config import Settings

DEPLOYMENT_DOC = "https://github.com/rachelgramlich/home-maintenance-hub/blob/main/docs/DEPLOYMENT.md"


def render_settings_page(settings: Settings) -> None:
    st.header("Settings")
    st.caption("Household configuration is set via environment variables and Streamlit secrets.")

    st.subheader("Data & time")
    st.text_input("Timezone", value=settings.timezone, disabled=True)
    st.text_input("Store mode", value=settings.store, disabled=True)
    if settings.store == "notion":
        st.caption("Notion database IDs and API key are configured in deployment secrets only.")

    st.subheader("Access control")
    st.checkbox("Require Google sign-in", value=settings.require_auth, disabled=True)
    raw = settings.auth_email_allowlist or ""
    emails = [e.strip() for e in raw.split(",") if e.strip()]
    if emails:
        st.caption(f"Allowlist: {len(emails)} authorized email(s) (addresses not shown).")
    else:
        st.caption("No email allowlist configured — any signed-in user may access when auth is on.")

    st.subheader("Operations")
    st.markdown(
        f"- [Deployment runbook]({DEPLOYMENT_DOC}) — Streamlit Community Cloud, "
        "Notion, and auth setup."
    )
    notion_doc = (
        "https://github.com/rachelgramlich/home-maintenance-hub/blob/main/docs/NOTION_SETUP.md"
    )
    st.markdown(f"- [Notion setup guide]({notion_doc})")
