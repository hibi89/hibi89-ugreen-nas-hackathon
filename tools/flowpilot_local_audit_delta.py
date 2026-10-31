"""G135: compare TWO completed owner-local G134 metadata audit snapshots.

Scope is re-derived using each run's stored unique salt. Evidence must pass
G134 structural integrity before state comparison. This does not inspect the
folder again, execute anything, or attest NAS/Expert safety. SQL read-only.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from flowpilot_local_audit_ledger import _ID, _TABLE, _read, _scope_digest
from flowpilot_owner_local_audit import OwnerAuditError, inspect_owner_folder
from flowpilot_persistent_qa import PersistentQARefused, _connect

_SCHEMA = "flowpilot-local-audit-delta-v1"
_ALLOWED_STATES = frozenset(("PRESENT", "MISSING", "VERSION_REVIEW", "NOT_CHECKED"))


def _base() -> dict:
    return {
        "schema": _SCHEMA, "release_gate": "HOLD",
        "owner_file_contents_opened": False, "owner_folder_inspected_again": False,
        "database_modified": False, "native_uliya_expert_invoked": False,
        "nas_verified": False, "production_applied": False,
        "external_api_called": False, "independently_notarized": False,
    }


def compare_local_audits(
    db_file: Path, previous_id: str, current_id: str, *,
    root: Path, required: list[str],
    candidates: dict[str, list[str]] | None = None,
    goal: str = "check required files",
) -> dict:
    """Read original G134 receipts in two transactions, never owner files.

    The exact same caller-supplied scope must reproduce EACH per-run salted
    digest. This prevents a comparison of two unrelated checklists.
    Scope values are never echoed or persisted here.
    """
    base = _base()
    if (type(previous_id) is not str or _ID.fullmatch(previous_id) is None
            or type(current_id) is not str or _ID.fullmatch(current_id) is None
            or previous_id == current_id):
        return {**base, "status": "INVALID_COMPARISON_RUN_IDS"}
    if (not isinstance(root, Path) or type(required) is not list
            or type(goal) is not str or type(candidates) not in (dict, type(None))):
        return {**base, "status": "INVALID_SCOPE"}
    versions = candidates if candidates is not None else {}
    # Consent-FALSE preflight checks exact scope and goal WITHOUT any owner
    # root/path metadata access. Reading the selected local DB is a separate
    # explicit operation authorized by the user-selected --db argument.
    try:
        preview = inspect_owner_folder(
            root, required, version_candidates=versions,
            goal=goal, metadata_consent=False,
        )
        if preview.get("status") != "WAITING_APPROVAL":
            return {**base, "status": "UNSUPPORTED_SCOPE_OR_GOAL"}
        with closing(_connect(db_file, mode="read")) as db:
            # Consistent read transaction; never run DDL or a write query.
            db.execute("BEGIN")
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (_TABLE,),
            ).fetchone()
            if exists is None:
                return {**base, "status": "NO_METADATA_RECORDS"}
            pairs = []
            for run_id in (previous_id, current_id):
                validated = _read(db, run_id)
                status = validated.get("status")
                if status == "NO_RUN_RECORD":
                    return {**base, "status": "SNAPSHOT_NOT_FOUND"}
                if status == "LOCAL_EVIDENCE_INVALID":
                    return {**base, "status": "EVIDENCE_INTEGRITY_INVALID"}
                if status == "PREVIOUS_RUN_INCOMPLETE_BLOCKED":
                    return {**base, "status": "INCOMPLETE_SNAPSHOT_BLOCKED"}
                if status != "READ_ONLY_LOCAL_METADATA_EVIDENCE" or not validated.get("local_observation_complete"):
                    return {**base, "status": "FAILED_OR_UNVERIFIED_SNAPSHOT_BLOCKED"}
                salt, stored_scope = db.execute(
                    "SELECT salt, scope_sha FROM fp134_metadata_runs WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if _scope_digest(salt, root=root, goal=goal,
                                 required=required, candidates=versions) != stored_scope:
                    return {**base, "status": "SNAPSHOT_SCOPE_MISMATCH"}
                pairs.append(validated)
            previous, current = pairs
            if (previous["item_count"] != current["item_count"]
                    or previous["item_count"] != len(required)
                    or len(previous["items"]) != len(current["items"])):
                return {**base, "status": "INCOMPATIBLE_SNAPSHOT_STRUCTURE"}
            changes: list[dict] = []
            new_missing, resolved_missing, new_uncertainty = 0, 0, 0
            for old, new in zip(previous["items"], current["items"]):
                if (type(old.get("index")) is not int
                        or old["index"] != new.get("index")
                        or old.get("state") not in _ALLOWED_STATES
                        or new.get("state") not in _ALLOWED_STATES):
                    return {**base, "status": "INCOMPATIBLE_SNAPSHOT_STRUCTURE"}
                if old["state"] != new["state"] or old["local_reference_count"] != new["local_reference_count"]:
                    changes.append({
                        "index": old["index"], "before": old["state"],
                        "after": new["state"],
                        "reference_count_before": old["local_reference_count"],
                        "reference_count_after": new["local_reference_count"],
                    })
                    if old["state"] != "MISSING" and new["state"] == "MISSING":
                        new_missing += 1
                    if old["state"] == "MISSING" and new["state"] == "PRESENT":
                        resolved_missing += 1
                    if old["state"] == "PRESENT" and new["state"] in ("NOT_CHECKED", "VERSION_REVIEW"):
                        new_uncertainty += 1
            return {
                **base, "status": "SNAPSHOT_DELTA_REVIEW_REQUIRED" if changes
                else "SNAPSHOTS_EQUAL_REVIEW_REQUIRED",
                "scope_match_verified_locally": True,
                "evidence_integrity": "LOCAL_CHAINS_INTACT_NOT_NOTARIZED",
                "previous_audit_result": previous["audit_result"],
                "current_audit_result": current["audit_result"],
                "item_count": len(required),
                "change_count": len(changes), "new_missing_count": new_missing,
                "resolved_missing_to_present_count": resolved_missing,
                "new_uncertainty_count": new_uncertainty,
                "changes": changes,
                "comparison_is_live_nas_state": False,
            }
    except (PersistentQARefused, OwnerAuditError, sqlite3.Error, OSError,
            TypeError, ValueError, OverflowError, KeyError):
        return {**base, "status": "LOCAL_SNAPSHOT_COMPARISON_REFUSED"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read-only same-scope local G134 snapshot delta, NOT NAS")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--previous-id", required=True)
    p.add_argument("--current-id", required=True)
    p.add_argument("--root", type=Path, required=True,
                   help="Exact previous audit scope, never accessed by this command")
    p.add_argument("--required", action="append", required=True)
    p.add_argument("--candidate", action="append", default=[],
                   help="required=candidate, repeatable")
    p.add_argument("--goal", default="check required files")
    args = p.parse_args(argv)
    candidates: dict[str, list[str]] = {}
    try:
        for pair in args.candidate:
            if "=" not in pair:
                raise ValueError("Invalid candidate pair")
            name, alternative = pair.split("=", 1)
            candidates.setdefault(name, []).append(alternative)
        result = compare_local_audits(
            args.db, args.previous_id, args.current_id,
            root=args.root, required=args.required,
            candidates=(candidates if args.candidate else None), goal=args.goal,
        )
    except (TypeError, ValueError):
        result = {**_base(), "status": "INVALID_SCOPE"}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] in (
        "SNAPSHOT_DELTA_REVIEW_REQUIRED", "SNAPSHOTS_EQUAL_REVIEW_REQUIRED"
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())