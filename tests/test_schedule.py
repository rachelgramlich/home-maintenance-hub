from datetime import date

from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.domain.schedule import task_applies_to_board, terminal_completion_exists
from maintenance_wizard.models import Completion, Template, Urgency


def _t(task_id: str, month: int, area: str = "HVAC", priority: str = "Medium") -> Template:
    return Template(
        task_id=task_id,
        name=f"Task {task_id}",
        due_month=month,
        area=area,
        priority=priority,  # type: ignore[arg-type]
    )


def test_task_shows_in_assigned_month() -> None:
    t = _t("a", 3)
    assert task_applies_to_board(t, 2026, 3, [])


def test_carry_over_after_assigned_month() -> None:
    t = _t("b", 2)
    assert not task_applies_to_board(t, 2026, 1, [])
    assert task_applies_to_board(t, 2026, 3, [])
    done = [Completion("1", "b", "2026-02", "done", date(2026, 2, 28))]
    assert not task_applies_to_board(t, 2026, 4, done)


def test_overdue_carry() -> None:
    templates = [_t("m", 2)]
    board = build_month_board(templates, [], 2026, 3, date(2026, 3, 5))
    assert len(board) == 1
    assert board[0].urgency == Urgency.OVERDUE


def test_current_month_open() -> None:
    templates = [_t("m", 3)]
    board = build_month_board(templates, [], 2026, 3, date(2026, 3, 20))
    assert board[0].urgency == Urgency.NORMAL


def test_in_progress_badge() -> None:
    templates = [_t("m", 3)]
    completions = [
        Completion("1", "m", "2026-03", "in_progress", date(2026, 3, 5)),
    ]
    board = build_month_board(templates, completions, 2026, 3, date(2026, 3, 10))
    assert board[0].urgency == Urgency.IN_PROGRESS


def test_priority_sort_within_bucket() -> None:
    templates = [
        _t("low", 3, priority="Low"),
        _t("high", 3, priority="High"),
    ]
    board = build_month_board(templates, [], 2026, 3, date(2026, 3, 1))
    assert board[0].template.task_id == "high"


def test_terminal_completion_exists() -> None:
    completions = [Completion("1", "x", "2026-01", "wont_do", date(2026, 1, 2))]
    assert terminal_completion_exists(completions, "x", "2026-01")
    in_prog = [Completion("2", "y", "2026-01", "in_progress", date(2026, 1, 2))]
    assert not terminal_completion_exists(in_prog, "y", "2026-01")
