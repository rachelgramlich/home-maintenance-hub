from __future__ import annotations

import json
from pathlib import Path

from home_maintenance_hub.store.local import LocalTaskStore


def test_local_store_drops_retired_template_keys_on_load(tmp_path: Path) -> None:
    path = tmp_path / "store.json"
    path.write_text(
        json.dumps(
            {
                "templates": [
                    {
                        "task_id": "t1",
                        "name": "Filter",
                        "due_month": 1,
                        "area": "HVAC",
                        "links_json": "[]",
                    }
                ],
                "completions": [],
                "contractors": [],
            }
        ),
        encoding="utf-8",
    )
    store = LocalTaskStore(path)
    store.list_templates()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert "links_json" not in saved["templates"][0]
