from __future__ import annotations

import re

from maintenance_wizard.domain.schedule import MONTH_NAMES


def normalize_token(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def stable_key(task: str, area: str, month: str) -> str:
    return f"{normalize_token(task)}|{normalize_token(area)}|{normalize_token(month)}"


def month_number(month_name: str) -> int:
    return MONTH_NAMES.get(month_name.strip().lower(), 0)


MW_AREAS = {
    "HVAC",
    "Plumbing",
    "Exterior",
    "Laundry",
    "Appliances",
    "Safety",
    "Pest",
    "Electrical",
    "Other",
}

AREA_ALIASES = {
    "Basement/Humidity": "Other",
    "Fireplace": "Other",
    "Yard": "Exterior",
    "Interior": "Other",
}

MW_TYPES = {"Replace", "Service", "Clean", "Inspect/Test"}

TYPE_ALIASES = {
    "Prevent": "Inspect/Test",
    "Monitor": "Inspect/Test",
    "Seasonal setup": "Inspect/Test",
}


def map_area(area: str) -> str:
    if area in MW_AREAS:
        return area
    return AREA_ALIASES.get(area, "Other")


def map_type(task_type: str) -> str:
    if task_type in MW_TYPES:
        return task_type
    return TYPE_ALIASES.get(task_type, "Inspect/Test")


def map_effort(effort: str) -> str:
    if effort in ("XS", "S", "M"):
        return effort
    if effort == "L":
        return "M"
    return "S"
