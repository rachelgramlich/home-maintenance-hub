from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from maintenance_wizard.domain.schedule import MONTH_LABELS, MONTH_NAMES
from maintenance_wizard.migration.keys import map_area, normalize_token

Cadence = str  # "monthly" | "annual"

_MONTH_ALT = "|".join(re.escape(name) for name in MONTH_NAMES)
_TASK_MONTH_SUFFIX = re.compile(rf"\s[-\u2013\u2014]\s*({_MONTH_ALT})\s*$", re.IGNORECASE)


def strip_month_suffix(task: str) -> str:
    return _TASK_MONTH_SUFFIX.sub("", task.strip())


def canonical_group_key(task: str, area: str) -> str:
    base = strip_month_suffix(task)
    return f"{normalize_token(base)}|{normalize_token(map_area(area))}"


def monthly_stable_key(task: str, area: str) -> str:
    base = strip_month_suffix(task)
    return f"{normalize_token(base)}|{normalize_token(map_area(area))}|monthly"


def slot_stable_key(task: str, area: str, month: str) -> str:
    from maintenance_wizard.migration.keys import stable_key

    return stable_key(task, map_area(area), month)


@dataclass(frozen=True)
class CadencePlan:
    cadence: Cadence
    canonical_name: str
    area: str
    month_slots: tuple[int, ...]


def infer_cadence_plans(
    rows: list[tuple[str, str, str, int]],
) -> dict[str, CadencePlan]:
    """Group (task, area, month_name, month_num) rows and infer monthly vs annual."""
    groups: dict[str, list[tuple[str, str, str, int]]] = defaultdict(list)
    for task, area, month_name, month_num in rows:
        key = canonical_group_key(task, area)
        groups[key].append((task, area, month_name, month_num))

    plans: dict[str, CadencePlan] = {}
    for key, members in groups.items():
        month_nums = sorted({m[3] for m in members if m[3]})
        task0, area0, _, _ = members[0]
        canonical = strip_month_suffix(task0)
        if len(month_nums) > 1:
            plans[key] = CadencePlan(
                cadence="monthly",
                canonical_name=canonical,
                area=map_area(area0),
                month_slots=tuple(month_nums),
            )
        else:
            plans[key] = CadencePlan(
                cadence="annual",
                canonical_name=task0.strip(),
                area=map_area(area0),
                month_slots=tuple(month_nums),
            )
    return plans


def display_month_for_cadence(cadence: Cadence, due_month: int) -> str:
    if cadence == "monthly":
        return "January"
    return MONTH_LABELS.get(due_month, "January")
