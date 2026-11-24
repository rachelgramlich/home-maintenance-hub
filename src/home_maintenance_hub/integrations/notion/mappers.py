from __future__ import annotations

from datetime import date
from typing import Any

from home_maintenance_hub.domain.schedule import MONTH_NAMES
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.models import Completion, Contractor, Template


def page_to_template(page: dict[str, Any]) -> Template:
    props = page.get("properties") or {}
    page_id = str(page.get("id", ""))
    month_num = nc.number_value(props.get("Month #"))
    if month_num is None:
        month_name = nc.select_name(props.get("Month"))
        month_num = float(MONTH_NAMES.get(month_name.lower(), 1))
    rel = nc.relation_ids(props.get("Contractor"))
    stable = nc.plain_text(props.get("Stable key"))
    cadence_select = nc.select_name(props.get("Cadence"))
    if cadence_select:
        cadence = "monthly" if cadence_select.lower().startswith("month") else "annual"
    elif stable.endswith("|monthly"):
        cadence = "monthly"
    else:
        cadence = "annual"
    return Template(
        task_id=page_id,
        name=nc.plain_text(props.get("Task")),
        due_month=int(month_num),
        area=nc.select_name(props.get("Area")) or "Other",
        cadence=cadence,  # type: ignore[arg-type]
        active=nc.checkbox_value(props.get("Active")) if "Active" in props else True,
        month_name=nc.select_name(props.get("Month")),
        task_type=nc.select_name(props.get("Type")),
        effort=nc.select_name(props.get("Effort")),
        priority=nc.select_name(props.get("Priority")) or "Medium",  # type: ignore[arg-type]
        season=nc.select_name(props.get("Season")),
        instructions=nc.plain_text(props.get("Instructions")),
        links=(),
        contractor_id=rel[0] if rel else None,
        stable_key=nc.plain_text(props.get("Stable key")),
        notion_url=str(page.get("url") or ""),
    )


def page_to_contractor(page: dict[str, Any], linked_task_ids: tuple[str, ...] = ()) -> Contractor:
    props = page.get("properties") or {}
    page_id = str(page.get("id", ""))
    return Contractor(
        contractor_id=page_id,
        name=nc.plain_text(props.get("Name")),
        trade=nc.select_name(props.get("Trade")),
        phone=nc.plain_text(props.get("Phone")),
        email=nc.plain_text(props.get("Email")),
        website=str((props.get("Website") or {}).get("url") or ""),
        notes=nc.plain_text(props.get("Notes")),
        active=nc.checkbox_value(props.get("Active")) if "Active" in props else True,
        notion_url=str(page.get("url") or ""),
        linked_task_ids=linked_task_ids,
    )


def page_to_completion(page: dict[str, Any]) -> Completion:
    props = page.get("properties") or {}
    page_id = str(page.get("id", ""))
    rel = nc.relation_ids(props.get("Task"))
    completed_raw = nc.date_start(props.get("Completed on"))
    completed_on = date.fromisoformat(completed_raw[:10]) if completed_raw else None
    status = nc.select_name(props.get("Status")) or "done"
    if status not in ("in_progress", "done", "wont_do"):
        status = "done"
    return Completion(
        completion_id=page_id,
        task_id=rel[0] if rel else "",
        period=nc.plain_text(props.get("Period")),
        status=status,  # type: ignore[arg-type]
        completed_on=completed_on,
        notes=nc.plain_text(props.get("Notes")),
        notion_url=str(page.get("url") or ""),
    )
