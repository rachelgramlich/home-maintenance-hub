"""Import completion rows from screenshot-verified checklist checks."""

from __future__ import annotations

import argparse
import calendar
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from maintenance_wizard.config import get_settings
from maintenance_wizard.integrations.notion import client as nc
from maintenance_wizard.integrations.notion.mappers import page_to_completion, page_to_template
from maintenance_wizard.migration.cadence import (
    canonical_group_key,
    monthly_stable_key,
    strip_month_suffix,
)
from maintenance_wizard.migration.keys import map_area, month_number, stable_key
from maintenance_wizard.models import Template
from maintenance_wizard.store.notion import NotionTaskStore

SCREENSHOT_NOTES = "Imported from checklist screenshot"
DEFAULT_YEAR = 2026
LOG_PATH = Path("/opt/cursor/artifacts/completions-import-2026.log")
_FIXTURE = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "screenshot_completions.json"
)

# Verified from user screenshots (2026 checklist).
CHECKED: tuple[tuple[str, str, str], ...] = (
    ("Replace HVAC filter — June", "HVAC", "June"),
    ("Replace HVAC filter — July", "HVAC", "July"),
    ("Replace HVAC filter — August", "HVAC", "August"),
    ("Replace HVAC filter — September", "HVAC", "September"),
    ("Replace HVAC filter — October", "HVAC", "October"),
    ("Replace HVAC filter — November", "HVAC", "November"),
    ("Pest: Summer pest inspection", "Pest", "June"),
    ("Exterior: Trim vegetation away from house (mid-summer)", "Exterior", "July"),
    ("Exterior: Clean + inspect outdoor furniture/patio", "Exterior", "August"),
    ("Basement: Shut off + store dehumidifier for winter", "Basement/Humidity", "September"),
    ("Plumbing: Winterize outdoor hose bibs (before first frost)", "Plumbing", "October"),
    ("Interior: Inspect + seal drafts around doors/windows (fall)", "Interior", "October"),
)


@dataclass(frozen=True)
class CompletionSpec:
    task: str
    area: str
    month: str

    @property
    def month_num(self) -> int:
        return month_number(self.month)

    def period(self, year: int) -> str:
        return f"{year:04d}-{self.month_num:02d}"

    def completed_on(self, year: int) -> date:
        _, last = calendar.monthrange(year, self.month_num)
        return date(year, self.month_num, last)


def export_fixture(year: int) -> None:
    specs = [CompletionSpec(t, a, m) for t, a, m in CHECKED]
    payload: dict[str, Any] = {
        "year": year,
        "checks": [
            {
                "task": s.task,
                "area": s.area,
                "month": s.month,
                "period": s.period(year),
                "completed_on": s.completed_on(year).isoformat(),
            }
            for s in specs
        ],
    }
    _FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    _FIXTURE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def last_day_of_month(year: int, month: int) -> date:
    _, last = calendar.monthrange(year, month)
    return date(year, month, last)


TaskIndexes = tuple[dict[str, str], dict[str, str], dict[str, Template]]


def build_task_indexes(store: NotionTaskStore) -> TaskIndexes:
    """stable_key / monthly_stable_key / canonical_group_key -> task_id."""
    pages = nc.paginate_data_source(store._client, store._settings.notion_tasks_ds_id)
    by_slot: dict[str, str] = {}
    by_monthly: dict[str, str] = {}
    by_canonical: dict[str, Template] = {}
    for page in pages:
        tmpl = page_to_template(page)
        if tmpl.stable_key and "|" in tmpl.stable_key:
            by_slot[tmpl.stable_key] = tmpl.task_id
        month_name = tmpl.month_name or ""
        if month_name:
            sk = stable_key(tmpl.name, tmpl.area, month_name)
            by_slot[sk] = tmpl.task_id
        base = strip_month_suffix(tmpl.name)
        msk = monthly_stable_key(base, tmpl.area)
        stable = tmpl.stable_key or ""
        if (tmpl.cadence == "monthly" or stable.endswith("|monthly")) and tmpl.active:
            by_monthly[msk] = tmpl.task_id
        cg = canonical_group_key(tmpl.name, tmpl.area)
        by_canonical[cg] = tmpl
    return by_slot, by_monthly, by_canonical


