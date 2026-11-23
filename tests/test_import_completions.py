"""Screenshot completion import expectations (year + periods)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from home_maintenance_hub.scripts.import_completions import CHECKED, DEFAULT_YEAR, CompletionSpec

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "screenshot_completions.json"


def test_screenshot_fixture_matches_checked_specs() -> None:
    year = DEFAULT_YEAR
    assert year == 2026
    expected = [
        {
            "task": s.task,
            "area": s.area,
            "month": s.month,
            "period": s.period(year),
            "completed_on": s.completed_on(year).isoformat(),
        }
        for s in (CompletionSpec(t, a, m) for t, a, m in CHECKED)
    ]
    payload = {"year": year, "checks": expected}
    _FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    if _FIXTURE.is_file():
        saved = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        assert saved == payload
    else:
        _FIXTURE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for row in expected:
        assert row["period"].startswith("2026-")
        y, m, d = map(int, row["completed_on"].split("-"))
        assert date(y, m, d) == CompletionSpec(row["task"], row["area"], row["month"]).completed_on(
            year
        )
