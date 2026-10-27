"""G61: offline intake of operator-normalized file-agent observation receipts.

This is not a Uliya SDK client, not official Creator output, not a NAS
execution proof. The operator-normalized JSON is untrusted; even a fully
'confirmed' claim never produces LIVE_NAS_VERIFIED or READY.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from flowpilot.pipeline import evaluate_offline
from flowpilot.evidence import ObservationBatch, Observed, safe_path
from flowpilot.planner import draft_plan, State

FORMAT = "flowpilot-agent-observation-v1"
ORIGINS = {"SYNTHETIC_TEST", "OPERATOR_TRANSCRIBED_UNVERIFIED"}
ACTIONS = {"ug-filesystem ls", "ug-filesystem find", "ug-filesystem stat"}
RECEIPT_KEYS = {
    "schema", "origin", "goal", "authorized_root", "required_paths",
    "metadata_approved", "unknown_processing_accepted", "file_agent_report",
    "version_candidates",
}
AGENT_KEYS = {
    "agent", "operation", "authorized_root", "permission_confirmed",
    "registered_adapter_confirmed", "scan_complete",
    "pagination_complete", "failed", "observations",
}
ROW_KEYS = {"relative_path", "reference", "contained", "is_symlink"}
MAX_JSON_BYTES = 64 * 1024
REF_ID = re.compile(r"[A-Za-z0-9:/._-]{1,128}\Z")


class IntakeRefused(ValueError):
    """Do not include untrusted fields, paths or source contents in errors."""


def _exact_keys(value: Any, allowed: set[str], required: set[str]) -> None:
    if not isinstance(value, dict) or not required.issubset(value) or not set(value).issubset(allowed):
        raise IntakeRefused("Unexpected normalized receipt structure")


def _flag(row: Mapping[str, Any], key: str) -> bool:
    val = row[key]
    if type(val) is not bool:
        raise IntakeRefused("Non-boolean evidence or approval claim")
    return val


def _path(value: Any) -> str:
    try:
        return safe_path(value)
    except (ValueError, TypeError) as exc:
        raise IntakeRefused("Noncanonical or restricted relative path") from exc


def evaluate_normalized_receipt(payload: Any) -> dict:
    """Consume only a bounded transcribed metadata contract, never raw vendor JSON."""
    _exact_keys(payload, RECEIPT_KEYS, RECEIPT_KEYS - {"version_candidates"})
    if payload["schema"] != FORMAT or payload["origin"] not in ORIGINS:
        raise IntakeRefused("Unsupported observation format or origin")
    goal = payload["goal"]
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 2048:
        raise IntakeRefused("Invalid goal")
    required = payload["required_paths"]
    if (not isinstance(required, list) or not 1 <= len(required) <= 100
            or any(not isinstance(p, str) for p in required)):
        raise IntakeRefused("Invalid bounded checklist")
    cleaned = tuple(_path(p) for p in required)
    if len(set(cleaned)) != len(cleaned):
        raise IntakeRefused("Duplicate checklist entry")
    approved = _flag(payload, "metadata_approved")
    processing = _flag(payload, "unknown_processing_accepted")
    root = payload["authorized_root"]
    # The planner handles roots, write-intent refusal and consent questions.
    try:
        plan = draft_plan(goal, root, cleaned,
                          metadata_approved=approved,
                          unknown_processing_accepted=processing)
    except (ValueError, TypeError) as exc:
        raise IntakeRefused("Invalid approved root or goal") from exc
    versions = payload.get("version_candidates", {})
    if not isinstance(versions, dict) or len(versions) > 100 or set(versions) - set(cleaned):
        raise IntakeRefused("Version candidates outside approved checklist")
    clean_versions: dict[str, tuple[str, ...]] = {}
    for key, names in versions.items():
        if not isinstance(names, list) or len(names) > 20:
            raise IntakeRefused("Invalid version alternatives")
        v = tuple(_path(p) for p in names)
        if len(set(v)) != len(v):
            raise IntakeRefused("Repeated version candidate")
        clean_versions[key] = v
    agent = payload["file_agent_report"]
    _exact_keys(agent, AGENT_KEYS, AGENT_KEYS)
    if agent["agent"] != "file-agent" or agent["operation"] not in ACTIONS:
        raise IntakeRefused("Unrecognized reported registered expert or read action")
    if not isinstance(root, str) or agent["authorized_root"] != root:
        raise IntakeRefused("Reported scope is different from owner scope")
    claims = {name: _flag(agent, name) for name in (
        "permission_confirmed", "registered_adapter_confirmed", "scan_complete",
        "pagination_complete", "failed",
    )}
    rows = agent["observations"]
    if not isinstance(rows, list) or len(rows) > 100:
        raise IntakeRefused("Too many or invalid metadata observations")
    permitted = set(cleaned)
    for entries in clean_versions.values():
        permitted.update(entries)
    observations: list[Observed] = []
    unique: set[tuple[str, str]] = set()
    used_refs: dict[str, str] = {}
    for row in rows:
        _exact_keys(row, ROW_KEYS, ROW_KEYS)
        path = _path(row["relative_path"])
        if path not in permitted:
            raise IntakeRefused("Agent observation exceeds owner-approved scope")
        ref = row["reference"]
        if not isinstance(ref, str) or (ref and not REF_ID.fullmatch(ref)):
            raise IntakeRefused("Malformed observation reference")
        contained = row["contained"]
        if contained is not None and type(contained) is not bool:
            raise IntakeRefused("Untrusted containment flag")
        is_symlink = _flag(row, "is_symlink")
        if (path, ref) in unique:
            raise IntakeRefused("Duplicate observation record")
        unique.add((path, ref))
        if ref:
            if ref in used_refs and used_refs[ref] != path:
                raise IntakeRefused("Same reference attributed to different files")
            used_refs[ref] = path
        observations.append(Observed(path, ref, is_symlink, contained))
    batch = ObservationBatch(
        authorized_root=root,
        observations=tuple(observations),
        permission_confirmed=claims["permission_confirmed"],
        registered_adapter_confirmed=claims["registered_adapter_confirmed"],
        scan_complete=claims["scan_complete"],
        pagination_complete=claims["pagination_complete"],
        failed=claims["failed"],
    )
    # Never claim a real registered expert was actually invoked: the JSON is
    # operator-provided and can be forged. This evaluates assertions only.
    try:
        result = evaluate_offline(goal, root, cleaned,
                                  metadata_approved=approved,
                                  unknown_processing_accepted=processing,
                                  batch=batch, version_candidates=clean_versions)
    except (ValueError, TypeError) as exc:
        raise IntakeRefused("Normalized observation cannot be evaluated") from exc
    return {
        "mode": "UNTRUSTED_NORMALIZED_AGENT_RECEIPT_OFFLINE_ONLY",
        "origin_claim": payload["origin"],
        "normalized_schema": FORMAT,
        "goal_type": result.plan.intent.value if result.plan.intent else None,
        "status": result.status,
        "plan_state": plan.state.value,
        "read_action_claim": agent["operation"],
        "observed_record_count": len(observations),
        "item_results": [
            {"requirement_index": i + 1, "state": item.state.value,
             "reference_count": len(item.evidence)}
            for i, item in enumerate(result.report.items)
        ] if result.report else [],
        "limitations": list(result.limitations),
        "contains_raw_paths_refs_or_contents": False,
        "operator_claims_independently_verified": False,
        "official_registered_agent_invocation_verified": False,
        "real_nas_verified": False,
        "official_creator_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Offline G61 normalized Agent-receipt intake; NOT NAS")
    p.add_argument("--input", required=True, type=Path,
                   help="Local JSON prepared by operator; not a native Uliya API result")
    args = p.parse_args(argv)
    try:
        f = args.input
        if f.is_symlink() or f.parent.is_symlink() or not f.is_file() or not 0 < f.stat().st_size <= MAX_JSON_BYTES:
            raise IntakeRefused("Unsupported local receipt file")
        payload = json.loads(f.read_text(encoding="utf-8"))
        print(json.dumps(evaluate_normalized_receipt(payload), ensure_ascii=False, indent=2))
        return 0
    except (IntakeRefused, OSError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"status": "G61_INTAKE_REFUSED", "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
