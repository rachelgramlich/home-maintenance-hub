from __future__ import annotations

from maintenance_wizard.config import get_settings
from maintenance_wizard.store.base import TaskStore
from maintenance_wizard.store.local import LocalTaskStore


def get_store() -> TaskStore:
    settings = get_settings()
    if settings.store == "notion":
        from maintenance_wizard.store.notion import NotionTaskStore

        return NotionTaskStore(settings)
    return LocalTaskStore(settings.local_data_path)
