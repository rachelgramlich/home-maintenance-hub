from __future__ import annotations

from maintenance_wizard.migration.names import strip_seasonal_parens


def display_task_name(name: str) -> str:
    """Task title for UI; mirrors stored names after seasonal cleanup."""
    return strip_seasonal_parens(name)
