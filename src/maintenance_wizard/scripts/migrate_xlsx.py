"""Idempotent migration: Ocala xlsx Home Maintenance tab -> Notion [MW] Tasks + Completions."""

from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from maintenance_wizard.config import get_settings
from maintenance_wizard.integrations.notion import client as nc
from maintenance_wizard.integrations.notion.mappers import page_to_template
from maintenance_wizard.migration.cadence import (
    canonical_group_key,
    display_month_for_cadence,
    infer_cadence_plans,
    monthly_stable_key,
    strip_month_suffix,
)
from maintenance_wizard.migration.keys import (
    map_area,
    map_effort,
    map_type,
    month_number,
    stable_key,
)
from maintenance_wizard.migration.names import strip_seasonal_parens
from maintenance_wizard.store.notion import NotionTaskStore

DEPRECATED_DS = "d7cb0608-b694-4103-b3ce-65af4fc82d3c"
DEFAULT_YEAR = datetime.now(ZoneInfo("America/New_York")).year
HOME_TAB = "Home Maintenance"
_FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "home_maintenance_rows.json"


@dataclass
class ImportRow:
    task: str
    month: str
    area: str
    task_type: str
    priority: str
    effort: str
    season: str
    instructions: str
    done: bool

    @property
    def month_num(self) -> int:
        return month_number(self.month)

    @property
    def key(self) -> str:
        return stable_key(self.task, self.area, self.month)


@dataclass
class CatalogRow:
    """One Notion task row to upsert (annual slot or consolidated monthly)."""

    task: str
    month: str
    month_num: int
    area: str
    task_type: str
    priority: str
    effort: str
    season: str
    instructions: str
    cadence: str
    migration_key: str


def last_day_of_month(year: int, month: int) -> date:
    _, last = calendar.monthrange(year, month)
    return date(year, month, last)


def read_xlsx(path: Path) -> list[ImportRow]:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    if HOME_TAB not in wb.sheetnames:
        msg = f"Sheet {HOME_TAB!r} not in {path}"
        raise ValueError(msg)
    ws = wb[HOME_TAB]
    rows = ws.iter_rows(values_only=True)
    header = [str(c or "").strip() for c in next(rows)]
    idx = {name: i for i, name in enumerate(header)}
    required = ["Task", "Month", "Area", "Type", "Priority", "Effort"]
    for col in required:
        if col not in idx:
            msg = f"Missing column {col!r} in {HOME_TAB}"
            raise ValueError(msg)

    out: list[ImportRow] = []
    for raw in rows:
        if not raw or not raw[idx["Task"]]:
            continue
        done_col = idx.get("Done?") or idx.get("Done")
        done = False
        if done_col is not None:
            val = raw[done_col]
            if isinstance(val, bool):
                done = val
            elif val is not None:
                done = str(val).strip().lower() in ("yes", "y", "true", "1", "x", "done")
        out.append(
            ImportRow(
                task=str(raw[idx["Task"]]).strip(),
                month=str(raw[idx["Month"]]).strip(),
                area=str(raw[idx["Area"]]).strip(),
                task_type=str(raw[idx["Type"]]).strip(),
                priority=str(raw[idx["Priority"]] or "Medium").strip(),
                effort=str(raw[idx["Effort"]] or "S").strip(),
                season=str(raw[idx.get("Season", -1)] or "").strip() if "Season" in idx else "",
                instructions=str(raw[idx.get("Notes", -1)] or "").strip() if "Notes" in idx else "",
                done=done,
            )
        )
    return out


def read_json_fixture(path: Path) -> list[ImportRow]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ImportRow(
            task=str(row["task"]),
            month=str(row["month"]),
            area=str(row["area"]),
            task_type=str(row["task_type"]),
            priority=str(row.get("priority") or "Medium"),
            effort=str(row.get("effort") or "S"),
            season=str(row.get("season") or ""),
            instructions=str(row.get("instructions") or ""),
            done=bool(row.get("done")),
        )
        for row in data
    ]


def read_deprecated_notion(client: Any) -> list[ImportRow]:
    pages = nc.paginate_data_source(client, DEPRECATED_DS)
    out: list[ImportRow] = []
    for page in pages:
        props = page.get("properties") or {}
        out.append(
            ImportRow(
                task=nc.plain_text(props.get("Task")),
                month=nc.select_name(props.get("Month")),
                area=nc.select_name(props.get("Area")),
                task_type=nc.select_name(props.get("Type")),
                priority=nc.select_name(props.get("Priority")) or "Medium",
                effort=nc.select_name(props.get("Effort")) or "S",
                season=nc.select_name(props.get("Season")),
                instructions=nc.plain_text(props.get("Notes")),
                done=False,
            )
        )
    return out


