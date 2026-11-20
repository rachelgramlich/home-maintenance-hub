from __future__ import annotations

import re

_TRAILING_SEASON_PAREN = re.compile(
    r"\s*\((?:fall|spring|summer|winter|mid-summer)\)\s*$",
    re.IGNORECASE,
)


def display_task_name(name: str) -> str:
    """Strip redundant trailing season parentheticals for UI labels only."""
    return _TRAILING_SEASON_PAREN.sub("", name.strip())
