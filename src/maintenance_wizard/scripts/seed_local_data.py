"""Seed demo templates for local development."""

from __future__ import annotations

import json

from maintenance_wizard.config import get_settings

SAMPLE = {
    "templates": [
        {
            "task_id": "hvac-filter-mar",
            "name": "Replace HVAC filter — March",
            "due_month": 3,
            "area": "HVAC",
            "month_name": "March",
            "task_type": "Replace",
            "effort": "XS",
            "priority": "High",
            "active": True,
            "stable_key": "replace hvac filter — march|hvac|march",
        },
        {
            "task_id": "hvac-service-heat",
            "name": "Service heating (fall)",
            "due_month": 10,
            "area": "HVAC",
            "month_name": "October",
            "task_type": "Service",
            "effort": "M",
            "priority": "High",
            "active": True,
        },
        {
            "task_id": "gfci-april",
            "name": "Electrical: Test GFCI outlets",
            "due_month": 4,
            "area": "Electrical",
            "month_name": "April",
            "task_type": "Inspect/Test",
            "effort": "XS",
            "priority": "High",
            "active": True,
        },
        {
            "task_id": "dryer-vent",
            "name": "Laundry: Professional dryer vent cleaning",
            "due_month": 3,
            "area": "Laundry",
            "month_name": "March",
            "task_type": "Service",
            "effort": "S",
            "priority": "High",
            "active": True,
        },
    ],
    "completions": [
        {
            "completion_id": "c1",
            "task_id": "gfci-april",
            "period": "2026-04",
            "status": "done",
            "completed_on": "2026-04-30",
            "notes": "All bathrooms OK",
        }
    ],
    "contractors": [],
}


def main() -> None:
    path = get_settings().local_data_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(SAMPLE, indent=2), encoding="utf-8")
    print(f"Wrote sample data to {path}")


if __name__ == "__main__":
    main()
