"""Google OIDC allowlist gate for Streamlit Community Cloud."""

from __future__ import annotations

import streamlit as st

from maintenance_wizard.config import Settings, get_settings


def enforce_access_gate(*, settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    if not cfg.require_auth:
        return
    if not st.user.is_logged_in:
        st.login("google")
        st.stop()

    raw = cfg.auth_email_allowlist or ""
    allowlist = {email.strip().lower() for email in raw.split(",") if email.strip()}
    if not allowlist:
        return

    email = (st.user.email or "").strip().lower()
    if email not in allowlist:
        st.error("This app is limited to authorized household Google accounts.")
        st.stop()
