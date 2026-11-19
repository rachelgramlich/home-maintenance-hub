from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Literal

Cadence = Literal["monthly", "annual"]
CompletionStatus = Literal["done", "wont_do"]


class Urgency(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    NORMAL = "normal"
    DONE = "done"
    WONT_DO = "wont_do"


@dataclass(frozen=True)
class Template:
    task_id: str
    name: str
    cadence: Cadence
    due_month: int  # 1-12; for monthly, optional anchor; for annual, required
    due_day: int  # 1-28, default 1
    area: str
    active: bool = True

    def period_key(self, year: int) -> str:
        """Canonical completion period for this task in a given year."""
        if self.cadence == "monthly":
            return f"{year:04d}-{self.due_month:02d}" if self.due_month else ""
        return f"{year:04d}-{self.due_month:02d}"


@dataclass(frozen=True)
class Completion:
    completion_id: str
    task_id: str
    period: str  # YYYY-MM
    status: CompletionStatus
    completed_on: date
    notes: str = ""


@dataclass(frozen=True)
class BoardTask:
    template: Template
    period: str  # period we're closing for this month (monthly: YYYY-MM of view month)
    urgency: Urgency
    last_done_on: date | None
    last_done_notes: str
