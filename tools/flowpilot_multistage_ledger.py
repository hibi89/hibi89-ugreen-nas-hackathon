"""G144: one durable, consented LOCAL multi-stage workflow receipt, not NAS.

Reuses G63/G64 vetted read-only recipe and G133 SQLite identity boundary.
A run ID is reserved BEFORE owner metadata reads. Interrupted runs cannot
silently repeat. Never stores raw owner paths, instructions, file names,
file contents or unsupported official execution claims.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3

from flowpilot_local_workflow import run_workflow
from flowpilot_text_workflow import parse_instructions, WorkflowRefused
from flowpilot_persistent_qa import _connect, PersistentQARefused

_SCHEMA = "flowpilot-local-multistage-ledger-v1"
_TABLE = "fp144_multistage_runs"
_RUN = re.compile(r"run_[A-Za-z0-9_-]{8,48}\Z")
_STATES = frozenset(("PRESENT", "MISSING", "VERSION_REVIEW", "NOT_CHECKED"))
_STEP_STATES = frozenset(("NEEDS_REVIEW", "BLOCKED", "NOT_CHECKED",
                          "WAITING_USER", "WAITING_APPROVAL"))
_TERMINAL = frozenset(("NEEDS_REVIEW", "BLOCKED", "LOCAL_WORKFLOW_FAILED"))


def _base() -> dict:
    return {"schema": _SCHEMA, "release_gate": "HOLD",
            "local_only": True, "raw_paths_returned": False,
            "owner_file_contents_opened": False,
            "native_uliya_expert_invoked": False, "nas_verified": False,
            "docker_executed": False, "production_applied": False,
            "external_api_called": False, "independently_notarized": False}


def _scope_hash(salt: str, root: Path, recipe: dict) -> str:
    bound = json.dumps([str(root), recipe], sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"))
    return hashlib.sha256((salt + bound).encode("utf-8")).hexdigest()


def _digest(run_id: str, salt: str, scope: str, state: str,
            planned: int, summary: list) -> str:
    blob = json.dumps([_SCHEMA, run_id, salt, scope, state, planned, summary],
                      separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def _setup(db: sqlite3.Connection) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS fp144_multistage_runs ("
               "run_id TEXT PRIMARY KEY,salt TEXT NOT NULL,"
               "scope_sha TEXT NOT NULL,state TEXT NOT NULL,"
               "planned INTEGER NOT NULL,summary_json TEXT NOT NULL,"
               "digest TEXT NOT NULL)")


def _safe_summary(row: dict, planned: int) -> tuple[str, list]:
    if (type(row) is not dict or row.get("status") not in ("NEEDS_REVIEW", "BLOCKED")
            or row.get("planned_steps") != planned
            or type(row.get("executed_steps")) is not int
            or not 1 <= row["executed_steps"] <= planned
            or row.get("owner_folder_contents_opened") is not False
            or row.get("raw_paths_returned") is not False
            or row.get("nas_verified") is not False
            or row.get("uliya_agent_invoked") is not False
            or row.get("release_gate") != "HOLD"):
        return "LOCAL_WORKFLOW_FAILED", []
    steps = row.get("steps")
    if type(steps) is not list or len(steps) != row["executed_steps"]:
        return "LOCAL_WORKFLOW_FAILED", []
    summary = []
    for index, step in enumerate(steps, 1):
        if (type(step) is not dict
                or set(step) != {"index", "status", "items", "inspected_local_metadata"}
                or type(step["index"]) is not int or step["index"] != index
                or step["status"] not in _STEP_STATES
                or type(step["inspected_local_metadata"]) is not bool):
            return "LOCAL_WORKFLOW_FAILED", []
        items = step["items"]
        if (type(items) is not list or len(items) > 100
                or (step["inspected_local_metadata"] and not items)):
            return "LOCAL_WORKFLOW_FAILED", []
        normalized = []
        for item_index, item in enumerate(items, 1):
            if (type(item) is not dict
                    or set(item) != {"index", "state", "local_reference_count"}
                    or type(item["index"]) is not int or item["index"] != item_index
                    or item["state"] not in _STATES
                    or type(item["local_reference_count"]) is not int
                    or not 0 <= item["local_reference_count"] <= 20):
                return "LOCAL_WORKFLOW_FAILED", []
            normalized.append([item_index, item["state"], item["local_reference_count"]])
        summary.append([index, step["status"], normalized])
    if (row["status"] == "NEEDS_REVIEW"
            and any(item[1] == "MISSING" for stage in summary for item in stage[2])):
        return "LOCAL_WORKFLOW_FAILED", []
    if row["status"] == "BLOCKED" and summary[-1][1] not in (
            "BLOCKED", "NOT_CHECKED", "WAITING_USER", "WAITING_APPROVAL"):
        return "LOCAL_WORKFLOW_FAILED", []
    if row["status"] == "NEEDS_REVIEW" and summary[-1][1] != "NEEDS_REVIEW":
        return "LOCAL_WORKFLOW_FAILED", []
    return row["status"], summary


def _read(db: sqlite3.Connection, run_id: str) -> dict:
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                  (_TABLE,)).fetchone() is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    row = db.execute("SELECT salt,scope_sha,state,planned,summary_json,digest "
                     "FROM fp144_multistage_runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    salt, scope, state, planned, raw, digest = row
    try:
        summary = json.loads(raw)
        valid = (type(salt) is str and re.fullmatch("[0-9a-f]{32}", salt) is not None
                 and type(scope) is str and re.fullmatch("[0-9a-f]{64}", scope) is not None
                 and type(digest) is str and re.fullmatch("[0-9a-f]{64}", digest) is not None
                 and type(planned) is int and 1 <= planned <= 8
                 and state in _TERMINAL | {"IN_PROGRESS"}
                 and type(summary) is list and len(summary) <= planned
                 and (state not in ("IN_PROGRESS", "LOCAL_WORKFLOW_FAILED") or not summary)
                 and (state not in ("BLOCKED", "NEEDS_REVIEW") or bool(summary))
                 and _digest(run_id, salt, scope, state, planned, summary) == digest)
        if valid:
            if state in ("BLOCKED", "NEEDS_REVIEW"):
                pseudo = {"status": state, "planned_steps": planned,
                          "executed_steps": len(summary),
                          "owner_folder_contents_opened": False,
                          "raw_paths_returned": False, "nas_verified": False,
                          "uliya_agent_invoked": False, "release_gate": "HOLD",
                          "steps": []}
                for index, stage in enumerate(summary, 1):
                    if (type(stage) is not list or len(stage) != 3
                            or type(stage[0]) is not int or stage[0] != index
                            or stage[1] not in _STEP_STATES
                            or type(stage[2]) is not list):
                        valid = False
                        break
                    items = [{"index": x[0], "state": x[1], "local_reference_count": x[2]}
                             for x in stage[2] if type(x) is list and len(x) == 3]
                    if len(items) != len(stage[2]):
                        valid = False
                        break
                    pseudo["steps"].append({"index": index, "status": stage[1],
                                            "items": items,
                                            "inspected_local_metadata": bool(items)})
                if valid and _safe_summary(pseudo, planned) != (state, summary):
                    valid = False
    except (ValueError, TypeError, UnicodeError, OverflowError, KeyError, IndexError):
        valid = False
        summary = []
    if not valid:
        return {"status": "LOCAL_EVIDENCE_INVALID", "evidence_integrity": "LOCAL_CHAIN_INVALID"}
    if state == "IN_PROGRESS":
        return {"status": "PREVIOUS_RUN_INCOMPLETE_BLOCKED",
                "evidence_integrity": "LOCAL_CHAIN_INTACT"}
    if state == "LOCAL_WORKFLOW_FAILED":
        return {"status": "STORED_LOCAL_WORKFLOW_FAILED",
                "evidence_integrity": "LOCAL_CHAIN_INTACT",
                "planned_steps": planned, "executed_steps": 0}
    return {"status": "READ_ONLY_LOCAL_WORKFLOW_EVIDENCE",
            "evidence_integrity": "LOCAL_CHAIN_INTACT_NOT_NOTARIZED",
            "audit_result": state, "planned_steps": planned,
            "executed_steps": len(summary),
            "steps": [{"index": stage[0], "status": stage[1],
                       "items": [{"index": x[0], "state": x[1],
                                  "local_reference_count": x[2]} for x in stage[2]]}
                      for stage in summary]}


def run_recorded_local_workflow(db_file: Path, run_id: str, *,
                                mode: str, instructions: str | None = None,
                                root: Path | None = None,
                                approve_local_metadata: bool = False,
                                approve_local_db_write: bool = False) -> dict:
    base = _base()
    if type(run_id) is not str or _RUN.fullmatch(run_id) is None:
        return {**base, "status": "INVALID_RUN_ID"}
    if mode not in ("new", "append", "read"):
        return {**base, "status": "INVALID_DB_MODE"}
    if (type(approve_local_metadata) is not bool
            or type(approve_local_db_write) is not bool):
        return {**base, "status": "INVALID_CONSENT"}
    if mode == "read":
        if (instructions is not None or root is not None
                or approve_local_metadata or approve_local_db_write):
            return {**base, "status": "READ_HAS_UNEXPECTED_OPTIONS"}
        try:
            with closing(_connect(db_file, mode="read")) as db:
                return {**base, **_read(db, run_id), "database_modified": False}
        except (PersistentQARefused, sqlite3.Error, OSError, TypeError, ValueError):
            return {**base, "status": "LOCAL_DB_REFUSED"}
    # No selected SQLite file or owner directory can be accessed before BOTH approvals.
    if not (approve_local_metadata and approve_local_db_write):
        return {**base, "status": "WAITING_TWO_SEPARATE_LOCAL_APPROVALS"}
    if type(instructions) is not str or not isinstance(root, Path):
        return {**base, "status": "INVALID_SCOPE"}
    try:
        recipe = parse_instructions(instructions)
        approval_preview = run_workflow(root, recipe, metadata_consent=False)
        if approval_preview.get("status") != "WAITING_APPROVAL":
            return {**base, "status": "UNSUPPORTED_SCOPE_OR_RECIPE"}
        planned = len(recipe["steps"])
        with closing(_connect(db_file, mode=mode)) as db:
            _setup(db)
            db.execute("BEGIN IMMEDIATE")
            try:
                previous = db.execute("SELECT salt,scope_sha FROM fp144_multistage_runs "
                                      "WHERE run_id=?", (run_id,)).fetchone()
                if previous is not None:
                    integrity = _read(db, run_id)
                    if integrity["status"] == "LOCAL_EVIDENCE_INVALID":
                        state = "PRIOR_LOCAL_EVIDENCE_INVALID"
                    elif integrity["status"] == "PREVIOUS_RUN_INCOMPLETE_BLOCKED":
                        state = "PREVIOUS_RUN_INCOMPLETE_BLOCKED"
                    else:
                        state = ("DUPLICATE_BLOCKED"
                                 if _scope_hash(previous[0], root, recipe) == previous[1]
                                 else "RUN_ID_SCOPE_CONFLICT")
                    db.commit()
                    return {**base, "status": state, "database_modified": False,
                            "owner_folder_inspected_again": False}
                salt = secrets.token_hex(16)
                scope = _scope_hash(salt, root, recipe)
                initial = _digest(run_id, salt, scope, "IN_PROGRESS", planned, [])
                db.execute("INSERT INTO fp144_multistage_runs VALUES(?,?,?,?,?,?,?)",
                           (run_id, salt, scope, "IN_PROGRESS", planned, "[]", initial))
                db.commit()
            except BaseException:
                db.rollback()
                raise
            try:
                result = run_workflow(root, recipe, metadata_consent=True)
                state, summary = _safe_summary(result, planned)
            except (WorkflowRefused, ValueError, TypeError, OSError, KeyError):
                state, summary = "LOCAL_WORKFLOW_FAILED", []
            db.execute("BEGIN IMMEDIATE")
            try:
                digest = _digest(run_id, salt, scope, state, planned, summary)
                db.execute("UPDATE fp144_multistage_runs SET state=?,summary_json=?,"
                           "digest=? WHERE run_id=? AND state='IN_PROGRESS'",
                           (state, json.dumps(summary, ensure_ascii=True,
                                              separators=(",", ":")), digest, run_id))
                if db.execute("SELECT changes()").fetchone()[0] != 1:
                    raise PersistentQARefused("CONCURRENT_RUN_CHANGED")
                db.commit()
            except BaseException:
                db.rollback()
                raise
            verified = _read(db, run_id)
            if verified["status"] not in ("READ_ONLY_LOCAL_WORKFLOW_EVIDENCE",
                                           "STORED_LOCAL_WORKFLOW_FAILED"):
                return {**base, "status": "LOCAL_EVIDENCE_INVALID",
                        "database_modified": True}
            public_status = ("LOCAL_WORKFLOW_REVIEW_STORED" if state == "NEEDS_REVIEW"
                             else "LOCAL_WORKFLOW_BLOCKED_STORED" if state == "BLOCKED"
                             else "LOCAL_WORKFLOW_FAILED_STORED")
            return {**base, "status": public_status, "database_modified": True,
                    "planned_steps": planned,
                    "executed_steps": len(summary),
                    "audit_result": state,
                    "evidence_integrity": verified["evidence_integrity"]}
    except (PersistentQARefused, WorkflowRefused, sqlite3.Error,
            OSError, TypeError, ValueError, OverflowError):
        return {**base, "status": "LOCAL_WORKFLOW_LEDGER_REFUSED"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LOCAL multi-stage SQLite audit; NOT Uliya/NAS")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--mode", required=True, choices=("new", "append", "read"))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--instructions")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--approve-local-metadata", action="store_true")
    ap.add_argument("--approve-local-db-write", action="store_true")
    args = ap.parse_args(argv)
    report = run_recorded_local_workflow(
        args.db, args.run_id, mode=args.mode, instructions=args.instructions,
        root=args.root, approve_local_metadata=args.approve_local_metadata,
        approve_local_db_write=args.approve_local_db_write)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report["status"] in (
        "LOCAL_WORKFLOW_REVIEW_STORED", "READ_ONLY_LOCAL_WORKFLOW_EVIDENCE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
