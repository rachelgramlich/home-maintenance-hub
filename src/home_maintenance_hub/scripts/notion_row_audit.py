"""Audit [MW] Tasks and Completions row counts; optional year correction for completions."""

from __future__ import annotations

import argparse
import calendar
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.domain.schedule import completion_page_title
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_completion, page_to_template

DEFAULT_LOG = Path("/opt/cursor/artifacts/notion-row-audit.log")
EXPECTED_ACTIVE_TASKS = 50
EXPECTED_SCREENSHOT_COMPLETIONS_2026 = 12


def audit_row_counts() -> dict[str, int | dict[str, int]]:
    settings = get_settings()
    if not settings.notion_api_key:
        raise SystemExit("NOTION_API_KEY missing")

    client = nc.make_client(settings.notion_api_key)
    task_pages = nc.paginate_data_source(client, settings.notion_tasks_ds_id)
    templates = [page_to_template(p) for p in task_pages]
    active = sum(1 for t in templates if t.active)
    inactive = len(templates) - active
    monthly_hvac = sum(
        1
        for t in templates
        if t.active and t.cadence == "monthly" and "hvac filter" in t.name.lower()
    )

    completion_pages = nc.paginate_data_source(client, settings.notion_completions_ds_id)
    completions = [page_to_completion(p) for p in completion_pages]
    by_year: Counter[str] = Counter()
    for comp in completions:
        yr = comp.period[:4] if len(comp.period) >= 4 else "unknown"
        by_year[yr] += 1

    pair_counts: Counter[tuple[str, str]] = Counter()
    for comp in completions:
        if comp.task_id and comp.period:
            pair_counts[(comp.task_id, comp.period)] += 1
    duplicate_pairs = sum(1 for _k, v in pair_counts.items() if v > 1)
    duplicate_extra_rows = sum(v - 1 for v in pair_counts.values() if v > 1)

    return {
        "tasks_total": len(templates),
        "tasks_active": active,
        "tasks_inactive": inactive,
        "monthly_hvac_active": monthly_hvac,
        "completions_total": len(completions),
        "completions_by_year": dict(by_year),
        "completion_duplicate_pairs": duplicate_pairs,
        "completion_duplicate_extra_rows": duplicate_extra_rows,
    }


def rewrite_completion_year(*, from_year: int, to_year: int, dry_run: bool) -> dict[str, int]:
    settings = get_settings()
    client = nc.make_client(settings.notion_api_key)
    task_pages = nc.paginate_data_source(client, settings.notion_tasks_ds_id)
    task_names = {page_to_template(p).task_id: page_to_template(p).name for p in task_pages}
    stats = {"updated": 0, "skipped": 0, "errors": 0}
    prefix = f"{from_year:04d}-"

    for page in nc.paginate_data_source(client, settings.notion_completions_ds_id):
        comp = page_to_completion(page)
        if not comp.period.startswith(prefix):
            stats["skipped"] += 1
            continue
        try:
            month = int(comp.period.split("-", 1)[1])
        except (IndexError, ValueError):
            stats["errors"] += 1
            continue
        new_period = f"{to_year:04d}-{month:02d}"
        _, last = calendar.monthrange(to_year, month)
        completed_on = date(to_year, month, last)
        task_name = task_names.get(comp.task_id, "Unknown task")
        title = completion_page_title(
            task_name=task_name,
            period=new_period,
            status=comp.status,
        )
        props: dict = {
            "Name": nc.title_value(title),
            "Period": nc.rich_text_value(new_period),
            "Completed on": nc.date_prop(completed_on.isoformat()),
        }
        if dry_run:
            stats["updated"] += 1
            continue
        try:
            client.pages.update(page_id=str(page["id"]), properties=props)
            stats["updated"] += 1
        except Exception:
            stats["errors"] += 1
    return stats


def delete_duplicate_completions(*, dry_run: bool) -> dict[str, int]:
    """Archive extra rows that share the same (task_id, period)."""
    settings = get_settings()
    client = nc.make_client(settings.notion_api_key)
    pages = nc.paginate_data_source(client, settings.notion_completions_ds_id)
    by_key: dict[tuple[str, str], list[str]] = {}
    for page in pages:
        comp = page_to_completion(page)
        if not comp.task_id or not comp.period:
            continue
        by_key.setdefault((comp.task_id, comp.period), []).append(str(page["id"]))

    to_delete: list[str] = []
    for ids in by_key.values():
        if len(ids) > 1:
            to_delete.extend(ids[1:])

    stats = {"duplicate_groups": sum(1 for ids in by_key.values() if len(ids) > 1), "deleted": 0}
    if dry_run:
        stats["would_delete"] = len(to_delete)
        return stats
    for pid in to_delete:
        client.pages.update(page_id=pid, archived=True)
        stats["deleted"] += 1
    return stats


def format_audit(snapshot: dict[str, int | dict[str, int]]) -> str:
    by_year = snapshot.get("completions_by_year") or {}
    y2026 = by_year.get("2026", 0)
    task_line = (
        f"Tasks total: {snapshot['tasks_total']} "
        f"(active {snapshot['tasks_active']}, inactive {snapshot['tasks_inactive']})"
    )
    dup_line = (
        f"Duplicate (task, period) pairs: {snapshot['completion_duplicate_pairs']} "
        f"(extra rows {snapshot['completion_duplicate_extra_rows']})"
    )
    expect_line = (
        f"Expected: ~{EXPECTED_ACTIVE_TASKS} active tasks, "
        f"{EXPECTED_SCREENSHOT_COMPLETIONS_2026} completions in 2026 (got {y2026})"
    )
    lines = [
        "=== Notion row audit ===",
        task_line,
        f"Monthly HVAC templates (active): {snapshot['monthly_hvac_active']}",
        f"Completions total: {snapshot['completions_total']} by year: {by_year}",
        dup_line,
        expect_line,
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument(
        "--rewrite-completion-year",
        nargs=2,
        metavar=("FROM", "TO"),
        type=int,
        help="Rewrite Period + Completed on from FROM calendar year to TO (e.g. 2025 2026)",
    )
    parser.add_argument(
        "--dedupe-completions",
        action="store_true",
        help="Archive duplicate completion rows",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    before = audit_row_counts()
    print(format_audit(before))

    actions: list[str] = []
    if args.rewrite_completion_year:
        fy, ty = args.rewrite_completion_year
        fix_stats = rewrite_completion_year(from_year=fy, to_year=ty, dry_run=args.dry_run)
        actions.append(f"rewrite_completion_year {fy}->{ty} dry_run={args.dry_run}: {fix_stats}")

    if args.dedupe_completions:
        dedupe_stats = delete_duplicate_completions(dry_run=args.dry_run)
        actions.append(f"dedupe_completions dry_run={args.dry_run}: {dedupe_stats}")

    after = before if args.dry_run or not actions else audit_row_counts()
    if actions and not args.dry_run:
        print(format_audit(after))

    log_body = {
        "before": before,
        "after": after,
        "actions": actions,
        "dry_run": args.dry_run,
    }
    args.log.parent.mkdir(parents=True, exist_ok=True)
    text = format_audit(before)
    if actions:
        text += "\n--- actions ---\n" + "\n".join(actions)
    if not args.dry_run and actions:
        text += "\n--- after ---\n" + format_audit(after)
    args.log.write_text(text + "\n", encoding="utf-8")
    json_path = args.log.with_suffix(".json")
    json_path.write_text(json.dumps(log_body, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
