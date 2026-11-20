from __future__ import annotations

import re

_TRAILING_SEASON_PAREN = re.compile(
    r"\s*\((?:fall|spring|summer|winter|mid[\s-]?summer)\)\s*$",
    re.IGNORECASE,
)


def strip_seasonal_parens(name: str) -> str:
    """Remove redundant trailing season parentheticals from a task title."""
    return _TRAILING_SEASON_PAREN.sub("", name.strip())
