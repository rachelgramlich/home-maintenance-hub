from __future__ import annotations

from maintenance_wizard.integrations.notion.mappers import page_to_template


def _task_page(
    *, cadence: str | None, stable: str, name: str = "Electrical: Test GFCI outlets"
) -> dict:
    cadence_prop: dict
    if cadence is None:
        cadence_prop = {"type": "select", "select": None}
    else:
        cadence_prop = {"type": "select", "select": {"name": cadence}}
    return {
        "id": "page-1",
        "properties": {
            "Task": {"type": "title", "title": [{"plain_text": name}]},
            "Month #": {"type": "number", "number": 4},
            "Month": {"type": "select", "select": {"name": "April"}},
            "Area": {"type": "select", "select": {"name": "Electrical"}},
            "Cadence": cadence_prop,
            "Stable key": {
                "type": "rich_text",
                "rich_text": [{"plain_text": stable}],
            },
        },
    }


def test_cadence_select_annual_wins_over_monthly_stable_suffix() -> None:
    page = _task_page(
        cadence="Annual",
        stable="electrical: test gfci outlets|electrical|monthly",
    )
    assert page_to_template(page).cadence == "annual"


def test_cadence_select_monthly_used_when_present() -> None:
    page = _task_page(
        cadence="Monthly",
        stable="replace hvac filter|hvac|monthly",
        name="Replace HVAC filter",
    )
    assert page_to_template(page).cadence == "monthly"


def test_missing_cadence_falls_back_to_stable_monthly_suffix() -> None:
    page = _task_page(
        cadence=None, stable="replace hvac filter|hvac|monthly", name="Replace HVAC filter"
    )
    assert page_to_template(page).cadence == "monthly"
