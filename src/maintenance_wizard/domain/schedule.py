from __future__ import annotations

from datetime import date

from maintenance_wizard.models import Completion, Template

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


def period_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def completion_for_period(
    completions: list[Completion], task_id: str, period: str
) -> Completion | None:
    for row in completions:
        if row.task_id == task_id and row.period == period:
            return row
    return None


def terminal_completion_exists(
    completions: list[Completion], task_id: str, period: str
) -> bool:
    row = completion_for_period(completions, task_id, period)
    return row is not None


def monthly_task_period(template: Template, year: int, month: int) -> str:
    """Monthly tasks use the viewing month as the period key."""
    return period_key(year, month)


def annual_task_period(template: Template, year: int) -> str:
    return f"{year:04d}-{template.due_month:02d}"


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
  # annual
    if month == template.due_month:
        return True
    if month > template.due_month:
        p = annual_task_period(template, year)
        return not terminal_completion_exists(completions, template.task_id, p)
    return False


def board_period_for_task(template: Template, year: int, month: int) -> str:
    if template.cadence == "monthly":
        return monthly_task_period(template, year, month)
    return annual_task_period(template, year)


def is_overdue(
    template: Template,
    year: int,
    month: int,
    today: date,
    completions: list[Completion],
) -> bool:
    current_period = board_period_for_task(template, year, month)
    if terminal_completion_exists(completions, template.task_id, current_period):
        return False

    if template.cadence == "monthly":
        if (today.year, today.month) > (year, month):
            return True
        prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
        prior = period_key(prev_year, prev_month)
        return prior < current_period and not terminal_completion_exists(
            completions, template.task_id, prior
        )

    # annual: overdue only after the due month, until completed
    return (year, month) > (year, template.due_month)