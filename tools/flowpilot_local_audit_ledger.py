"""G134: durable, consent-gated REAL LOCAL filesystem-metadata audit receipts.

Reads only exact owner-selected local file metadata via the existing G62 reader.
Separate from G119 synthetic QA: this never invokes NAS, Uliya, Docker,
LLMs, network, code generation or actual deployment. No file contents or
raw owner root/path/goal are written to the DB or returned to the caller.

SQLite digests are accidental-tamper checks, NOT external notarization.
Do not use with an untrusted concurrently modified filesystem or NAS mount.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
from contextlib import closing

from flowpilot_owner_local_audit import inspect_owner_folder, OwnerAuditError
from flowpilot_persistent_qa import _connect, PersistentQARefused

_SCHEMA = "flowpilot-local-audit-ledger-v1"
_ID = re.compile(r"run_[A-Za-z0-9_-]{8,48}\Z")
_STATES = frozenset(("PRESENT", "MISSING", "VERSION_REVIEW", "NOT_CHECKED"))
_TERMINALS = frozenset(("NEEDS_REVIEW", "BLOCKED", "LOCAL_AUDIT_FAILED"))
_TABLE = "fp134_metadata_runs"


def _base() -> dict:
    return {"schema": _SCHEMA, "release_gate": "HOLD",
            "local_metadata_only": True, "owner_file_contents_opened": False,
            "native_uliya_expert_invoked": False, "nas_verified": False,
            "actual_docker_executed": False, "production_applied": False,
            "database_independently_notarized": False, "external_api_called": False}


def _scope_digest(salt: str, *, root: Path, goal: str, required: list[str],
                  candidates: dict[str, list[str]]) -> str:
    # A per-run random salt limits cross-database stable correlations. This
    # checksum is NOT encryption or secure against a database reader guessing
    # common file names; the owner-selected DB remains private local data.
    value = json.dumps({"root": str(root), "goal": goal, "required": required,
                        "candidates": candidates}, ensure_ascii=True,
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((salt + value).encode("utf-8")).hexdigest()


def _digest(run_id: str, salt: str, scope_sha: str, state: str, summary: list) -> str:
    value = json.dumps([_SCHEMA, run_id, salt, scope_sha, state, summary],
                       ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _setup(db: sqlite3.Connection) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS fp134_metadata_runs ("
               "run_id TEXT PRIMARY KEY, salt TEXT NOT NULL, "
               "scope_sha TEXT NOT NULL, state TEXT NOT NULL, "
               "summary_json TEXT NOT NULL, digest TEXT NOT NULL)")


def _read(db: sqlite3.Connection, run_id: str) -> dict:
    existing = db.execute("SELECT name FROM sqlite_master WHERE type='table' "
                          "AND name=?", (_TABLE,)).fetchone()
    if existing is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    row = db.execute("SELECT salt,scope_sha,state,summary_json,digest "
                     "FROM fp134_metadata_runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    salt, scope_sha, state, raw_summary, digest = row
    try:
        summary = json.loads(raw_summary)
        valid = (type(salt) is str and bool(re.fullmatch(r"[0-9a-f]{32}", salt))
                 and type(scope_sha) is str and bool(re.fullmatch(r"[0-9a-f]{64}", scope_sha))
                 and type(digest) is str and bool(re.fullmatch(r"[0-9a-f]{64}", digest))
                 and state in _TERMINALS | {"IN_PROGRESS"}
                 and type(summary) is list and len(summary) <= 100
                 and all(type(item) is list and len(item) == 3
                         and type(item[0]) is int and item[0] == i
                         and item[1] in _STATES and type(item[2]) is int
                         and 0 <= item[2] <= 20
                         for i, item in enumerate(summary, 1))
                 and (state not in ("IN_PROGRESS", "LOCAL_AUDIT_FAILED") or not summary)
                 and (state not in ("NEEDS_REVIEW", "BLOCKED") or bool(summary))
                 and (state != "NEEDS_REVIEW" or not any(x[1] == "MISSING" for x in summary))
                 and (state != "BLOCKED" or any(x[1] == "MISSING" for x in summary))
                 and _digest(run_id, salt, scope_sha, state, summary) == digest)
    except (TypeError, ValueError, UnicodeError, OverflowError):
        valid = False
        summary = []
    if not valid:
        return {"status": "LOCAL_EVIDENCE_INVALID", "evidence_integrity": "LOCAL_CHAIN_INVALID"}
    if state == "IN_PROGRESS":
        return {"status": "PREVIOUS_RUN_INCOMPLETE_BLOCKED",
                "evidence_integrity": "LOCAL_CHAIN_INTACT", "local_observation_complete": False}
    return {"status": "READ_ONLY_LOCAL_METADATA_EVIDENCE",
            "evidence_integrity": "LOCAL_CHAIN_INTACT",
            "local_observation_complete": state in ("NEEDS_REVIEW", "BLOCKED"),
            "audit_result": state, "item_count": len(summary),
            "items": [{"index": idx, "state": item_state, "local_reference_count": count}
                      for idx, item_state, count in summary]}


def _summary(row: dict, required_count: int) -> tuple[str, list]:
    """Never persist caller labels, paths, messages or other untrusted keys."""
    if (type(row) is not dict or row.get("status") not in ("NEEDS_REVIEW", "BLOCKED")
            or row.get("item_count") != required_count
            or row.get("inspected_local_metadata") is not True
            or row.get("file_contents_opened") is not False
            or row.get("nas_verified") is not False
            or row.get("registered_uliya_agent_invoked") is not False):
        return "LOCAL_AUDIT_FAILED", []
    items = row.get("items")
    if (type(items) is not list or len(items) != required_count or
            any(type(item) is not dict
                or set(item) != {"index", "state", "local_reference_count"}
                or type(item["index"]) is not int or item["index"] != index
                or item["state"] not in _STATES
                or type(item["local_reference_count"]) is not int
                or not 0 <= item["local_reference_count"] <= 20
                for index, item in enumerate(items, 1))):
        return "LOCAL_AUDIT_FAILED", []
    has_missing = any(x["state"] == "MISSING" for x in items)
    if (row["status"] == "BLOCKED") != has_missing:
        return "LOCAL_AUDIT_FAILED", []
    return row["status"], [[x["index"], x["state"], x["local_reference_count"]]
                            for x in items]


def run_local_audit_ledger(db_file: Path, run_id: str, *, mode: str,
                           root: Path | None = None, required: list[str] | None = None,
                           candidates: dict[str, list[str]] | None = None,
                           goal: str = "check required files",
                           approve_local_metadata: bool = False,
                           approve_local_db_write: bool = False) -> dict:
    """One run ID, at-most-once local metadata read; explicit two consents.

    Writes reserve a run ID before reading the chosen local folder. If the
    process crashes mid-scan, the reserved ID remains incomplete and cannot
    be silently retried; the user must inspect/review and choose a new ID.
    """
    base = _base()
    if type(run_id) is not str or _ID.fullmatch(run_id) is None:
        return {**base, "status": "INVALID_RUN_ID"}
    if mode not in ("new", "append", "read"):
        return {**base, "status": "INVALID_DB_MODE"}
    if type(approve_local_metadata) is not bool or type(approve_local_db_write) is not bool:
        return {**base, "status": "INVALID_CONSENT"}
    if mode == "read":
        if (root is not None or required is not None or candidates is not None
                or approve_local_metadata or approve_local_db_write):
            return {**base, "status": "READ_MODE_HAS_UNEXPECTED_SCOPE_OR_CONSENT"}
        try:
            with closing(_connect(db_file, mode="read")) as db:
                return {**base, **_read(db, run_id), "database_modified": False}
        except (PersistentQARefused, sqlite3.Error, OSError, TypeError, ValueError):
            return {**base, "status": "LOCAL_DB_REFUSED"}
    # Denial before ANY user-chosen disk reads, including the selected DB.
    if not (approve_local_metadata and approve_local_db_write):
        return {**base, "status": "WAITING_TWO_SEPARATE_LOCAL_APPROVALS"}
    if (not isinstance(root, Path) or type(required) is not list
            or type(goal) is not str or type(candidates) not in (dict, type(None))):
        return {**base, "status": "INVALID_SCOPE"}
    versions = candidates if candidates is not None else {}
    try:
        preflight = inspect_owner_folder(root, required,
                                         version_candidates=versions,
                                         goal=goal, metadata_consent=False)
        if preflight["status"] != "WAITING_APPROVAL":
            return {**base, "status": "BLOCKED_UNSUPPORTED_SCOPE_OR_GOAL"}
        with closing(_connect(db_file, mode=mode)) as db:
            _setup(db)
            db.execute("BEGIN IMMEDIATE")
            try:
                existing = db.execute(
                    "SELECT salt,scope_sha FROM fp134_metadata_runs WHERE run_id=?",
                    (run_id,)).fetchone()
                if existing is not None:
                    seen = _read(db, run_id)
                    if seen["status"] == "LOCAL_EVIDENCE_INVALID":
                        status = "PRIOR_LOCAL_EVIDENCE_INVALID"
                    elif seen["status"] == "PREVIOUS_RUN_INCOMPLETE_BLOCKED":
                        status = "PREVIOUS_RUN_INCOMPLETE_BLOCKED"
                    else:
                        status = ("DUPLICATE_BLOCKED" if
                                  _scope_digest(existing[0], root=root, goal=goal,
                                                required=required, candidates=versions)
                                  == existing[1] else "RUN_ID_SCOPE_CONFLICT")
                    db.commit()
                    return {**base, "status": status, "database_modified": False,
                            "local_folder_inspected_again": False}
                salt = secrets.token_hex(16)
                scope_sha = _scope_digest(salt, root=root, goal=goal,
                                          required=required, candidates=versions)
                initial_digest = _digest(run_id, salt, scope_sha, "IN_PROGRESS", [])
                db.execute("INSERT INTO fp134_metadata_runs VALUES(?,?,?,?,?,?)",
                           (run_id, salt, scope_sha, "IN_PROGRESS", "[]", initial_digest))
                db.commit()
            except BaseException:
                db.rollback()
                raise
            try:
                observed = inspect_owner_folder(root, required,
                                                version_candidates=versions,
                                                goal=goal, metadata_consent=True)
                state, summary = _summary(observed, len(required))
            except (OwnerAuditError, OSError, TypeError, ValueError):
                state, summary = "LOCAL_AUDIT_FAILED", []
            summary_json = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
            digest = _digest(run_id, salt, scope_sha, state, summary)
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("UPDATE fp134_metadata_runs SET state=?, summary_json=?, digest=? "
                           "WHERE run_id=? AND state='IN_PROGRESS'",
                           (state, summary_json, digest, run_id))
                if db.execute("SELECT changes()").fetchone()[0] != 1:
                    raise PersistentQARefused("CONCURRENT_RUN_CHANGED")
                db.commit()
            except BaseException:
                db.rollback()
                raise
            checked = _read(db, run_id)
            if checked["status"] != "READ_ONLY_LOCAL_METADATA_EVIDENCE":
                return {**base, "status": "LOCAL_EVIDENCE_INVALID", "database_modified": True}
            status = ("LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED" if state == "NEEDS_REVIEW"
                      else "LOCAL_METADATA_BLOCKED_EVIDENCE_STORED" if state == "BLOCKED"
                      else "LOCAL_METADATA_CHECK_FAILED_EVIDENCE_STORED")
            return {**base, "status": status, "local_metadata_check_attempted": True,
                    "local_metadata_check_completed": state != "LOCAL_AUDIT_FAILED",
                    "database_modified": True, "evidence_integrity": checked["evidence_integrity"],
                    "item_count": checked["item_count"], "audit_result": checked["audit_result"]}
    except (PersistentQARefused, OwnerAuditError, sqlite3.Error, OSError,
            TypeError, ValueError, OverflowError):
        return {**base, "status": "LOCAL_AUDIT_LEDGER_REFUSED"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consented LOCAL metadata and durable receipt; NOT NAS")
    parser.add_argument("--db", type=Path, required=True, help="Absolute local NEW or existing G133 .sqlite")
    parser.add_argument("--mode", required=True, choices=("new", "append", "read"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--required", action="append")
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--goal", default="check required files")
    parser.add_argument("--approve-local-metadata", action="store_true")
    parser.add_argument("--approve-local-db-write", action="store_true")
    args = parser.parse_args(argv)
    candidates: dict[str, list[str]] = {}
    try:
        for pair in args.candidate:
            if "=" not in pair:
                raise ValueError("invalid bounded candidate")
            key, value = pair.split("=", 1)
            candidates.setdefault(key, []).append(value)
        if args.mode == "read" and args.candidate:
            result = {**_base(), "status": "READ_MODE_HAS_UNEXPECTED_SCOPE_OR_CONSENT"}
        else:
            result = run_local_audit_ledger(
                args.db, args.run_id, mode=args.mode, root=args.root,
                required=args.required, candidates=(candidates if args.candidate else None),
                goal=args.goal, approve_local_metadata=args.approve_local_metadata,
                approve_local_db_write=args.approve_local_db_write)
    except (TypeError, ValueError):
        result = {**_base(), "status": "INVALID_SCOPE"}
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result["status"] in (
        "LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED",
        "READ_ONLY_LOCAL_METADATA_EVIDENCE", "NO_RUN_RECORD") else 2


if __name__ == "__main__":
    raise SystemExit(main())
