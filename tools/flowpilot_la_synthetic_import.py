"""Bounded synthetic CSV -> *installed* Lightning Azent -> local SQLite proof.

Development only, separate from UGREEN Round 1 Markdown Skill. No HAE
application, NAS, registered Uliya Expert, DBVORA, SOVIA or customer files.
The only input is a hard-coded CSV fixture in a disposable temp directory.
Missing/incompatible LA fails closed; never executes FlowPilot group-sum graph.
"""
from __future__ import annotations

from contextlib import closing

import argparse
import csv
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

GOAL = "import synthetic sales CSV to local SQLite"
APPROVAL = "APPROVE_SYNTHETIC_SQLITE_IMPORT"
LA_PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "source", "op": "csv_read", "path": "sales.csv"},
    {"id": "imported", "op": "sqlite_import_csv", "from": "source"},
]}
REQUIRED_OPS = frozenset({"csv_read", "sqlite_import_csv"})
TEST_ROWS = (("customer", "amount"), ("alice", "1.25"), ("bob", "2.00"))
RUN_ID = "FlowPilotSyntheticImport"


def _answer(status: str, *, attempted: bool = False, executed: bool = False,
            persisted: int = 0, replay: bool = False, audited: bool = False,
            source_preserved: bool = False) -> dict:
    return {
        "schema": "flowpilot-la-synthetic-import-v1", "status": status,
        "mode": "DISPOSABLE_SYNTHETIC_ONLY_NOT_NAS",
        "goal": GOAL, "requires_approval": True,
        "requires_external_call": False, "requested_steps": ["csv_read", "sqlite_import_csv"],
        "la_executor_called": attempted, "la_execution_verified": executed,
        "persisted_rows": persisted, "replay_verified": replay,
        "metadata_audit_observed": audited, "source_hash_preserved": source_preserved,
        "hae_application_called": False, "dbvora_called": False,
        "sovia_called": False, "uliya_or_nas_called": False,
        "flowpilot_grouped_csv_supported": False, "release_gate": "HOLD",
    }


def _compatible(executor_type: object) -> bool:
    """Validate the real installed facade contract without touching any files."""
    try:
        info = executor_type.capabilities()
        preview = executor_type.preflight(LA_PLAN)
    except Exception:
        return False
    if not isinstance(info, dict) or not isinstance(preview, dict):
        return False
    ops = info.get("implemented_operations")
    if (info.get("api_version") != "azent.api.v0"
            or info.get("native_ir_version") != "azent.ir.v0"
            or info.get("scope") != "synthetic-local-only"
            or info.get("external_connectors") != []
            or not isinstance(ops, list)
            or not all(isinstance(op, str) for op in ops)
            or len(set(ops)) != len(ops)
            or not REQUIRED_OPS.issubset(set(ops))):
        return False
    return (preview.get("source_version") == "azent.ir.v0"
            and preview.get("runtime_version") == "axflow.ir.v0"
            and preview.get("step_count") == 2
            and preview.get("requires_write_approval") is True
            and preview.get("requires_input_root") is True
            and preview.get("executes_workflow") is False
            and preview.get("scope") == "synthetic-local-only")


def run_demo(*, approval: str | None = None, loader=import_module,
             workspace=TemporaryDirectory) -> dict:
    """Perform an actual LA call only on explicitly approved synthetic inputs.

    A test loader may supply a fake package; that does not independently prove
    the private installed LA works. No customer path/CSV parameters are accepted.
    """
    if approval is None:
        return _answer("WAITING_EXECUTION_APPROVAL")
    if approval == "REJECT":
        return _answer("DECLINED")
    if approval != APPROVAL:
        return _answer("REFUSED_INVALID_APPROVAL")
    try:
        executor_type = loader("lightning_azent").LAExecutor
    except Exception:
        return _answer("BLOCKED_RUNTIME_UNAVAILABLE")
    if not _compatible(executor_type):
        return _answer("BLOCKED_RUNTIME_CONTRACT")
    attempted = False
    try:
        with workspace(prefix="flowpilot-la-synthetic-") as temporary:
            root = Path(temporary)
            source = root / "sales.csv"
            with source.open("x", encoding="utf-8", newline="") as stream:
                csv.writer(stream).writerows(TEST_ROWS)
            before = sha256(source.read_bytes()).hexdigest()
            state, business = root / "state.sqlite", root / "business.sqlite"
            engine = executor_type(state, business, input_root=root)
            attempted = True
            engine.execute(LA_PLAN, RUN_ID, approve_writes=True)
            engine.execute(LA_PLAN, RUN_ID, approve_writes=True)
            status = engine.status(RUN_ID)
            audit = engine.audit(RUN_ID)
            verified = engine.verify_receipts(LA_PLAN, RUN_ID)
            # SQLite's connection context manager commits/rolls back but does NOT
            # close the file handle. Release before the temporary root cleanup.
            with closing(sqlite3.connect(
                business.resolve(strict=True).as_uri() + "?mode=ro", uri=True,
                timeout=2.0,
            )) as connection:
                persisted_rows = connection.execute(
                    "SELECT row_number, source_sha256, payload_json "
                    "FROM csv_records WHERE run_id=? AND import_step_id=? "
                    "ORDER BY row_number",
                    (RUN_ID, "imported"),
                ).fetchall()
            expected_rows = [
                (index, before, dict(zip(TEST_ROWS[0], cells)))
                for index, cells in enumerate(TEST_ROWS[1:], start=1)
            ]
            provenance_matches = (
                len(persisted_rows) == len(expected_rows)
                and all(
                    type(row_number) is int and row_number == expected_number
                    and digest == expected_digest
                    and isinstance(payload, str)
                    and json.loads(payload) == expected_data
                    for (row_number, digest, payload),
                        (expected_number, expected_digest, expected_data)
                    in zip(persisted_rows, expected_rows)
                )
            )
            preserved = sha256(source.read_bytes()).hexdigest() == before
            if (not isinstance(status, dict) or status.get("status") != "completed"
                    or not isinstance(audit, dict) or audit.get("run_id") != RUN_ID
                    or not isinstance(audit.get("events"), list) or not audit["events"]
                    or not isinstance(audit.get("approval_receipts"), list)
                    or not audit["approval_receipts"]
                    or not isinstance(verified, dict) or verified.get("verified") is not True
                    or not provenance_matches or not preserved):
                return _answer("BLOCKED_RECEIPT_MISMATCH", attempted=attempted)
            return _answer("SYNTHETIC_LA_SQLITE_VERIFIED", attempted=True, executed=True,
                           persisted=len(persisted_rows), replay=True, audited=True, source_preserved=True)
    except Exception:
        # Never echo exception strings, filesystem paths, database values or CSV cells.
        return _answer("BLOCKED_LA_EXECUTION_OR_AUDIT", attempted=attempted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Disposable synthetic LA import; not NAS")
    parser.add_argument("--approval", help="Requires APPROVE_SYNTHETIC_SQLITE_IMPORT")
    args = parser.parse_args(argv)
    result = run_demo(approval=args.approval)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"WAITING_EXECUTION_APPROVAL", "DECLINED",
                                       "SYNTHETIC_LA_SQLITE_VERIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
