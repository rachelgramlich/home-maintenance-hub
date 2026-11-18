from __future__ import annotations

from maintenance_wizard.config import get_settings
from maintenance_wizard.store.base import TaskStore
from maintenance_wizard.store.local import LocalTaskStore


def get_store() -> TaskStore:
    settings = get_settings()
    if settings.store == "google_sheets":
        if not settings.sheet_id:
            msg = "Set MAINTENANCE_WIZARD_SHEET_ID for google_sheets store"
            raise RuntimeError(msg)
        from maintenance_wizard.store.google_sheets import GoogleSheetsTaskStore

        return GoogleSheetsTaskStore(
            sheet_id=settings.sheet_id,
            token_path=str(settings.google_token_path),
        )
    return LocalTaskStore(settings.local_data_path)