"""Archive inactive task rows and completion rows that still point at them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.integrations.notion.mappers import page_to_completion, page_to_template

DEFAULT_LOG = Path("/opt/cursor/artifacts/purge-inactive-duplicates.json")


def run(*, dry_run: bool, log_path: Path) -> dict[str, int]:
    settings = get_settings()
    if not settings.notion_api_key:
        raise SystemExit("NOTION_API_KEY missing")

    client = nc.make_client(settings.notion_api_key)
    inactive_ids: list[str] = []
    for page in nc.paginate_data_source(client, settings.notion_tasks_ds_id):
        tmpl = page_to_template(page)
        if not tmpl.active:
            inactive_ids.append(tmpl.task_id)

    inactive_set = set(inactive_ids)
    completion_ids: list[str] = []
    for page in nc.paginate_data_source(client, settings.notion_completions_ds_id):
        comp = page_to_completion(page)
        if comp.task_id in inactive_set:
            completion_ids.append(str(page["id"]))

    stats = {
        "dry_run": dry_run,
        "inactive_tasks": len(inactive_ids),
        "orphan_completions": len(completion_ids),
        "archived_tasks": 0,
        "archived_completions": 0,
    }

    if dry_run:
        print(
            f"Would archive {len(completion_ids)} completion rows and {len(inactive_ids)} task rows"
        )
        payload = {**stats, "task_ids": inactive_ids, "completion_ids": completion_ids}
        log_path.write_text(json.dumps(payload, indent=2))
        return stats

    for pid in completion_ids:
        client.pages.update(page_id=pid, archived=True)
        stats["archived_completions"] += 1
    for pid in inactive_ids:
        client.pages.update(page_id=pid, archived=True)
        stats["archived_tasks"] += 1

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report counts only")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()
    run(dry_run=args.dry_run, log_path=args.log)


if __name__ == "__main__":
    main()
