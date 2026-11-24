"""Normalize maintenance task Instructions text (migration / Notion cleanup)."""

from __future__ import annotations

import re

_SOURCE_PREFIXES = (
    r"^From home inspection:\s*",
    r"^From example checklist:\s*",
    r"^From seasonal checklist:\s*",
    r"^Maintenance monitoring item from inspection notes:\s*",
    r"^Annual;\s*from inspection checklist:\s*",
)
_SUFFIX_SEASONAL = re.compile(r"\s*From seasonal checklist\.?\s*$", re.IGNORECASE)

# Entire value is only a generic import note — clear the field.
_GENERIC_BOILERPLATE = frozenset(
    {
        "service heating + a/c units 2x/year (spring + fall).",
        "service heating + a/c units 2x/year (spring + fall)",
        "commonly annual.",
        "commonly annual",
        "commonly annual if used; otherwise per usage.",
        "lawncare.",
        "garbage disposal clean/clear.",
        "basement mold inspection.",
        "test gfci outlets.",
        "clear drain screens.",
        "dishwasher clean/check filters.",
        "washing machine clean/check filter.",
        "microwave inspect filters.",
        "vacuum fridge coils.",
        "pressure dust electronics/pc/ps.",
        "vacuum out return grills.",
        "smoke/co test.",
        "inspect fire extinguishers.",
        "inspect basement plumbing (leaks).",
        "clean outdoor furniture.",
        "clean ceiling fans.",
        "deep clean kitchen.",
        "check window/door drafts.",
        "inspect drafts before winter.",
        "inspect patios/decks.",
        "clear gutters after leaves fall.",
        "power wash walkways.",
        "bathroom re-caulking.",
        "pest inspection (summer).",
        "aerate lawn.",
        "roof inspection.",
        "ongoing prevention; touch up as needed.",
        "debris/leaf litter.",
        "seasonal check, especially after big storms.",
        "annual at first frost (maryland).",
        "annual check; touch up as needed.",
        "use dehumidifier during humid months.",
    }
)


def clean_instruction_text(text: str | None) -> str:
    """Remove import boilerplate; return empty when no actionable steps remain."""
    if not text:
        return ""
    cleaned = text.strip()
    for pattern in _SOURCE_PREFIXES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = _SUFFIX_SEASONAL.sub("", cleaned).strip()
    if cleaned.lower() in _GENERIC_BOILERPLATE:
        return ""
    if cleaned.lower().startswith("from ") and len(cleaned) < 40:
        return ""
    return cleaned
