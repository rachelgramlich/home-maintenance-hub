from datetime import date

from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.domain.schedule import board_period_for_task, task_applies_to_board
from maintenance_wizard.migration.cadence import (
    canonical_group_key,
    infer_cadence_plans,
    monthly_stable_key,
    strip_month_suffix,
)
from maintenance_wizard.models import Completion, Template, Urgency


def test_strip_month_suffix() -> None:
    assert strip_month_suffix("Replace HVAC filter — June") == "Replace HVAC filter"


def test_hvac_inferred_monthly() -> None:
    rows = [
        ("Replace HVAC filter — January", "HVAC", "January", 1),
        ("Replace HVAC filter — February", "HVAC", "February", 2),
    ]
    plans = infer_cadence_plans(rows)
    key = canonical_group_key("Replace HVAC filter — January", "HVAC")
    assert plans[key].cadence == "monthly"
    assert plans[key].canonical_name == "Replace HVAC filter"


def test_monthly_stable_key() -> None:
    assert monthly_stable_key("Replace HVAC filter", "HVAC") == "replace hvac filter|hvac|monthly"


def test_monthly_task_on_every_board_month() -> None:
    t = Template(
        task_id="hvac",
        name="Replace HVAC filter",
        due_month=1,
        area="HVAC",
        cadence="monthly",
    )
    assert task_applies_to_board(t, 2025, 6, [])
    assert task_applies_to_board(t, 2025, 12, [])
    assert board_period_for_task(t, 2025, 6) == "2025-06"


def test_monthly_completions_per_period() -> None:
    t = Template(
        task_id="hvac",
        name="Replace HVAC filter",
        due_month=1,
        area="HVAC",
        cadence="monthly",
        priority="High",
    )
    completions = [
        Completion("1", "hvac", "2025-06", "done", date(2025, 6, 30)),
        Completion("2", "hvac", "2025-07", "done", date(2025, 7, 31)),
    ]
    board_june = build_month_board([t], completions, 2025, 6, date(2025, 6, 15))
    board_july = build_month_board([t], completions, 2025, 7, date(2025, 7, 15))
    assert board_june[0].urgency == Urgency.DONE
    assert board_july[0].urgency == Urgency.DONE
    board_aug = build_month_board([t], completions, 2025, 8, date(2025, 8, 1))
    assert board_aug[0].urgency == Urgency.NORMAL
