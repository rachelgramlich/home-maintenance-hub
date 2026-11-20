"""Task metadata line lives in the details drawer only (not on board cards)."""

from maintenance_wizard.models import Template
from maintenance_wizard.ui.views.drawer import format_drawer_task_meta, task_context_fields


def test_task_context_fields_in_drawer() -> None:
    t = Template(
        task_id="1",
        name="Replace HVAC filter",
        due_month=3,
        area="HVAC",
        month_name="March",
        task_type="Replace",
        effort="XS",
        priority="High",
        season="Spring",
        cadence="monthly",
    )
    fields = dict(task_context_fields(t, "2026-03"))
    assert fields["Area"] == "HVAC"
    assert fields["Type"] == "Replace"
    assert fields["Period"] == "2026-03"
    assert fields["Cadence"] == "Monthly"
    assert "Area: HVAC" in format_drawer_task_meta(t, "2026-03")
