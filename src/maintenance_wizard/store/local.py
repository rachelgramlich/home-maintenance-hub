from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from maintenance_wizard.models import (
    Completion,
    CompletionStatus,
    Contractor,
    Template,
    parse_links_json,
)
from maintenance_wizard.store.base import TaskStore


def _parse_templates(raw: list[dict]) -> list[Template]:
    return [
        Template(
            task_id=str(row["task_id"]),
            name=str(row["name"]),
            due_month=int(row.get("due_month", 1)),
            area=str(row.get("area", "Other")),
            cadence=row.get("cadence", "annual"),  # type: ignore[arg-type]
            active=bool(row.get("active", True)),
            month_name=str(row.get("month_name", "")),
            task_type=str(row.get("task_type", "")),
            effort=str(row.get("effort", "")),
            priority=row.get("priority", "Medium"),  # type: ignore[arg-type]
            season=str(row.get("season", "")),
            instructions=str(row.get("instructions", "")),
            links=parse_links_json(str(row.get("links_json", ""))),
            contractor_id=row.get("contractor_id"),
            stable_key=str(row.get("stable_key", "")),
        )
        for row in raw
    ]


def _parse_completions(raw: list[dict]) -> list[Completion]:
    out: list[Completion] = []
    for row in raw:
        completed = row.get("completed_on")
        completed_on = None
        if completed:
            if isinstance(completed, str):
                completed_on = date.fromisoformat(completed[:10])
            elif isinstance(completed, date):
                completed_on = completed
        out.append(
            Completion(
                completion_id=str(row.get("completion_id", uuid.uuid4().hex[:12])),
                task_id=str(row["task_id"]),
                period=str(row["period"]),
                status=row["status"],
                completed_on=completed_on,
                notes=str(row.get("notes", "")),
            )
        )
    return out


class LocalTaskStore(TaskStore):
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict:
        if not self._path.exists():
            return {"templates": [], "completions": [], "contractors": []}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def list_templates(self) -> list[Template]:
        return _parse_templates(self._load().get("templates", []))

    def list_completions(self) -> list[Completion]:
        return _parse_completions(self._load().get("completions", []))

    def upsert_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date | None,
        notes: str,
    ) -> Completion:
        data = self._load()
        completions = _parse_completions(data.get("completions", []))
        for i, existing in enumerate(completions):
            if existing.task_id == task_id and existing.period == period:
                updated = Completion(
                    completion_id=existing.completion_id,
                    task_id=task_id,
                    period=period,
                    status=status,
                    completed_on=completed_on,
                    notes=notes,
                )
                completions[i] = updated
                data["completions"] = [
                    {
                        "completion_id": c.completion_id,
                        "task_id": c.task_id,
                        "period": c.period,
                        "status": c.status,
                        "completed_on": c.completed_on.isoformat() if c.completed_on else None,
                        "notes": c.notes,
                    }
                    for c in completions
                ]
                self._save(data)
                return updated

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
                "completed_on": c.completed_on.isoformat() if c.completed_on else None,
                "notes": c.notes,
            }
            for c in completions
        ]
        self._save(data)
        return row

    def list_contractors(self, *, active_only: bool = True) -> list[Contractor]:
        data = self._load()
        rows = [
            Contractor(
                contractor_id=str(r["contractor_id"]),
                name=str(r["name"]),
                trade=str(r.get("trade", "")),
                phone=str(r.get("phone", "")),
                email=str(r.get("email", "")),
                website=str(r.get("website", "")),
                notes=str(r.get("notes", "")),
                active=bool(r.get("active", True)),
            )
            for r in data.get("contractors", [])
        ]
        if active_only:
            rows = [c for c in rows if c.active]
        return rows

    def upsert_contractor(self, contractor: Contractor) -> Contractor:
        data = self._load()
        raw = data.get("contractors", [])
        row = {
            "contractor_id": contractor.contractor_id or uuid.uuid4().hex[:12],
            "name": contractor.name,
            "trade": contractor.trade,
            "phone": contractor.phone,
            "email": contractor.email,
            "website": contractor.website,
            "notes": contractor.notes,
            "active": contractor.active,
        }
        if contractor.contractor_id:
            replaced = False
            for i, existing in enumerate(raw):
                if str(existing.get("contractor_id")) == contractor.contractor_id:
                    raw[i] = row
                    replaced = True
                    break
            if not replaced:
                raw.append(row)
        else:
            raw.append(row)
        data["contractors"] = raw
        self._save(data)
        return Contractor(
            contractor_id=str(row["contractor_id"]),
            name=row["name"],
            trade=row["trade"],
            phone=row["phone"],
            email=row["email"],
            website=row["website"],
            notes=row["notes"],
            active=row["active"],
        )

    def update_task(self, template: Template) -> Template:
        data = self._load()
        templates = _parse_templates(data.get("templates", []))
        updated = template
        out_raw: list[dict] = []
        for t in templates:
            if t.task_id == template.task_id:
                updated = template
            rec = {
                "task_id": t.task_id,
                "name": t.name,
                "due_month": t.due_month,
                "area": t.area,
                "cadence": t.cadence,
                "active": t.active,
                "month_name": t.month_name,
                "task_type": t.task_type,
                "effort": t.effort,
                "priority": t.priority,
                "season": t.season,
                "instructions": t.instructions,
                "links_json": "",
                "contractor_id": t.contractor_id,
                "stable_key": t.stable_key,
            }
            if t.task_id == template.task_id:
                rec = {
                    **rec,
                    "name": template.name,
                    "area": template.area,
                    "priority": template.priority,
                    "instructions": template.instructions,
                    "contractor_id": template.contractor_id,
                    "task_type": template.task_type,
                    "effort": template.effort,
                    "season": template.season,
                }
            out_raw.append(rec)
        data["templates"] = out_raw
        self._save(data)
        return updated
