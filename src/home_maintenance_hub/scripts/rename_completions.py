"""Retitle [MW] Completions rows to human-readable names."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.domain.schedule import completion_page_title
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_completion, page_to_template

LOG_PATH = Path("/opt/cursor/artifacts/rename-completions.log")


def retitle_completions(*, dry_run: bool) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY missing")
        return {"error": 1}

    client = nc.make_client(settings.notion_api_key)
    task_pages = nc.paginate_data_source(client, settings.notion_tasks_ds_id)
    task_names = {page_to_template(p).task_id: page_to_template(p).name for p in task_pages}

    stats = {"updated": 0, "unchanged": 0, "errors": 0}
    lines: list[str] = [f"rename_completions dry_run={dry_run}", "---"]

    for page in nc.paginate_data_source(client, settings.notion_completions_ds_id):
        comp = page_to_completion(page)
        if not comp.task_id or not comp.period:
            stats["errors"] += 1
            lines.append(f"SKIP missing task/period page={str(page.get('id', ''))[:8]}…")
            continue
        task_name = task_names.get(comp.task_id, "Unknown task")
        title = completion_page_title(
            task_name=task_name,
            period=comp.period,
            status=comp.status,
        )
        props = page.get("properties") or {}
        current = nc.plain_text(props.get("Name"))
        if current == title:
            stats["unchanged"] += 1
            continue
        lines.append(f"{'DRY' if dry_run else 'SET'} {current!r} -> {title!r}")
        if dry_run:
            stats["updated"] += 1
            continue
        try:
            client.pages.update(
                page_id=str(page["id"]),
                properties={"Name": nc.title_value(title)},
            )
            stats["updated"] += 1
        except Exception as exc:
            stats["errors"] += 1
            lines.append(f"ERR {comp.period}: {exc}")

    lines.append("---")
    lines.append(str(stats))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retitle completion rows in Notion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    stats = retitle_completions(dry_run=args.dry_run)
    if stats.get("error"):
        return 1
    if stats.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
