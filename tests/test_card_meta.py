"""Task card metadata line (mockup C v4)."""

from maintenance_wizard.models import Template
from maintenance_wizard.ui.app import format_card_meta


def test_format_card_meta_mockup_shape() -> None:
    t = Template(
        task_id="1",
        name="Replace HVAC filter",
        due_month=3,
        area="HVAC",
        task_type="Replace",
        effort="XS",
        priority="High",
    )
    assert format_card_meta(t, "2026-03") == "HVAC · Replace · XS · High priority · Period 2026-03"
