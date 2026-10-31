"""G138: read-only, same-scope review of ONE completed G134 LOCAL snapshot.

This never scans the owner folder, opens file contents, calls Uliya/NAS/Docker,
or promotes local evidence to an official release. The per-run scope digest
is independently re-derived from the caller's exact original checklist.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from flowpilot_local_audit_ledger import _ID, _TABLE, _read, _scope_digest
from flowpilot_owner_local_audit import OwnerAuditError, inspect_owner_folder
from flowpilot_persistent_qa import PersistentQARefused, _connect

_SCHEMA = "flowpilot-local-snapshot-review-v1"


def inspect_local_snapshot(
    db_file: Path, run_id: str, *, root: Path, required: list[str],
    candidates: dict[str, list[str]] | None = None,
    goal: str = "check required files",
) -> dict:
    """Inspect already-stored LOCAL evidence only, fail closed on any mismatch."""
    base = {
        "schema": _SCHEMA, "release_gate": "HOLD",
        "database_modified": False, "local_only": True,
        "owner_folder_inspected_again": False,
        "owner_file_contents_opened": False, "raw_paths_returned": False,
        "nas_verified": False, "native_uliya_expert_invoked": False,
        "docker_executed": False, "production_applied": False,
        "external_api_called": False, "independently_notarized": False,
    }
    if type(run_id) is not str or _ID.fullmatch(run_id) is None:
        return {**base, "status": "INVALID_SNAPSHOT_RUN_ID"}
    if (not isinstance(root, Path) or type(required) is not list
            or type(goal) is not str
            or type(candidates) not in (dict, type(None))):
        return {**base, "status": "INVALID_SCOPE"}
    versions = {} if candidates is None else candidates
    try:
        preflight = inspect_owner_folder(
            root, required, version_candidates=versions,
            goal=goal, metadata_consent=False,
        )
        if preflight.get("status") != "WAITING_APPROVAL":
            return {**base, "status": "UNSUPPORTED_SCOPE_OR_GOAL"}
        with closing(_connect(db_file, mode="read")) as db:
            db.execute("BEGIN")
            validated = _read(db, run_id)
            if validated["status"] == "NO_RUN_RECORD":
                return {**base, "status": "SNAPSHOT_NOT_FOUND"}
            if validated["status"] == "LOCAL_EVIDENCE_INVALID":
                return {**base, "status": "EVIDENCE_INTEGRITY_INVALID"}
            if validated["status"] == "PREVIOUS_RUN_INCOMPLETE_BLOCKED":
                return {**base, "status": "INCOMPLETE_SNAPSHOT_BLOCKED"}
            if (validated["status"] != "READ_ONLY_LOCAL_METADATA_EVIDENCE"
                    or validated.get("local_observation_complete") is not True):
                return {**base, "status": "FAILED_OR_UNVERIFIED_SNAPSHOT_BLOCKED"}
            row = db.execute(
                "SELECT salt, scope_sha FROM " + _TABLE + " WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if row is None:
                return {**base, "status": "SNAPSHOT_NOT_FOUND"}
            if _scope_digest(row[0], root=root, goal=goal,
                             required=required, candidates=versions) != row[1]:
                return {**base, "status": "SNAPSHOT_SCOPE_MISMATCH"}
            items = validated["items"]
            if len(items) != len(required):
                return {**base, "status": "INCOMPATIBLE_SNAPSHOT_STRUCTURE"}
            return {
                **base, "status": "LOCAL_SNAPSHOT_REVIEW_REQUIRED",
                "scope_match_verified_locally": True,
                "evidence_integrity": "LOCAL_CHAIN_INTACT_NOT_NOTARIZED",
                "item_count": validated["item_count"],
                "audit_result": validated["audit_result"],
                "items": items,
                "comparison_is_live_nas_state": False,
            }
    except (PersistentQARefused, OwnerAuditError, sqlite3.Error, OSError,
            TypeError, ValueError, OverflowError, KeyError):
        return {**base, "status": "LOCAL_SNAPSHOT_REVIEW_REFUSED"}
