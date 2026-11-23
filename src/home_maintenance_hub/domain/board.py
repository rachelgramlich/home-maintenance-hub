from __future__ import annotations

from datetime import date

from home_maintenance_hub.domain import schedule
from home_maintenance_hub.models import BoardTask, Completion, Template, Urgency

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def last_done(completions: list[Completion], task_id: str) -> tuple[date | None, str]:
    done_rows = [c for c in completions if c.task_id == task_id and c.status == "done"]
    if not done_rows:
        return None, ""
    latest = max(
        done_rows,
        key=lambda c: (c.completed_on or date.min, c.period),
    )
    return latest.completed_on, latest.notes


def build_month_board(
    templates: list[Template],
    completions: list[Completion],
    year: int,
    month: int,
    today: date,
) -> list[BoardTask]:
    rows: list[BoardTask] = []
    for template in templates:
        if not schedule.task_applies_to_board(template, year, month, completions):
            continue
        period = schedule.board_period_for_task(template, year, month)
        row = schedule.completion_for_period(completions, template.task_id, period)
        if row and schedule.is_terminal_status(row.status):
            urgency = Urgency.DONE if row.status == "done" else Urgency.WONT_DO
            completion_notes = row.notes
        elif row and row.status == "in_progress":
            urgency = Urgency.IN_PROGRESS
            completion_notes = row.notes
        elif schedule.is_overdue(template, year, month, today, completions):
            urgency = Urgency.OVERDUE
            completion_notes = row.notes if row else ""
        else:
            urgency = Urgency.NORMAL
            completion_notes = row.notes if row else ""

        last_on, last_notes = last_done(completions, template.task_id)
        rows.append(
            BoardTask(
                template=template,
                period=period,
                urgency=urgency,
                last_done_on=last_on,
                last_done_notes=last_notes,
                completion_notes=completion_notes,
            )
        )

    order = {
        Urgency.OVERDUE: 0,
        Urgency.IN_PROGRESS: 1,
        Urgency.NORMAL: 2,
        Urgency.DONE: 3,
        Urgency.WONT_DO: 4,
    }
    rows.sort(
        key=lambda r: (
            order[r.urgency],
            PRIORITY_ORDER.get(r.template.priority, 1),
            r.template.area,
            r.template.name,
        )
    )
    return rows
