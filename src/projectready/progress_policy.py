"""Validate honest day-scoped completion percentages; not a time tracker.

A DONE milestone needs real evidence. Other statuses contribute zero percentage.
Remain-hour allocation is a planning heuristic; not a completion ETA when blocked.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

VALID = {"DONE", "IN_PROGRESS", "BLOCKED", "NOT_STARTED", "SKIPPED"}

def expected_remaining_hours(planned_hours: float, remaining_percent: int) -> float:
    value = Decimal(str(planned_hours)) * Decimal(remaining_percent) / 100
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def validate_daily_progress(entry: dict) -> dict:
    milestones = entry["milestones"]
    if not isinstance(milestones, list) or not milestones:
        raise ValueError("At least one day-scoped milestone is required")
    ids = [m["id"] for m in milestones]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate milestone identifiers")
    if any(m["status"] not in VALID for m in milestones):
        raise ValueError("Invalid milestone status")
    if any(type(m["weight_percent"]) is not int or m["weight_percent"] <= 0 for m in milestones):
        raise ValueError("Positive integer weights required")
    if sum(m["weight_percent"] for m in milestones) != 100:
        raise ValueError("Daily milestones must total exactly 100%")
    if any(m["status"] == "DONE" and not m.get("evidence") for m in milestones):
        raise ValueError("Every completed milestone requires evidence")
    complete = sum(m["weight_percent"] for m in milestones if m["status"] == "DONE")
    if entry["completed_percent"] != complete or entry["remaining_percent"] != 100 - complete:
        raise ValueError("Displayed percentage does not match evidenced DONE items")
    planned, reserve = entry["planned_active_hours"], entry["separate_reserve_hours"]
    if not isinstance(planned, (float, int)) or not isinstance(reserve, (float, int)) or planned < 0 or reserve < 0:
        raise ValueError("Nonnegative separate planned and reserve hour budgets required")
    left = expected_remaining_hours(planned, 100-complete)
    if entry["remaining_plan_allocation_hours_approx"] != left:
        raise ValueError("Remaining planned-hour allocation not aligned with completion")
    if entry["remaining_reserve_allocation_hours"] != reserve:
        raise ValueError("Reserve is allocation, never call it measured unused hours")
    if entry["actual_active_hours"] is None:
        if entry["actual_time_measurement"] != "NOT_MEASURED":
            raise ValueError("Unknown active hours cannot be labeled measured")
    elif not isinstance(entry["actual_active_hours"], (float, int)) or entry["actual_active_hours"] < 0:
        raise ValueError("Invalid measured hours")
    if any(m["status"] == "BLOCKED" for m in milestones):
        if entry["remaining_total_completion_eta_hours"] is not None:
            raise ValueError("Blocked external dependency cannot have a guaranteed completion ETA")
        if not entry.get("remaining_total_completion_eta_reason"):
            raise ValueError("Missing blocker explanation")
    return {"completed_percent":complete, "remaining_percent":100-complete,
            "remaining_plan_allocation_hours_approx":left}
