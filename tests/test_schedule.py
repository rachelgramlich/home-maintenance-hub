from datetime import date

from maintenance_wizard.domain.board import build_month_board
from maintenance_wizard.domain.schedule import task_applies_to_board, terminal_completion_exists
from maintenance_wizard.models import Completion, Template, Urgency


def test_monthly_always_applies() -> None:
    t = Template("a", "Filter", "monthly", 1, 15, "HVAC")
    assert task_applies_to_board(t, 2026, 3, [])


def test_annual_only_due_month_or_carry() -> None:
    t = Template("b", "Heat service", "annual", 10, 1, "HVAC")
    assert task_applies_to_board(t, 2026, 10, [])
    assert not task_applies_to_board(t, 2026, 3, [])
    done = [
        Completion("1", "b", "2026-10", "done", date(2026, 10, 5)),
    ]
    assert not task_applies_to_board(t, 2026, 11, done)
    assert task_applies_to_board(t, 2026, 11, [])


def test_overdue_when_prior_month_open() -> None:
    templates = [
        Template("m", "Monthly", "monthly", 1, 1, "Other"),
    ]
    completions: list[Completion] = []
    board = build_month_board(templates, completions, 2026, 3, date(2026, 3, 5))
    assert len(board) == 1
    assert board[0].urgency == Urgency.OVERDUE


def test_current_month_stays_open_after_due_day() -> None:
    templates = [Template("m", "Monthly", "monthly", 1, 1, "Other")]
    completions = [
        Completion("1", "m", "2026-02", "done", date(2026, 2, 2)),
    ]
    board = build_month_board(templates, completions, 2026, 3, date(2026, 3, 20))
    assert board[0].urgency == Urgency.NORMAL


def test_done_hides_from_board_when_not_showing_closed() -> None:
    templates = [Template("m", "Monthly", "monthly", 1, 1, "Other")]
    completions = [
        Completion("1", "m", "2026-03", "done", date(2026, 3, 1)),
    ]
    board = build_month_board(templates, completions, 2026, 3, date(2026, 3, 5))
    assert board[0].urgency == Urgency.DONE


def test_terminal_completion_exists() -> None:
    completions = [Completion("1", "x", "2026-01", "wont_do", date(2026, 1, 2))]
    assert terminal_completion_exists(completions, "x", "2026-01")