def build_task_props(row: CatalogRow) -> dict[str, Any]:
    cadence_label = "Monthly" if row.cadence == "monthly" else "Annual"
    props: dict[str, Any] = {
        "Task": nc.title_value(strip_seasonal_parens(row.task)),
        "Month": nc.select_value(row.month),
        "Month #": nc.number_prop(row.month_num),
        "Area": nc.select_value(map_area(row.area)),
        "Type": nc.select_value(map_type(row.task_type)),
        "Priority": nc.select_value(row.priority or "Medium"),
        "Effort": nc.select_value(map_effort(row.effort)),
        "Instructions": nc.rich_text_value(row.instructions),
        "Stable key": nc.rich_text_value(row.migration_key),
        "Cadence": nc.select_value(cadence_label),
        "Active": nc.checkbox_prop(True),
        "Links JSON": nc.rich_text_value("[]"),
    }
    if row.season:
        props["Season"] = nc.select_value(row.season)
    return props


def catalog_rows_from_import(rows: list[ImportRow]) -> list[CatalogRow]:
    plan_input = [(r.task, r.area, r.month, r.month_num) for r in rows]
    plans = infer_cadence_plans(plan_input)
    monthly_done: set[str] = set()
    catalog: list[CatalogRow] = []
    for row in rows:
        group = canonical_group_key(row.task, row.area)
        plan = plans[group]
        if plan.cadence == "monthly":
            if group in monthly_done:
                continue
            monthly_done.add(group)
            catalog.append(
                CatalogRow(
                    task=strip_seasonal_parens(plan.canonical_name),
                    month=display_month_for_cadence("monthly", 1),
                    month_num=1,
                    area=row.area,
                    task_type=row.task_type,
                    priority=row.priority,
                    effort=row.effort,
                    season=row.season,
                    instructions=row.instructions,
                    cadence="monthly",
                    migration_key=monthly_stable_key(plan.canonical_name, row.area),
                )
            )
        else:
            catalog.append(
                CatalogRow(
                    task=strip_seasonal_parens(row.task),
                    month=row.month,
                    month_num=row.month_num,
                    area=row.area,
                    task_type=row.task_type,
                    priority=row.priority,
                    effort=row.effort,
                    season=row.season,
                    instructions=row.instructions,
                    cadence="annual",
                    migration_key=row.key,
                )
            )
    return catalog


def monthly_task_id_for_row(row: ImportRow, task_id_by_key: dict[str, str]) -> str | None:
    base = strip_month_suffix(row.task)
    mkey = monthly_stable_key(base, row.area)
    return task_id_by_key.get(mkey) or task_id_by_key.get(row.key)


def dedupe_monthly_slots(
    store: NotionTaskStore,
    *,
    dry_run: bool,
    rows: list[ImportRow],
) -> dict[str, int]:
    """Collapse duplicate per-month Notion rows into one monthly template."""
    plan_input = [(r.task, r.area, r.month, r.month_num) for r in rows]
    plans = infer_cadence_plans(plan_input)
    pages = nc.paginate_data_source(store._client, store._settings.notion_tasks_ds_id)
    templates = [page_to_template(p) for p in pages]
    by_group: dict[str, list] = {}
    for page, tmpl in zip(pages, templates, strict=True):
        cg = canonical_group_key(tmpl.name, tmpl.area)
        plan = plans.get(cg)
        if plan and plan.cadence == "monthly":
            by_group.setdefault(cg, []).append((page, tmpl))

    stats = {"keepers_updated": 0, "slots_deactivated": 0}
    for group, members in by_group.items():
        plan = plans[group]
        if len(members) < 2:
            continue
        members.sort(key=lambda m: (0 if m[1].cadence == "monthly" else 1, m[1].due_month))
        _, keeper = members[0]
        keeper_id = keeper.task_id
        mkey = monthly_stable_key(plan.canonical_name, keeper.area)
        props = {
            "Task": nc.title_value(strip_seasonal_parens(plan.canonical_name)),
            "Month": nc.select_value("January"),
            "Month #": nc.number_prop(1),
            "Cadence": nc.select_value("Monthly"),
            "Stable key": nc.rich_text_value(mkey),
            "Active": nc.checkbox_prop(True),
        }
        if dry_run:
            print(f"  dedupe keeper {plan.canonical_name} ← {len(members)} slots")
            stats["keepers_updated"] += 1
            stats["slots_deactivated"] += len(members) - 1
            continue
        store._client.pages.update(page_id=keeper_id, properties=props)
        stats["keepers_updated"] += 1
        for _, tmpl in members[1:]:
            if tmpl.task_id == keeper_id:
                continue
            store._client.pages.update(
                page_id=tmpl.task_id,
                properties={"Active": nc.checkbox_prop(False)},
            )
            stats["slots_deactivated"] += 1
    return stats


def index_tasks_by_key(store: NotionTaskStore) -> dict[str, str]:
    pages = nc.paginate_data_source(store._client, store._settings.notion_tasks_ds_id)
    out: dict[str, str] = {}
    for page in pages:
        tmpl = page_to_template(page)
        if tmpl.stable_key:
            out[tmpl.stable_key] = tmpl.task_id
        key = stable_key(tmpl.name, tmpl.area, tmpl.month_name)
        out[key] = tmpl.task_id
        if tmpl.cadence == "monthly":
            out[monthly_stable_key(strip_month_suffix(tmpl.name), tmpl.area)] = tmpl.task_id
    return out


