"""Seed demo templates for local development."""

from __future__ import annotations

import json

from maintenance_wizard.config import get_settings

SAMPLE = {
    "templates": [
        {
            "task_id": "hvac-filter",
            "name": "Replace HVAC return filter",
            "cadence": "monthly",
            "due_month": 1,
            "due_day": 15,
            "area": "HVAC",
            "active": True,
        },
        {
            "task_id": "hvac-service-heat",
            "name": "Service heating (fall)",
            "cadence": "annual",
            "due_month": 10,
            "due_day": 15,
            "area": "HVAC",
            "active": True,
        },
        {
            "task_id": "gfci-test",
            "name": "Test GFCI outlets",
            "cadence": "monthly",
            "due_month": 1,
            "due_day": 1,
            "area": "Electrical",
            "active": True,
        },
        {
            "task_id": "dryer-vent",
            "name": "Clean dryer lint trap & check vent",
            "cadence": "monthly",
            "due_month": 1,
            "due_day": 28,
            "area": "Laundry",
            "active": True,
        },
    ],
    "completions": [
        {
            "completion_id": "c1",
            "task_id": "gfci-test",
            "period": "2026-02",
            "status": "done",
            "completed_on": "2026-02-10",
            "notes": "All bathrooms OK",
        }
    ],
}


def main() -> None:
    path = get_settings().local_data_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(SAMPLE, indent=2), encoding="utf-8")
    print(f"Wrote sample data to {path}")


if __name__ == "__main__":
    main()