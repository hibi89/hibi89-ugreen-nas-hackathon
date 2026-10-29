"""Read-only local SQLite execution history viewer for FlowPilot 3.0 prototype.

This is NOT an integration with SOVIA or DBVORA, nor a Uliya/NAS runtime.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class AuditReadRefused(ValueError):
    pass


def recent_runs(db_path: Path, *, limit: int = 20) -> dict:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise AuditReadRefused("Invalid result limit")
    db_path = Path(db_path)
    if db_path.is_symlink() or not db_path.is_file():
        raise AuditReadRefused("Audit database not found")
    try:
        # URI read-only mode prevents implicit creation and all writes.
        with sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA busy_timeout=1000")
            rows = db.execute(
                "SELECT id, timestamp, record_json FROM flowpilot_runs "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    except sqlite3.Error as exc:
        raise AuditReadRefused("Cannot read audit history") from exc
    results = []
    for run_id, timestamp, payload in rows:
        try:
            record = json.loads(payload)
        except (TypeError, ValueError) as exc:
            raise AuditReadRefused("Corrupted audit record") from exc
        if not isinstance(record, dict):
            raise AuditReadRefused("Invalid audit record")
        results.append({"id": run_id, "timestamp": timestamp, "record": record})
    return {"mode": "LOCAL_SQLITE_AUDIT_NOT_SOVIA_DBVORA_NAS",
            "count": len(results), "runs": results,
            "sovia_integrated": False, "dbvora_integrated": False,
            "nas_verified": False}
