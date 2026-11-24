"""Backfill: strip import boilerplate from [MW] Tasks Instructions in Notion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.domain.instructions import clean_instruction_text
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_template

LOG_PATH = Path("/opt/cursor/artifacts/notion-instructions-cleanup.log")


def clean_notion_instructions(*, dry_run: bool) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY missing")
        return {"error": 1}

    client = nc.make_client(settings.notion_api_key)
    stats = {"updated": 0, "cleared": 0, "unchanged": 0, "errors": 0}
    lines: list[str] = [f"clean_notion_instructions dry_run={dry_run}", "---"]

    for page in nc.paginate_data_source(client, settings.notion_tasks_ds_id):
        tmpl = page_to_template(page)
        before = tmpl.instructions or ""
        after = clean_instruction_text(before)
        if after == before:
            stats["unchanged"] += 1
            continue
        mode = "DRY" if dry_run else "SET"
        preview_before = before.replace("\n", " ")[:90]
        preview_after = after.replace("\n", " ")[:90] if after else "(empty)"
        lines.append(f"{mode} {tmpl.name!r}: {preview_before!r} -> {preview_after!r}")
        if not after:
            stats["cleared"] += 1
        if dry_run:
            stats["updated"] += 1
            continue
        try:
            client.pages.update(
                page_id=tmpl.task_id,
                properties={"Instructions": nc.rich_text_value(after)},
            )
            stats["updated"] += 1
        except Exception as exc:
            stats["errors"] += 1
            lines.append(f"ERR {tmpl.task_id[:8]}…: {exc}")

    lines.append("---")
    lines.append(str(stats))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove spreadsheet/import boilerplate from Notion task Instructions",
    )
    parser.add_argument("--apply", action="store_true", help="Apply updates (default is dry-run)")
    args = parser.parse_args(argv)
    stats = clean_notion_instructions(dry_run=not args.apply)
    if stats.get("error"):
        return 1
    if stats.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
