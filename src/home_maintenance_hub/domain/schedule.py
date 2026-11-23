from __future__ import annotations

from datetime import date

from home_maintenance_hub.models import Completion, Template

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

MONTH_LABELS = {v: k.capitalize() for k, v in MONTH_NAMES.items()}

MONTH_SHORT = {v: name[:3].title() for name, v in MONTH_NAMES.items()}

COMPLETION_STATUS_LABELS: dict[str, str] = {
    "done": "Done",
    "wont_do": "Won't do",
    "in_progress": "In progress",
}


def period_short_label(period: str) -> str:
    """Turn ``YYYY-MM`` into a compact month label such as ``Jun 2026``."""
    try:
        year_s, month_s = period.split("-", 1)
        month = int(month_s)
    except (ValueError, IndexError):
        return period
    mon = MONTH_SHORT.get(month, month_s)
    return f"{mon} {year_s}"


def completion_page_title(*, task_name: str, period: str, status: str) -> str:
    """Human-readable Notion completion row title."""
    label = COMPLETION_STATUS_LABELS.get(status, status.replace("_", " ").title())
    return f"{label} · {task_name} · {period_short_label(period)}"


def period_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def completion_for_period(
    completions: list[Completion], task_id: str, period: str
) -> Completion | None:
    for row in completions:
        if row.task_id == task_id and row.period == period:
            return row
    return None


def is_terminal_status(status: str) -> bool:
    return status in ("done", "wont_do")


def terminal_completion_exists(completions: list[Completion], task_id: str, period: str) -> bool:
    row = completion_for_period(completions, task_id, period)
    return row is not None and is_terminal_status(row.status)


def task_applies_to_board(
    template: Template,
    year: int,
    month: int,
    completions: list[Completion],
) -> bool:
    if not template.active:
        return False
    if template.cadence == "monthly":
        return True
    if template.due_month == month:
        return True
    if template.due_month < month:
        p = template.period_key(year)
        return not terminal_completion_exists(completions, template.task_id, p)
    return False


def board_period_for_task(template: Template, year: int, month: int) -> str:
    if template.cadence == "monthly":
        return template.period_key(year, board_month=month)
    return template.period_key(year)


def is_overdue(
    template: Template,
    year: int,
    month: int,
    _today: date,
    completions: list[Completion],
) -> bool:
    if template.cadence == "monthly":
        return False
    period = template.period_key(year)
    row = completion_for_period(completions, template.task_id, period)
    if row and is_terminal_status(row.status):
        return False
    return month > template.due_month
