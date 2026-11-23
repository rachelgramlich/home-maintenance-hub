from __future__ import annotations

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.store.base import TaskStore
from home_maintenance_hub.store.local import LocalTaskStore


def get_store() -> TaskStore:
    settings = get_settings()
    if settings.store == "notion":
        from home_maintenance_hub.store.notion import NotionTaskStore

        return NotionTaskStore(settings)
    return LocalTaskStore(settings.local_data_path)
