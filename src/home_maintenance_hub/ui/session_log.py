"""Board session debug logs (local JSON + feedback attachment)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from home_maintenance_hub.config import get_settings
from home_maintenance_hub.models import BoardTask, Urgency

SESSION_LOG_SCHEMA_VERSION = 1
MAX_SESSION_LOGS = 20
_LOG = logging.getLogger(__name__)


def session_history_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / ".local" / "home_maintenance_hub" / "session_history"


@dataclass
class BoardSessionTrace:
    month_key: str
    store_mode: str
    filters: dict[str, list[str]] = field(default_factory=dict)
    task_ids_rendered: list[str] = field(default_factory=list)
    overdue_ids: list[str] = field(default_factory=list)
    in_progress_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def record_board(self, rows: list[BoardTask]) -> None:
        self.task_ids_rendered = [r.template.task_id for r in rows]
        self.overdue_ids = [r.template.task_id for r in rows if r.urgency == Urgency.OVERDUE]
        self.in_progress_ids = [
            r.template.task_id for r in rows if r.urgency == Urgency.IN_PROGRESS
        ]


def build_session_log(
    trace: BoardSessionTrace, *, built_at: datetime | None = None
) -> dict[str, Any]:
    when = built_at or datetime.now(tz=UTC)
    return {
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        "built_at": when.isoformat(),
        "month_key": trace.month_key,
        "store_mode": trace.store_mode,
        "timezone": get_settings().timezone,
        "filters": trace.filters,
        "task_ids_rendered": list(trace.task_ids_rendered),
        "overdue_ids": list(trace.overdue_ids),
        "in_progress_ids": list(trace.in_progress_ids),
        "errors": list(trace.errors),
    }


def write_session_log(log: dict[str, Any], *, history_dir: Path | None = None) -> Path | None:
    directory = history_dir or session_history_dir()
    stamp = datetime.fromisoformat(log["built_at"]).astimezone(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    path = directory / f"{stamp}.json"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
        files = sorted(directory.glob("*.json"))
        for old in files[:-MAX_SESSION_LOGS]:
            old.unlink(missing_ok=True)
    except OSError:
        _LOG.warning("Could not write session debug log to %s", path, exc_info=True)
        return None
    return path


def latest_session_log_path(history_dir: Path | None = None) -> Path | None:
    directory = history_dir or session_history_dir()
    if not directory.is_dir():
        return None
    files = sorted(directory.glob("*.json"))
    return files[-1] if files else None
