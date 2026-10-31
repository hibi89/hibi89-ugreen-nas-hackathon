"""G119: append-only evidence and replay barrier for synthetic FlowPilot runs.

Caller owns a local sqlite3.Connection. No NAS access, network, Docker,
persistent user files or arbitrary generated code. Entries describe
deterministic template review + disposable fixture tests, NOT production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import tempfile
from pathlib import Path

from flowpilot_code_council import run_council
from flowpilot_task_compiler import compile_goal

_ID = re.compile(r"run_[A-Za-z0-9_-]{8,48}\Z")
_ROLES = frozenset(("Architect", "Security", "Builder", "Repair", "QA"))
_STATES = frozenset(("PASS", "REJECTED"))
_SCHEMA = "flowpilot-evidence-ledger-v1"


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()


def _setup(db: sqlite3.Connection) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS fp119_runs ("
               "run_id TEXT PRIMARY KEY, goal_sha TEXT NOT NULL, "
               "status TEXT NOT NULL, final_sha TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS fp119_events ("
               "run_id TEXT NOT NULL, seq INTEGER NOT NULL, kind TEXT NOT NULL, "
               "detail TEXT NOT NULL, previous_sha TEXT NOT NULL, event_sha TEXT NOT NULL, "
               "PRIMARY KEY(run_id, seq))")


def _append(db: sqlite3.Connection, run_id: str, kind: str, detail: dict) -> str:
    last = db.execute(
        "SELECT seq, event_sha FROM fp119_events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
        (run_id,)
    ).fetchone()
    seq, prev = (last[0] + 1, last[1]) if last else (1, "0" * 64)
    record = {"run_id": run_id, "seq": seq, "kind": kind,
              "detail": detail, "previous_sha": prev}
    digest = _sha(record)
    db.execute("INSERT INTO fp119_events VALUES(?,?,?,?,?,?)",
               (run_id, seq, kind, json.dumps(detail, sort_keys=True), prev, digest))
    return digest


def run_once(goal: str, run_id: str, db: sqlite3.Connection, *,
             inject_test_fault: bool = False, max_repairs: int = 1) -> dict:
    """Reserve run ID transactionally before launching synthetic fixtures."""
    if type(run_id) is not str or _ID.fullmatch(run_id) is None:
        raise ValueError("Invalid opaque synthetic run ID")
    if not isinstance(db, sqlite3.Connection) or db.in_transaction:
        raise ValueError("Independent SQLite connection required")
    if type(inject_test_fault) is not bool or type(max_repairs) is not int or max_repairs not in (0, 1):
        raise ValueError("Invalid repair settings")
    plan = compile_goal(goal)
    if plan.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return {"schema": _SCHEMA, "status": "UNSUPPORTED_GOAL", "executed": False,
                "nas_verified": False, "release_gate": "HOLD"}
    goal_sha = _sha({"template": plan["template"], "goal": plan["goal"]})
    _setup(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        prior = db.execute("SELECT goal_sha, status FROM fp119_runs WHERE run_id=?",
                           (run_id,)).fetchone()
        if prior is not None:
            db.commit()
            return {"schema": _SCHEMA,
                    "status": "DUPLICATE_BLOCKED" if prior[0] == goal_sha
                              else "RUN_ID_GOAL_CONFLICT",
                    "previous_status": prior[1], "executed": False,
                    "nas_verified": False, "release_gate": "HOLD"}
        db.execute("INSERT INTO fp119_runs VALUES(?,?,?,?)",
                   (run_id, goal_sha, "IN_PROGRESS", ""))
        _append(db, run_id, "RESERVED", {"template": plan["template"]})
        db.commit()
    except Exception:
        db.rollback()
        raise
    try:
        reviewed = run_council(goal, inject_test_fault=inject_test_fault,
                               max_repairs=max_repairs)
        success = reviewed.get("status") == "OFFLINE_COUNCIL_REHEARSAL_PASS"
        trace = reviewed.get("trace", [])
        events: list[tuple[str, dict]] = []
        if not isinstance(trace, list) or len(trace) > 8:
            success = False
            trace = []
        for row in trace:
            if (type(row) is not dict or row.get("role") not in _ROLES
                    or row.get("status") not in _STATES):
                success = False
                events = []
                break
            # No raw untrusted strings from the model or NAS are persisted.
            events.append(("ROLE", {"role": row["role"], "status": row["status"]}))
        terminal = "SYNTHETIC_QA_PASS" if success else "SYNTHETIC_QA_BLOCKED"
    except Exception:
        events = []
        success, terminal = False, "SANITIZED_EXECUTION_ERROR"
    db.execute("BEGIN IMMEDIATE")
    try:
        for kind, detail in events:
            _append(db, run_id, kind, detail)
        final_sha = _append(db, run_id, "TERMINAL", {"result": terminal})
        db.execute("UPDATE fp119_runs SET status=?, final_sha=? WHERE run_id=?",
                   ("PASS" if success else "BLOCKED", final_sha, run_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "schema": _SCHEMA, "status": "SYNTHETIC_LEDGER_PASS" if success else "SYNTHETIC_LEDGER_BLOCKED",
        "run_id": run_id, "template": plan["template"], "receipt_sha256": final_sha,
        "repair_count": reviewed.get("repair_count", 0) if "reviewed" in locals() else 0,
        "synthetic_fixture_executed": bool(success), "actual_docker_executed": False,
        "nas_verified": False, "production_applied": False, "release_gate": "HOLD",
    }


def verify_record(db: sqlite3.Connection, run_id: str) -> dict:
    """Detect accidental/naive tampering; not independently notarized."""
    if type(run_id) is not str or _ID.fullmatch(run_id) is None:
        raise ValueError("Invalid run ID")
    row = db.execute("SELECT status, final_sha FROM fp119_runs WHERE run_id=?",
                     (run_id,)).fetchone()
    events = db.execute(
        "SELECT seq, kind, detail, previous_sha, event_sha FROM fp119_events "
        "WHERE run_id=? ORDER BY seq", (run_id,)
    ).fetchall()
    expected = "0" * 64
    good = row is not None and bool(events)
    last_kind = None
    for i, (seq, kind, serialized, prev, digest) in enumerate(events, 1):
        try:
            detail = json.loads(serialized)
            candidate = _sha({"run_id": run_id, "seq": seq, "kind": kind,
                              "detail": detail, "previous_sha": prev})
        except (TypeError, ValueError):
            good = False
            break
        if seq != i or prev != expected or candidate != digest:
            good = False
            break
        expected, last_kind = digest, kind
    good = good and last_kind == "TERMINAL" and row[1] == expected and row[0] in ("PASS", "BLOCKED")
    return {"schema": _SCHEMA,
            "status": "LOCAL_CHAIN_INTACT" if good else "LOCAL_CHAIN_INVALID",
            "event_count": len(events), "independently_notarized": False,
            "nas_verified": False, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Synthetic council with replay barrier; not NAS")
    ap.add_argument("--goal", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--inject-test-fault", action="store_true")
    args = ap.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g119-") as tmp:
            with sqlite3.connect(Path(tmp) / "evidence.sqlite") as db:
                result = run_once(args.goal, args.run_id, db,
                                  inject_test_fault=args.inject_test_fault)
                if result["status"] == "SYNTHETIC_LEDGER_PASS":
                    result["integrity"] = verify_record(db, args.run_id)["status"]
    except (ValueError, sqlite3.Error, OSError):
        result = {"status": "LEDGER_REFUSED", "release_gate": "HOLD"}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "SYNTHETIC_LEDGER_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