def run_migration(
    *,
    dry_run: bool,
    xlsx: Path | None,
    from_deprecated: bool,
    fixture: Path | None,
    completion_year: int,
    apply_cadence_dedupe: bool,
) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY missing — aborting (dry-run logic unavailable for Notion).")
        return {"error": 1}

    try:
        from maintenance_wizard.scripts.notion_row_audit import audit_row_counts, format_audit

        print("Before migration:")
        print(format_audit(audit_row_counts()))
    except Exception as exc:
        print(f"(before audit skipped: {exc})")

    client = nc.make_client(settings.notion_api_key)
    store = NotionTaskStore(settings)

    if xlsx and xlsx.is_file():
        rows = read_xlsx(xlsx)
        source = f"xlsx:{xlsx}"
    elif from_deprecated:
        rows = read_deprecated_notion(client)
        source = "notion:deprecated"
    elif fixture and fixture.is_file():
        rows = read_json_fixture(fixture)
        source = f"fixture:{fixture}"
    else:
        print("Provide --xlsx PATH, --from-deprecated-notion, or --from-fixture PATH")
        return {"error": 1}

    print(f"Source: {source} — {len(rows)} rows")
    if apply_cadence_dedupe:
        dedupe_stats = dedupe_monthly_slots(store, dry_run=dry_run, rows=rows)
        print(f"Cadence dedupe: {dedupe_stats}")

    catalog = catalog_rows_from_import(rows)
    print(f"Catalog rows (after cadence consolidate): {len(catalog)}")
    existing = index_tasks_by_key(store)
    stats = {"create": 0, "update": 0, "skip": 0, "completions": 0, "completion_skip": 0}

    task_id_by_key: dict[str, str] = dict(existing)

    for cat in catalog:
        props = build_task_props(cat)
        page_id = task_id_by_key.get(cat.migration_key)
        if page_id:
            if dry_run:
                print(f"  update  {cat.migration_key}")
                stats["update"] += 1
            else:
                store._client.pages.update(page_id=page_id, properties=props)
                stats["update"] += 1
        elif dry_run:
            print(f"  create  {cat.migration_key}")
            stats["create"] += 1
        else:
            created = store._client.pages.create(
                parent={
                    "type": "data_source_id",
                    "data_source_id": store._settings.notion_tasks_ds_id,
                },
                properties=props,
            )
            task_id_by_key[cat.migration_key] = str(created["id"])
            stats["create"] += 1

    plan_input = [(r.task, r.area, r.month, r.month_num) for r in rows]
    plans = infer_cadence_plans(plan_input)

    for row in rows:
        if not row.done or not row.month_num:
            continue
        group = canonical_group_key(row.task, row.area)
        plan = plans[group]
        if plan.cadence == "monthly":
            tid = monthly_task_id_for_row(row, task_id_by_key)
        else:
            tid = task_id_by_key.get(row.key)
        period = f"{completion_year:04d}-{row.month_num:02d}"
        completed_on = last_day_of_month(completion_year, row.month_num)
        if not tid:
            stats["completion_skip"] += 1
            continue
        if dry_run:
            print(f"  completion {period} done @ {completed_on} for {row.task[:40]}")
            stats["completions"] += 1
        else:
            store.upsert_completion(
                tid,
                period,
                "done",
                completed_on,
                notes="Imported from xlsx (Done?)",
            )
            stats["completions"] += 1

    print("---")
    print(stats)
    if not dry_run and not stats.get("error"):
        try:
            from maintenance_wizard.scripts.notion_row_audit import audit_row_counts, format_audit

            print("After migration:")
            print(format_audit(audit_row_counts()))
        except Exception as exc:
            print(f"(after audit skipped: {exc})")
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate Home Maintenance tasks to Notion")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--xlsx", type=Path, default=None)
    parser.add_argument("--from-deprecated-notion", action="store_true", dest="from_deprecated")
    parser.add_argument(
        "--from-fixture",
        type=Path,
        default=None,
        help="JSON rows (e.g. tests/fixtures/home_maintenance_rows.json)",
    )
    parser.add_argument("--completion-year", type=int, default=DEFAULT_YEAR)
    parser.add_argument(
        "--apply-cadence-dedupe",
        action="store_true",
        help="Deactivate duplicate monthly slot rows; keep one Monthly template",
    )
    args = parser.parse_args(argv)

    xlsx = args.xlsx or get_settings().xlsx_path
    if xlsx is None:
        env_path = os.environ.get("MAINTENANCE_WIZARD_XLSX_PATH")
        if env_path:
            xlsx = Path(env_path)

    fixture = args.from_fixture
    if fixture is None and not xlsx and not args.from_deprecated and _FIXTURE.is_file():
        fixture = _FIXTURE

    stats = run_migration(
        dry_run=args.dry_run,
        xlsx=xlsx,
        from_deprecated=args.from_deprecated,
        fixture=fixture,
        completion_year=args.completion_year,
        apply_cadence_dedupe=args.apply_cadence_dedupe,
    )
    return 1 if stats.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
