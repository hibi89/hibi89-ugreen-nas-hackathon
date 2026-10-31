"""G117 offline proactive NAS *suggestion* engine over supplied test telemetry.

No polling, timers, filesystem reads, agents, background service, privileges,
notification sends, automatic fixes or genuine NAS metrics. Defaults disabled.
"""
from __future__ import annotations

import argparse
import json


_FIELDS = frozenset({"disk_used_percent", "repeated_error_count", "backup_age_hours"})
_THRESHOLDS = (
    ("disk_used_percent", 90, "REVIEW_DISK_CAPACITY",
     "Disk usage is above the configured review threshold."),
    ("repeated_error_count", 3, "REVIEW_REPEATED_ERRORS",
     "Repeated error signals warrant a human log review."),
    ("backup_age_hours", 72, "REVIEW_BACKUP_FRESHNESS",
     "A stale backup age warrants a backup policy review."),
)


def advise_local(telemetry: dict, *, opt_in: bool = False) -> dict:
    """Produce read-only, human-approval-required recommendations."""
    base = {
        "schema": "flowpilot-proactive-suggestions-v1",
        "source": "UNVERIFIED_OPERATOR_SUPPLIED_METRICS",
        "nas_polled": False, "background_service_started": False,
        "telemetry_verified": False, "actions_executed": False,
        "external_notifications_sent": False, "release_gate": "HOLD",
    }
    if type(opt_in) is not bool:
        return {**base, "status": "INVALID_CONSENT", "suggestions": []}
    if not opt_in:
        return {**base, "status": "DISABLED_NO_CONSENT", "suggestions": []}
    if type(telemetry) is not dict or not telemetry or set(telemetry) - _FIELDS:
        return {**base, "status": "INVALID_TELEMETRY", "suggestions": []}
    if any(type(value) is not int or value < 0 or
           (key == "disk_used_percent" and value > 100) or
           (key != "disk_used_percent" and value > 87600)
           for key, value in telemetry.items()):
        return {**base, "status": "INVALID_TELEMETRY", "suggestions": []}
    suggestions = [
        {"id": name, "message": message,
         "status": "PROPOSAL_ONLY",
         "requires_explicit_user_approval_to_act": True,
         "verified_on_real_nas": False}
        for field, threshold, name, message in _THRESHOLDS
        if field in telemetry and telemetry[field] >= threshold
    ]
    return {
        **base, "status": "SUGGESTIONS_READY" if suggestions else "NO_ALERTS_IN_SUPPLIED_DATA",
        "evaluated_fields": sorted(telemetry),
        "suggestions": suggestions, "suggestion_count": len(suggestions),
        "missing_inputs_not_checked": sorted(_FIELDS - set(telemetry)),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Offline consent-gated proposal engine; NOT NAS")
    p.add_argument("--telemetry-json", required=True, help="Synthetic local telemetry JSON")
    p.add_argument("--opt-in", action="store_true")
    args = p.parse_args(argv)
    try:
        telemetry = json.loads(args.telemetry_json)
    except ValueError:
        telemetry = None
    result = advise_local(telemetry, opt_in=args.opt_in)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] in ("DISABLED_NO_CONSENT", "SUGGESTIONS_READY",
                                     "NO_ALERTS_IN_SUPPLIED_DATA") else 1


if __name__ == "__main__":
    raise SystemExit(main())
