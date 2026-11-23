from __future__ import annotations

import re

from home_maintenance_hub.migration.cadence import strip_month_suffix

_TRAILING_SEASON_PAREN = re.compile(
    r"\s*\((?:fall|spring|summer|winter|mid[\s-]?summer)\)\s*$",
    re.IGNORECASE,
)


def strip_seasonal_parens(name: str) -> str:
    """Remove redundant trailing season parentheticals from a task title."""
    return _TRAILING_SEASON_PAREN.sub("", name.strip())


def normalize_task_title(name: str) -> str:
    """Strip redundant season parens and xlsx-style `` — Month`` suffixes."""
    return strip_month_suffix(strip_seasonal_parens(name))
