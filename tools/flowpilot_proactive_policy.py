"""G119 pure, caller-driven suggestion throttler; no NAS polling/background jobs.

Caller keeps state; only unverified numeric telemetry and strictly typed
simulation time are inspected. All outputs are recommendations, not actions.
"""
from __future__ import annotations

import argparse
import json

from flowpilot_proactive_advisor import advise_local

_SCHEMA = "flowpilot-proactive-policy-v1"
_ALLOWED_IDS = frozenset(("REVIEW_DISK_CAPACITY", "REVIEW_REPEATED_ERRORS",
                          "REVIEW_BACKUP_FRESHNESS"))
_WINDOW = 3600
_MAX_PER_WINDOW = 3
_MAX_PER_TICK = 2


def new_state() -> dict:
    return {"schema": _SCHEMA, "last_tick": 0, "recent": []}


def _valid_state(state: dict) -> bool:
    if (type(state) is not dict or set(state) != {"schema", "last_tick", "recent"}
            or state.get("schema") != _SCHEMA or type(state["last_tick"]) is not int
            or not 0 <= state["last_tick"] <= 4102444800
            or type(state["recent"]) is not list or len(state["recent"]) > _MAX_PER_WINDOW):
        return False
    if any(type(e) is not dict or set(e) != {"time", "id"}
           or type(e["time"]) is not int or not 0 <= e["time"] <= state["last_tick"]
           or e["id"] not in _ALLOWED_IDS for e in state["recent"]):
        return False
    return all(state["recent"][i]["time"] <= state["recent"][i+1]["time"]
               for i in range(len(state["recent"]) - 1))


def evaluate_tick(telemetry: dict, state: dict, now: int, *,
                  opted_in: bool = False) -> dict:
    """No state mutation on invalid inputs, revocation or invalid timestamps."""
    base = {"schema": _SCHEMA, "nas_polled": False, "monitor_started": False,
            "notifications_sent": False, "actions_executed": False,
            "telemetry_verified": False, "release_gate": "HOLD"}
    if type(opted_in) is not bool or not opted_in:
        return {**base, "status": "DISABLED_NO_CONSENT", "proposals": [],
                "next_state": state}
    if not _valid_state(state) or type(now) is not int or not 0 <= now <= 4102444800:
        return {**base, "status": "INVALID_STATE_OR_TIME", "proposals": [],
                "next_state": state}
    if now < state["last_tick"]:
        return {**base, "status": "NON_MONOTONIC_TICK", "proposals": [],
                "next_state": state}
    observed = advise_local(telemetry, opt_in=True)
    if observed["status"] == "INVALID_TELEMETRY":
        return {**base, "status": "INVALID_TELEMETRY", "proposals": [],
                "next_state": state}
    retained = [dict(e) for e in state["recent"] if now-e["time"] < _WINDOW]
    emitted_ids = {e["id"] for e in retained}
    capacity = max(0, min(_MAX_PER_TICK, _MAX_PER_WINDOW-len(retained)))
    candidates = observed["suggestions"]
    new = [dict(e) for e in candidates if e["id"] not in emitted_ids][:capacity]
    next_recent = retained + [{"time": now, "id": e["id"]} for e in new]
    next_state = {"schema": _SCHEMA, "last_tick": now, "recent": next_recent}
    return {
        **base, "status": ("PROPOSALS_READY" if new else
                           "THROTTLED_OR_DUPLICATE" if candidates else "NO_ALERTS"),
        "proposals": new, "proposal_count": len(new),
        "suppressed_count": len(candidates) - len(new),
        "next_state": next_state,
        "max_per_window": _MAX_PER_WINDOW, "window_seconds": _WINDOW,
        "source": "UNVERIFIED_CALLER_SUPPLIED_TELEMETRY",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Offline proposal throttle (not NAS monitoring)")
    ap.add_argument("--telemetry-json", required=True)
    ap.add_argument("--now", type=int, required=True)
    ap.add_argument("--opt-in", action="store_true")
    args = ap.parse_args(argv)
    try:
        telemetry = json.loads(args.telemetry_json)
        result = evaluate_tick(telemetry, new_state(), args.now,
                               opted_in=args.opt_in)
    except (ValueError, TypeError):
        result = {"status": "INVALID_TELEMETRY", "release_gate": "HOLD"}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] in ("PROPOSALS_READY", "NO_ALERTS",
                                     "THROTTLED_OR_DUPLICATE", "DISABLED_NO_CONSENT") else 1


if __name__ == "__main__":
    raise SystemExit(main())
