from __future__ import annotations

from home_maintenance_hub.domain.display import display_task_name


def test_strips_trailing_season_parentheticals() -> None:
    assert display_task_name("Service heating (fall)") == "Service heating"
    assert display_task_name("HVAC: Service heating (fall)") == "HVAC: Service heating"
    assert display_task_name("HVAC: Service A/C (spring)") == "HVAC: Service A/C"
    assert display_task_name("Task (SUMMER)") == "Task"
    assert display_task_name("Task (Mid-Summer)") == "Task"


def test_leaves_non_season_parentheticals() -> None:
    assert display_task_name("Inspect roof (annual)") == "Inspect roof (annual)"


def test_leaves_mid_sentence_seasons() -> None:
    assert display_task_name("Service (spring + fall) units") == "Service (spring + fall) units"


def test_strips_trailing_month_suffix() -> None:
    assert display_task_name("Replace HVAC filter — March") == "Replace HVAC filter"
    assert display_task_name("Replace HVAC filter \u2013 June") == "Replace HVAC filter"
    assert display_task_name("Laundry: Professional dryer vent cleaning — March") == (
        "Laundry: Professional dryer vent cleaning"
    )
