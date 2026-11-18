from __future__ import annotations

from datetime import date

from maintenance_wizard.domain import schedule
from maintenance_wizard.models import BoardTask, Completion, Template, Urgency


def last_done(
    completions: list[Completion], task_id: str
) -> tuple[date | None, str]:
    done_rows = [c for c in completions if c.task_id == task_id and c.status == "done"]
    if not done_rows:
        return None, ""
    latest = max(done_rows, key=lambda c: c.completed_on)
    return latest.completed_on, latest.notes


def build_month_board(
    templates: list[Template],
    completions: list[Completion],
    year: int,
    month: int,
    today: date,
    due_soon_days: int,
) -> list[BoardTask]:
    rows: list[BoardTask] = []
    for template in templates:
        if not schedule.task_applies_to_board(template, year, month, completions):
            continue
        period = schedule.board_period_for_task(template, year, month)
        term = schedule.terminal_completion_exists(completions, template.task_id, period)
        if term:
            row = schedule.completion_for_period(completions, template.task_id, period)
            assert row is not None
            urgency = Urgency.DONE if row.status == "done" else Urgency.WONT_DO
        elif schedule.is_overdue(template, year, month, today, completions):
            urgency = Urgency.OVERDUE
        elif schedule.is_due_soon(template, year, month, today, due_soon_days):
            urgency = Urgency.DUE_SOON
        else:
            urgency = Urgency.NORMAL
        last_on, last_notes = last_done(completions, template.task_id)
        rows.append(
            BoardTask(
                template=template,
                period=period,
                urgency=urgency,
                last_done_on=last_on,
                last_done_notes=last_notes,
            )
        )

    order = {
        Urgency.OVERDUE: 0,
        Urgency.DUE_SOON: 1,
        Urgency.NORMAL: 2,
        Urgency.DONE: 3,
        Urgency.WONT_DO: 4,
    }
    rows.sort(key=lambda r: (order[r.urgency], r.template.area, r.template.name))
    return rows