def resolve_task_id(
    spec: CompletionSpec,
    *,
    by_slot: dict[str, str],
    by_monthly: dict[str, str],
    by_canonical: dict[str, Template],
) -> str | None:
    area = map_area(spec.area)
    msk = monthly_stable_key(strip_month_suffix(spec.task), area)
    if msk in by_monthly:
        return by_monthly[msk]
    for area_variant in (spec.area, area):
        slot = stable_key(spec.task, area_variant, spec.month)
        if slot in by_slot:
            return by_slot[slot]
    cg = canonical_group_key(spec.task, spec.area)
    tmpl = by_canonical.get(cg)
    if tmpl and tmpl.cadence == "monthly":
        return tmpl.task_id
    return None


def is_screenshot_import(notes: str) -> bool:
    return SCREENSHOT_NOTES.lower() in (notes or "").lower()


def purge_wrong_year_screenshot_rows(
    store: NotionTaskStore,
    *,
    year: int,
    dry_run: bool,
) -> tuple[int, list[str]]:
    """Archive completion rows from prior screenshot imports for a different calendar year."""
    lines: list[str] = []
    archived = 0
    prefix = f"{year:04d}-"
    pages = nc.paginate_data_source(store._client, store._settings.notion_completions_ds_id)
    for page in pages:
        comp = page_to_completion(page)
        if not is_screenshot_import(comp.notes):
            continue
        if comp.period and comp.period.startswith(prefix):
            continue
        page_id = str(page["id"])
        if dry_run:
            lines.append(f"PURGE dry_run {comp.period} {page_id[:8]}…")
            archived += 1
            continue
        store._client.pages.update(page_id=page_id, archived=True)
        lines.append(f"PURGED {comp.period} {page_id}")
        archived += 1
    return archived, lines


def run_import(*, dry_run: bool, year: int, purge_legacy: bool) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY missing")
        return {"error": 1}

    store = NotionTaskStore(settings)
    by_slot, by_monthly, by_canonical = build_task_indexes(store)
    specs = [CompletionSpec(t, a, m) for t, a, m in CHECKED]

    stats: dict[str, int] = {
        "purged_wrong_year": 0,
        "created_or_updated": 0,
        "skipped_no_task": 0,
        "errors": 0,
    }
    lines: list[str] = [f"import_completions year={year} dry_run={dry_run}", "---"]

    if purge_legacy:
        purged, purge_lines = purge_wrong_year_screenshot_rows(store, year=year, dry_run=dry_run)
        stats["purged_wrong_year"] = purged
        lines.extend(purge_lines)
        if purge_lines:
            lines.append("---")

    for spec in specs:
        task_id = resolve_task_id(
            spec,
            by_slot=by_slot,
            by_monthly=by_monthly,
            by_canonical=by_canonical,
        )
        period = spec.period(year)
        completed_on = spec.completed_on(year)
        if not task_id:
            stats["skipped_no_task"] += 1
            lines.append(f"SKIP no task: {spec.task!r} {spec.month} ({period})")
            continue
        if dry_run:
            stats["created_or_updated"] += 1
            short = task_id[:8]
            lines.append(f"UPSERT done {period} @ {completed_on} task={short}… {spec.task[:50]}")
            continue
        try:
            store.upsert_completion(
                task_id,
                period,
                "done",
                completed_on,
                notes=SCREENSHOT_NOTES,
            )
            stats["created_or_updated"] += 1
            lines.append(f"OK {period} @ {completed_on} task={task_id} {spec.task}")
        except Exception as exc:
            stats["errors"] += 1
            lines.append(f"ERR {spec.task} {period}: {exc}")

    lines.append("---")
    lines.append(str(stats))
    if not dry_run and stats.get("errors", 0) == 0:
        try:
            from maintenance_wizard.scripts.notion_row_audit import audit_row_counts, format_audit

            after = format_audit(audit_row_counts())
            lines.append("--- after audit ---")
            lines.append(after)
            print(after)
        except Exception as exc:
            lines.append(f"after audit skipped: {exc}")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    export_fixture(year)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import completions from verified checklist")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument(
        "--no-purge-legacy",
        action="store_true",
        help="Do not archive screenshot imports for other years before upserting",
    )
    args = parser.parse_args(argv)
    stats = run_import(
        dry_run=args.dry_run,
        year=args.year,
        purge_legacy=not args.no_purge_legacy,
    )
    if stats.get("error"):
        return 1
    if stats.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
