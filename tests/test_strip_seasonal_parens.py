from __future__ import annotations

from maintenance_wizard.domain.display import display_task_name
from maintenance_wizard.migration.names import strip_seasonal_parens
from maintenance_wizard.scripts.migrate_xlsx import CatalogRow, build_task_props


def test_strip_seasonal_parens_trailing() -> None:
    assert strip_seasonal_parens("Service heating (fall)") == "Service heating"
    assert strip_seasonal_parens("HVAC: Service heating (fall)") == "HVAC: Service heating"
    assert strip_seasonal_parens("HVAC: Service A/C (spring)") == "HVAC: Service A/C"
    assert strip_seasonal_parens("Task (SUMMER)") == "Task"
    assert strip_seasonal_parens("Task (Mid-Summer)") == "Task"
    assert strip_seasonal_parens("Task (mid summer)") == "Task"
    assert strip_seasonal_parens("Task (mid summer)") == "Task"


def test_strip_seasonal_parens_leaves_other() -> None:
    assert strip_seasonal_parens("Inspect roof (annual)") == "Inspect roof (annual)"
    assert strip_seasonal_parens("Service (spring + fall) units") == "Service (spring + fall) units"


def test_display_task_name_matches_helper() -> None:
    assert display_task_name("HVAC: Service heating (fall)") == strip_seasonal_parens(
        "HVAC: Service heating (fall)"
    )


def test_build_task_props_strips_title_not_stable_key() -> None:
    row = CatalogRow(
        task="HVAC: Service heating (fall)",
        month="October",
        month_num=10,
        area="HVAC",
        task_type="Service",
        priority="High",
        effort="M",
        season="Fall",
        instructions="",
        cadence="annual",
        migration_key="hvac: service heating (fall)|hvac|october",
    )
    props = build_task_props(row)
    task_title = props["Task"]["title"][0]["text"]["content"]
    assert task_title == "HVAC: Service heating"
    assert props["Stable key"]["rich_text"][0]["text"]["content"] == row.migration_key
