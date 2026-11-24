"""Compare Notion Cadence property vs values loaded into the app for every task."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_template

DEFAULT_REPORT = Path("/opt/cursor/artifacts/cadence-audit.json")


def _notion_cadence_label(props: dict) -> str:
    return nc.select_name(props.get("Cadence")) or "(empty)"


def _expected_from_notion(props: dict, stable: str) -> str:
    label = nc.select_name(props.get("Cadence"))
    if label:
        return "monthly" if label.lower().startswith("month") else "annual"
    if stable.endswith("|monthly"):
        return "monthly"
    return "annual"


def audit(*, report_path: Path) -> dict:
    settings = get_settings()
    if not settings.notion_api_key:
        raise SystemExit("NOTION_API_KEY missing")
    if not settings.notion_tasks_ds_id:
        raise SystemExit("HOME_MAINTENANCE_NOTION_TASKS_DS_ID missing")

    client = nc.make_client(settings.notion_api_key)
    pages = nc.paginate_data_source(client, settings.notion_tasks_ds_id)
    rows: list[dict] = []
    mismatches: list[dict] = []
    stable_drifts: list[dict] = []

    for page in pages:
        props = page.get("properties") or {}
        stable = nc.plain_text(props.get("Stable key"))
        notion_label = _notion_cadence_label(props)
        expected = _expected_from_notion(props, stable)
        template = page_to_template(page)
        row = {
            "name": template.name,
            "active": template.active,
            "notion_cadence": notion_label,
            "expected_cadence": expected,
            "ui_cadence": template.cadence,
            "stable_key": stable,
            "task_id": template.task_id,
        }
        rows.append(row)
        if expected != template.cadence:
            mismatches.append(row)
        if notion_label != "(empty)":
            notion_norm = "monthly" if notion_label.lower().startswith("month") else "annual"
            if stable.endswith("|monthly") and notion_norm != "monthly":
                stable_drifts.append(row)
            if notion_norm == "monthly" and not stable.endswith("|monthly"):
                stable_drifts.append(row)

    summary = {
        "tasks_total": len(rows),
        "mismatches": len(mismatches),
        "stable_key_drifts": len(stable_drifts),
        "active_monthly": sum(1 for r in rows if r["active"] and r["ui_cadence"] == "monthly"),
        "active_annual": sum(1 for r in rows if r["active"] and r["ui_cadence"] == "annual"),
    }
    report = {
        "summary": summary,
        "mismatches": mismatches,
        "stable_key_drifts": stable_drifts,
        "tasks": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    report = audit(report_path=args.report)
    s = report["summary"]
    print(
        f"Tasks: {s['tasks_total']} | active monthly {s['active_monthly']} | "
        f"active annual {s['active_annual']}"
    )
    print(f"Cadence mismatches (Notion vs UI): {s['mismatches']}")
    print(f"Stable key drifts: {s['stable_key_drifts']}")
    print(f"Wrote {args.report}")
    return 1 if s["mismatches"] or s["stable_key_drifts"] else 0


if __name__ == "__main__":
    sys.exit(main())
