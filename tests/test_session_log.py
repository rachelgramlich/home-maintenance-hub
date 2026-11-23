"""Session debug log builder tests."""

from __future__ import annotations

from datetime import UTC, datetime

from home_maintenance_hub.models import BoardTask, Template, Urgency
from home_maintenance_hub.ui.session_log import (
    BoardSessionTrace,
    build_session_log,
    write_session_log,
)


def test_build_session_log_records_overdue_ids(tmp_path) -> None:
    template = Template(task_id="t1", name="Filter", due_month=11, area="HVAC")
    rows = [
        BoardTask(
            template=template,
            period="2026-11",
            urgency=Urgency.OVERDUE,
            last_done_on=None,
            last_done_notes="",
        )
    ]
    trace = BoardSessionTrace(month_key="2026-11", store_mode="local")
    trace.record_board(rows)
    log = build_session_log(trace, built_at=datetime(2026, 11, 20, tzinfo=UTC))

    assert log["month_key"] == "2026-11"
    assert log["task_ids_rendered"] == ["t1"]
    assert log["overdue_ids"] == ["t1"]

    path = write_session_log(log, history_dir=tmp_path)
    assert path is not None
    assert path.exists()
