from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from maintenance_wizard.models import Completion, CompletionStatus, Template
from maintenance_wizard.store.base import TaskStore


def _parse_templates(raw: list[dict]) -> list[Template]:
    out: list[Template] = []
    for row in raw:
        out.append(
            Template(
                task_id=str(row["task_id"]),
                name=str(row["name"]),
                cadence=row["cadence"],
                due_month=int(row.get("due_month", 1)),
                due_day=int(row.get("due_day", 1)),
                area=str(row.get("area", "Other")),
                active=bool(row.get("active", True)),
            )
        )
    return out


def _parse_completions(raw: list[dict]) -> list[Completion]:
    out: list[Completion] = []
    for row in raw:
        completed = row["completed_on"]
        if isinstance(completed, str):
            completed = date.fromisoformat(completed[:10])
        out.append(
            Completion(
                completion_id=str(row.get("completion_id", uuid.uuid4().hex[:12])),
                task_id=str(row["task_id"]),
                period=str(row["period"]),
                status=row["status"],
                completed_on=completed,
                notes=str(row.get("notes", "")),
            )
        )
    return out


class LocalTaskStore(TaskStore):
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict:
        if not self._path.exists():
            return {"templates": [], "completions": []}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def list_templates(self) -> list[Template]:
        return _parse_templates(self._load().get("templates", []))

    def list_completions(self) -> list[Completion]:
        return _parse_completions(self._load().get("completions", []))

    def add_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date,
        notes: str,
    ) -> Completion:
        data = self._load()
        completions = _parse_completions(data.get("completions", []))
        for existing in completions:
            if existing.task_id == task_id and existing.period == period:
                msg = f"Completion already exists for {task_id} in {period}."
                raise ValueError(msg)
        row = Completion(
            completion_id=uuid.uuid4().hex[:12],
            task_id=task_id,
            period=period,
            status=status,
            completed_on=completed_on,
            notes=notes,
        )
        completions.append(row)
        data["completions"] = [
            {
                "completion_id": c.completion_id,
                "task_id": c.task_id,
                "period": c.period,
                "status": c.status,
                "completed_on": c.completed_on.isoformat(),
                "notes": c.notes,
            }
            for c in completions
        ]
        self._save(data)
        return row