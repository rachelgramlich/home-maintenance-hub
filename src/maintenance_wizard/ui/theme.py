"""Lavender Streamlit theme (Grocery Wizard contrast pattern)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

MIN_CONTRAST_RATIO_AA: Final[float] = 4.5

APP_THEME_STATIC_CSS = Path(__file__).resolve().parent / "static" / "app_theme.css"


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    bg: str
    text: str
    text_muted: str
    input_bg: str
    accent: str
    blue: str
    blue_strong: str
    blue_text: str
    border: str
    on_accent: str = "#ffffff"
    card_bg: str = "#ffffff"
    card_shadow: str = "0 1px 3px rgba(58, 40, 73, 0.08)"


# Lavender page + deep plum text (WCAG AA vs grocery-wizard tooling).
MW_THEME = ThemeTokens(
    bg="#e6e0f2",
    text="#3a2849",
    text_muted="#5a4868",
    input_bg="#f8f6fc",
    accent="#6341a5",
    blue="#c8d8f0",
    blue_strong="#7ba3d4",
    blue_text="#1e3d5c",
    border="#a894c8",
    card_bg="#ffffff",
)


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return r, g, b


def _relative_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(foreground: str, background: str) -> float:
    l1 = _relative_luminance(foreground)
    l2 = _relative_luminance(background)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def theme_contrast_pairs(tokens: ThemeTokens = MW_THEME) -> list[tuple[str, str, str]]:
    return [
        ("body text on page", tokens.text, tokens.bg),
        ("body text on cards", tokens.text, tokens.card_bg),
        ("body text on inputs", tokens.text, tokens.input_bg),
        ("muted text on page", tokens.text_muted, tokens.bg),
        ("primary button", tokens.on_accent, tokens.accent),
        ("secondary button", tokens.text, tokens.input_bg),
        ("overdue badge", "#ffffff", "#b71c3a"),
    ]


def assert_theme_contrast_aa(
    tokens: ThemeTokens = MW_THEME,
    *,
    minimum: float = MIN_CONTRAST_RATIO_AA,
) -> None:
    for label, fg, bg in theme_contrast_pairs(tokens):
        ratio = contrast_ratio(fg, bg)
        if ratio < minimum:
            msg = f"{label}: contrast {ratio:.2f} < {minimum} ({fg} on {bg})"
            raise AssertionError(msg)


def app_theme_css(tokens: ThemeTokens = MW_THEME) -> str:
    if tokens is MW_THEME and APP_THEME_STATIC_CSS.is_file():
        css = APP_THEME_STATIC_CSS.read_text(encoding="utf-8")
        return f"<style>\n{css}\n</style>"

    t = tokens
    border = t.border
    return f"""<style>
:root {{
    --mw-bg: {t.bg};
    --mw-text: {t.text};
    --mw-text-muted: {t.text_muted};
    --mw-input-bg: {t.input_bg};
    --mw-accent: {t.accent};
    --mw-blue: {t.blue};
    --mw-blue-strong: {t.blue_strong};
    --mw-blue-text: {t.blue_text};
    --mw-card-bg: {t.card_bg};
    --mw-border: {border};
}}

html {{ color-scheme: light; }}

.stApp {{
    background-color: var(--mw-bg);
    color: var(--mw-text);
}}

[data-testid="stSidebar"] {{
    background-color: var(--mw-input-bg);
    border-right: 1px solid var(--mw-border);
}}

.stApp h1, .stApp h2, .stApp h3, .stApp label,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stWidgetLabel"] p {{
    color: var(--mw-text);
}}

.stApp .stCaption, .stApp small,
.stApp [data-testid="stCaptionContainer"] {{
    color: var(--mw-text-muted);
}}

[data-testid="stMetric"] {{
    background: var(--mw-card-bg);
    border: 1px solid var(--mw-border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    box-shadow: {t.card_shadow};
}}

[data-testid="stMetricLabel"] {{
    color: var(--mw-text-muted) !important;
}}

[data-testid="stMetricValue"] {{
    color: var(--mw-text) !important;
}}

[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputContainer"],
[data-testid="stMultiSelect"] div:has([data-testid="stMultiSelectTagsContainer"]),
[data-testid="stSelectbox"] div:has(button[aria-label="Open"]) {{
    background-color: var(--mw-input-bg) !important;
    border-color: var(--mw-border) !important;
    color: var(--mw-text) !important;
}}

.stButton button[kind="primary"],
.stButton button[data-testid^="stBaseButton-primary"] {{
    background-color: var(--mw-accent) !important;
    border-color: var(--mw-accent) !important;
    color: {t.on_accent} !important;
    font-weight: 600;
    border-radius: 8px !important;
}}

.stButton button[kind="secondary"],
.stButton button[data-testid^="stBaseButton-secondary"] {{
    background-color: var(--mw-input-bg) !important;
    border: 1px solid var(--mw-border) !important;
    color: var(--mw-text) !important;
    border-radius: 8px !important;
}}

.stButton button[kind="primary"] *,
.stButton button[kind="secondary"] * {{
    color: inherit !important;
}}

.block-container {{
    max-width: 42rem;
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

#MainMenu, footer, [data-testid="stToolbar"] {{
    visibility: hidden;
    height: 0;
}}
</style>"""