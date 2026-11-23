"""One-time / periodic backfill: normalize [MW] Tasks titles (season parens, month suffixes)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_template
from home_maintenance_hub.migration.names import normalize_task_title

LOG_PATH = Path("/opt/cursor/artifacts/notion-title-cleanup.log")


def normalize_task_titles(*, dry_run: bool) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY missing")
        return {"error": 1}

    client = nc.make_client(settings.notion_api_key)
    stats = {"updated": 0, "unchanged": 0, "errors": 0}
    lines: list[str] = [f"normalize_task_titles dry_run={dry_run}", "---"]
    examples: list[str] = []

    for page in nc.paginate_data_source(client, settings.notion_tasks_ds_id):
        tmpl = page_to_template(page)
        current = tmpl.name
        cleaned = normalize_task_title(current)
        if cleaned == current:
            stats["unchanged"] += 1
            continue
        mode = "DRY" if dry_run else "SET"
        short_id = tmpl.task_id[:8]
        line = f"{mode} {current!r} -> {cleaned!r} (page={short_id}…)"
        lines.append(line)
        if len(examples) < 15:
            examples.append(line)
        if dry_run:
            stats["updated"] += 1
            continue
        try:
            client.pages.update(
                page_id=tmpl.task_id,
                properties={"Task": nc.title_value(cleaned)},
            )
            stats["updated"] += 1
        except Exception as exc:
            stats["errors"] += 1
            lines.append(f"ERR {tmpl.task_id[:8]}…: {exc}")

    lines.append("---")
    lines.append(f"examples ({len(examples)} shown):")
    lines.extend(examples)
    lines.append("---")
    lines.append(str(stats))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Strip trailing (season) parens and — Month suffixes from Notion [MW] Tasks",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Apply updates (default is dry-run)")
    args = parser.parse_args(argv)
    dry_run = not args.apply
    stats = normalize_task_titles(dry_run=dry_run)
    if stats.get("error"):
        return 1
    if stats.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
