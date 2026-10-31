"""Opt-in durable LOCAL SQLite evidence for FlowPilot's synthetic council QA.

No real NAS, Expert Agent, Docker, external API, or customer files are used.
A successful receipt is not production evidence or independently notarized.
Run IDs are replay-protected only within the selected SQLite database.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

_SCHEMA = "flowpilot-persistent-local-qa-v1"
_MARKER = "flowpilot-g133-created-local-db-v1"
_RUN = re.compile(r"run_[A-Za-z0-9_-]{8,48}\Z")
_MAX_DB_BYTES = 10 * 1024 * 1024


class PersistentQARefused(ValueError):
    """Public status never includes the path, goal, or database contents."""


def _check_path(path: Path, *, create: bool) -> None:
    if (not isinstance(path, Path) or not path.is_absolute()
            or path.suffix.lower() != ".sqlite"
            or str(path).startswith(("//", "\\\\"))
            or not path.parent.is_dir()):
        raise PersistentQARefused("INVALID_LOCAL_DB_PATH")
    if any(parent.is_symlink() for parent in (path.parent, *path.parent.parents)):
        raise PersistentQARefused("SYMLINK_PARENT_REFUSED")
    if path.is_symlink():
        raise PersistentQARefused("SYMLINK_DB_REFUSED")
    if create:
        if path.exists():
            raise PersistentQARefused("ORIGINAL_DB_ALREADY_EXISTS")
        return
    try:
        meta = path.stat()
    except OSError as exc:
        raise PersistentQARefused("DB_NOT_FOUND") from exc
    if (not stat.S_ISREG(meta.st_mode) or not 0 < meta.st_size <= _MAX_DB_BYTES
            or (os.name != "nt" and meta.st_nlink != 1)):
        raise PersistentQARefused("UNSUPPORTED_EXISTING_DB")


def _connect(path: Path, *, mode: str) -> sqlite3.Connection:
    if mode not in ("new", "append", "read"):
        raise PersistentQARefused("INVALID_DB_MODE")
    create = mode == "new"
    _check_path(path, create=create)
    created = False
    if create:
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
            os.close(fd)
            created = True
        except (FileExistsError, OSError) as exc:
            raise PersistentQARefused("EXCLUSIVE_CREATE_REFUSED") from exc
    try:
        access = "ro" if mode == "read" else "rw"
        conn = sqlite3.connect(path.as_uri() + "?mode=" + access, uri=True, timeout=3)
        try:
            if create:
                conn.execute("CREATE TABLE fp133_identity (singleton INTEGER PRIMARY KEY "
                             "CHECK(singleton=1), schema_id TEXT NOT NULL)")
                conn.execute("INSERT INTO fp133_identity VALUES(1,?)", (_MARKER,))
                conn.commit()
            row = conn.execute(
                "SELECT schema_id FROM fp133_identity WHERE singleton=1"
            ).fetchone()
            if row != (_MARKER,):
                raise PersistentQARefused("UNRECOGNIZED_DB_IDENTITY")
            return conn
        except BaseException:
            conn.close()
            raise
    except BaseException:
        # Only a newly created and still empty/invalid file is discarded.
        # Never delete or overwrite an existing owner-selected database.
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise


def _inspect_connection(db: sqlite3.Connection, run_id: str) -> dict:
    table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fp119_runs'"
    ).fetchone()
    if table is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    row = db.execute(
        "SELECT status FROM fp119_runs WHERE run_id=?", (run_id,)
    ).fetchone()
    if row is None:
        return {"status": "NO_RUN_RECORD", "evidence_integrity": "NOT_RUN"}
    from flowpilot_repair_ledger import verify_record
    integrity = verify_record(db, run_id)["status"]
    return {"status": "READ_ONLY_LOCAL_EVIDENCE" if integrity == "LOCAL_CHAIN_INTACT"
            else "LOCAL_EVIDENCE_INVALID", "evidence_integrity": integrity,
            "stored_run_state": row[0] if row[0] in ("PASS", "BLOCKED") else "INVALID"}


def run_persistent(goal: str | None, run_id: str, db_file: Path, *, mode: str,
                   approve_local_write: bool = False,
                   inject_test_fault: bool = False) -> dict:
    """Explicitly create, resume, or inspect a known local SQLite evidence file.

    No disk access precedes consent in write modes. read mode never writes.
    The G119 transactional run reservation protects duplicates across CLI runs.
    """
    base = {"schema": _SCHEMA, "release_gate": "HOLD", "nas_verified": False,
            "registered_expert_invoked": False, "actual_docker_executed": False,
            "production_applied": False, "independently_notarized": False,
            "external_api_called": False}
    if type(run_id) is not str or _RUN.fullmatch(run_id) is None:
        return {**base, "status": "INVALID_RUN_ID"}
    if mode not in ("new", "append", "read"):
        return {**base, "status": "INVALID_DB_MODE"}
    if type(approve_local_write) is not bool or type(inject_test_fault) is not bool:
        return {**base, "status": "INVALID_FLAGS"}
    if mode != "read" and not approve_local_write:
        return {**base, "status": "WAITING_EXPLICIT_LOCAL_DB_APPROVAL"}
    if mode != "read" and (type(goal) is not str or not goal.strip()):
        return {**base, "status": "INVALID_GOAL"}
    if mode == "read" and inject_test_fault:
        return {**base, "status": "INVALID_FLAGS"}
    try:
        with closing(_connect(db_file, mode=mode)) as db:
            if mode == "read":
                record = _inspect_connection(db, run_id)
                return {**base, **record, "database_modified": False}
            from flowpilot_repair_ledger import run_once
            receipt = run_once(goal, run_id, db, inject_test_fault=inject_test_fault)
            state = receipt["status"]
            if state in ("SYNTHETIC_LEDGER_PASS", "SYNTHETIC_LEDGER_BLOCKED",
                         "DUPLICATE_BLOCKED", "RUN_ID_GOAL_CONFLICT"):
                checked = _inspect_connection(db, run_id)
                integrity = checked["evidence_integrity"]
            else:
                integrity = "NOT_RUN"
            if integrity == "LOCAL_CHAIN_INVALID":
                status = "PRIOR_LOCAL_EVIDENCE_INVALID"
            elif state == "SYNTHETIC_LEDGER_PASS" and integrity == "LOCAL_CHAIN_INTACT":
                status = "PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD"
            elif state == "SYNTHETIC_LEDGER_BLOCKED" and integrity == "LOCAL_CHAIN_INTACT":
                status = "PERSISTED_SYNTHETIC_QA_BLOCKED"
            elif state in ("DUPLICATE_BLOCKED", "RUN_ID_GOAL_CONFLICT") and integrity == "LOCAL_CHAIN_INTACT":
                status = state
            else:
                status = "NOT_VERIFIED_OR_UNSUPPORTED"
            return {**base, "status": status, "evidence_integrity": integrity,
                    "synthetic_fixture_executed": bool(receipt.get("synthetic_fixture_executed", False)
                                                     and integrity == "LOCAL_CHAIN_INTACT"),
                    "database_modified": state in ("SYNTHETIC_LEDGER_PASS", "SYNTHETIC_LEDGER_BLOCKED"),
                    "run_id": run_id}
    except (PersistentQARefused, sqlite3.Error, OSError, ValueError, TypeError):
        return {**base, "status": "LOCAL_DB_REFUSED"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persistent local synthetic QA; no NAS/Expert")
    parser.add_argument("--db", type=Path, required=True, help="Owner-selected absolute local .sqlite path")
    parser.add_argument("--mode", required=True, choices=("new", "append", "read"))
    parser.add_argument("--goal", help="One of two exact supported synthetic goals")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--approve-local-write", action="store_true")
    parser.add_argument("--inject-test-fault", action="store_true")
    args = parser.parse_args(argv)
    result = run_persistent(args.goal, args.run_id, args.db, mode=args.mode,
                            approve_local_write=args.approve_local_write,
                            inject_test_fault=args.inject_test_fault)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] in ("PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD",
                                      "READ_ONLY_LOCAL_EVIDENCE", "NO_RUN_RECORD") else 2


if __name__ == "__main__":
    raise SystemExit(main())
