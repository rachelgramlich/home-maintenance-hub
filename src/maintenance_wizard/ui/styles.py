"""Inject Maintenance Wizard theme + component CSS."""

from __future__ import annotations

import streamlit as st

from maintenance_wizard.ui.theme import APP_THEME_STATIC_CSS, app_theme_css


@st.cache_resource
def _cached_theme_markup(css_mtime_ns: int) -> str:
    del css_mtime_ns
    return app_theme_css()


def inject_app_styles() -> None:
    mtime_ns = int(APP_THEME_STATIC_CSS.stat().st_mtime_ns) if APP_THEME_STATIC_CSS.is_file() else 0
    st.markdown(_cached_theme_markup(mtime_ns), unsafe_allow_html=True)