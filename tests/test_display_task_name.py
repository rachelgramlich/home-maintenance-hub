from __future__ import annotations

from maintenance_wizard.domain.display import display_task_name


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
