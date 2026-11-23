from __future__ import annotations

from home_maintenance_hub.migration.names import normalize_task_title


def display_task_name(name: str) -> str:
    """Strip redundant season parens and month suffixes for UI labels."""
    return normalize_task_title(name)
