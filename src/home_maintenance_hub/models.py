from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Literal

CompletionStatus = Literal["in_progress", "done", "wont_do"]
Cadence = Literal["monthly", "annual"]
Priority = Literal["High", "Medium", "Low"]


class Urgency(StrEnum):
    OVERDUE = "overdue"
    IN_PROGRESS = "in_progress"
    NORMAL = "normal"
    DONE = "done"
    WONT_DO = "wont_do"


@dataclass(frozen=True)
class Template:
    """Task template: annual (one board month per year) or monthly (every month)."""

    task_id: str
    name: str
    due_month: int  # annual: assigned month; monthly: anchor month (1) for sorting
    area: str
    cadence: Cadence = "annual"
    active: bool = True
    month_name: str = ""
    task_type: str = ""
    effort: str = ""
    priority: Priority = "Medium"
    season: str = ""
    instructions: str = ""
    contractor_id: str | None = None
    stable_key: str = ""
    notion_url: str = ""

    def period_key(self, year: int, *, board_month: int | None = None) -> str:
        if self.cadence == "monthly" and board_month is not None:
            month = board_month
        else:
            month = self.due_month
        return f"{year:04d}-{month:02d}"


@dataclass(frozen=True)
class Contractor:
    contractor_id: str
    name: str
    trade: str
    phone: str = ""
    email: str = ""
    website: str = ""
    notes: str = ""
    active: bool = True
    notion_url: str = ""
    linked_task_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Completion:
    completion_id: str
    task_id: str
    period: str  # YYYY-MM
    status: CompletionStatus
    completed_on: date | None
    notes: str = ""
    notion_url: str = ""


@dataclass(frozen=True)
class BoardTask:
    template: Template
    period: str
    urgency: Urgency
    last_done_on: date | None
    last_done_notes: str
    completion_notes: str = ""
