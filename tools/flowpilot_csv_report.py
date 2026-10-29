"""FlowPilot 3.0 bounded LOCAL CSV report prototype (NOT Uliya/NAS/LA/SOVIA integration).

Requires separate explicit approval for execution. No source writes, no symlinks,
no arbitrary code execution, and no network access.
"""
from __future__ import annotations

from contextlib import closing

import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_FILES = 20
MAX_BYTES = 8_000_000
MAX_ROWS = 100_000


class ReportRefused(ValueError):
    pass


def _inside(root: Path, relative: str, *, existing: bool) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ReportRefused("Invalid relative path")
    p = Path(relative)
    if p.is_absolute() or any(part in ("..", ".") for part in p.parts):
        raise ReportRefused("Unsafe path")
    root = root.resolve(strict=True)
    target = root / p
    cursor = root
    for part in p.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ReportRefused("Symlink path refused")
    if existing and not target.is_file():
        raise ReportRefused("Missing source file")
    if target.resolve(strict=existing) == root or root not in target.resolve(strict=existing).parents:
        raise ReportRefused("Out-of-root path")
    return target


def preview(root: Path, sources: list[str], output: str, *, group: str, amount: str) -> dict:
    if not isinstance(sources, list) or not 1 <= len(sources) <= MAX_FILES or len(set(sources)) != len(sources):
        raise ReportRefused("Invalid source list")
    if not group or not amount or group == amount:
        raise ReportRefused("Invalid column mapping")
    if not all(isinstance(x, str) and x.endswith(".csv") for x in sources):
        raise ReportRefused("CSV only")
    if not isinstance(output, str) or not output.endswith(".csv") or output in sources:
        raise ReportRefused("Output must be a separate CSV")
    paths = [_inside(root, x, existing=True) for x in sources]
    dest = _inside(root, output, existing=False)
    if dest.exists() or not dest.parent.is_dir():
        raise ReportRefused("Output exists or parent missing")
    if any(p.stat().st_size > MAX_BYTES for p in paths):
        raise ReportRefused("Source exceeds size limit")
    return {"schema": "flowpilot-local-csv-v1", "sources": sources, "output": output,
            "group": group, "amount": amount, "operations": ["read_csv", "group_sum_decimal", "write_new_csv"],
            "status": "WAITING_EXECUTION_APPROVAL", "nas_verified": False,
            "la_engine_integrated": False, "sovia_integrated": False, "dbvora_integrated": False}


def execute(root: Path, plan: dict, *, approval: str, audit_db: Path) -> dict:
    if approval != "APPROVE_EXECUTION":
        raise ReportRefused("Explicit execution approval required")
    if not isinstance(plan, dict) or set(plan) != {"schema", "sources", "output", "group", "amount",
            "operations", "status", "nas_verified", "la_engine_integrated", "sovia_integrated", "dbvora_integrated"}:
        raise ReportRefused("Invalid plan")
    verified = preview(root, plan["sources"], plan["output"], group=plan["group"], amount=plan["amount"])
    if plan != verified:
        raise ReportRefused("Plan changed since preview")
    root = root.resolve(strict=True)
    output = _inside(root, plan["output"], existing=False)
    audit_db = Path(audit_db)
    if audit_db.is_symlink() or audit_db.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
        raise ReportRefused("Unsafe audit database path")
    if audit_db.resolve() == output.resolve() or any(
        audit_db.resolve() == _inside(root, name, existing=True).resolve()
        for name in plan["sources"]
    ):
        raise ReportRefused("Audit database conflicts with source or output")
    if audit_db.exists() and not audit_db.is_file():
        raise ReportRefused("Invalid audit database")
    totals: dict[str, Decimal] = {}
    rows = 0
    for name in plan["sources"]:
        src = _inside(root, name, existing=True)
        with src.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ReportRefused("Invalid CSV headers")
            if plan["group"] not in reader.fieldnames or plan["amount"] not in reader.fieldnames:
                raise ReportRefused("Required column missing")
            for row in reader:
                rows += 1
                if rows > MAX_ROWS:
                    raise ReportRefused("Row limit exceeded")
                key = row[plan["group"]]
                try:
                    value = Decimal(row[plan["amount"]])
                except (InvalidOperation, TypeError):
                    raise ReportRefused("Invalid numeric value") from None
                if not key or not value.is_finite():
                    raise ReportRefused("Invalid group or non-finite value")
                totals[key] = totals.get(key, Decimal(0)) + value
    if not totals:
        raise ReportRefused("No data rows")
    # Exclusive creation avoids overwriting any pre-existing output.
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([plan["group"], "total_" + plan["amount"]])
        for key in sorted(totals):
            writer.writerow([key, str(totals[key])])
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "output": plan["output"],
              "source_count": len(plan["sources"]), "rows": rows, "groups": len(totals),
              "status": "LOCAL_REPORT_CREATED_NOT_NAS"}
    # This is a generic local SQLite trace, NOT a SOVIA/DBVORA integration.
    with closing(sqlite3.connect(audit_db)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS flowpilot_runs (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, record_json TEXT NOT NULL)")
        db.execute("INSERT INTO flowpilot_runs(timestamp, record_json) VALUES (?,?)",
                   (record["timestamp"], json.dumps(record, sort_keys=True)))
    return record
