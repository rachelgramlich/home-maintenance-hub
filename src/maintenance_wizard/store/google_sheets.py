from __future__ import annotations

import uuid
from datetime import date

from maintenance_wizard.models import Completion, CompletionStatus, Template
from maintenance_wizard.store.base import TaskStore

MONTH_NAMES = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def _month_to_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    s = str(value).strip().lower()
    if s.isdigit():
        return int(s)
    return MONTH_NAMES.index(s[:3]) + 1 if s[:3] in [m[:3] for m in MONTH_NAMES] else 1


class GoogleSheetsTaskStore(TaskStore):
    """Read/write templates and completions tabs. Requires gspread + authorized token."""

    def __init__(self, sheet_id: str, token_path: str) -> None:
        import gspread
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(token_path)
        client = gspread.authorize(creds)
        self._sheet = client.open_by_key(sheet_id)
        self._templates_ws = self._sheet.worksheet("templates")
        self._completions_ws = self._sheet.worksheet("completions")

    def list_templates(self) -> list[Template]:
        rows = self._templates_ws.get_all_records()
        out: list[Template] = []
        for row in rows:
            if str(row.get("active", "TRUE")).upper() in ("FALSE", "0", "NO"):
                active = False
            else:
                active = True
            cadence = str(row.get("cadence", "monthly")).lower()
            if cadence not in ("monthly", "annual"):
                cadence = "monthly"
            out.append(
                Template(
                    task_id=str(row["task_id"]),
                    name=str(row["name"]),
                    cadence=cadence,  # type: ignore[arg-type]
                    due_month=_month_to_int(row.get("due_month", 1)),
                    due_day=int(row.get("due_day", 1) or 1),
                    area=str(row.get("area", "Other")),
                    active=active,
                )
            )
        return out

    def list_completions(self) -> list[Completion]:
        rows = self._completions_ws.get_all_records()
        out: list[Completion] = []
        for row in rows:
            if not row.get("task_id"):
                continue
            completed = row.get("completed_on", "")
            if isinstance(completed, str):
                completed = date.fromisoformat(completed[:10])
            status = str(row.get("status", "done")).lower()
            if status not in ("done", "wont_do"):
                continue
            out.append(
                Completion(
                    completion_id=str(row.get("completion_id", uuid.uuid4().hex[:12])),
                    task_id=str(row["task_id"]),
                    period=str(row["period"]),
                    status=status,  # type: ignore[arg-type]
                    completed_on=completed,
                    notes=str(row.get("notes", "")),
                )
            )
        return out

    def add_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date,
        notes: str,
    ) -> Completion:
        row = Completion(
            completion_id=uuid.uuid4().hex[:12],
            task_id=task_id,
            period=period,
            status=status,
            completed_on=completed_on,
            notes=notes,
        )
        self._completions_ws.append_row(
            [
                row.completion_id,
                row.task_id,
                row.period,
                row.status,
                row.completed_on.isoformat(),
                row.notes,
            ],
            value_input_option="USER_ENTERED",
        )
        return row


def ensure_sheet_layout(sheet_id: str, token_path: str) -> None:
    """Create tabs and headers if missing (run once after OAuth)."""
    import gspread
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file(token_path)
    client = gspread.authorize(creds)
    book = client.open_by_key(sheet_id)
    for title, headers in (
        (
            "templates",
            [
                "task_id",
                "name",
                "cadence",
                "due_month",
                "due_day",
                "area",
                "active",
            ],
        ),
        (
            "completions",
            [
                "completion_id",
                "task_id",
                "period",
                "status",
                "completed_on",
                "notes",
            ],
        ),
    ):
        try:
            ws = book.worksheet(title)
        except Exception:
            ws = book.add_worksheet(title=title, rows=500, cols=len(headers))
        if not ws.row_values(1):
            ws.append_row(headers)
