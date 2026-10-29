"""FlowPilot 3.0 bounded LOCAL CSV report prototype (NOT Uliya/NAS/LA/SOVIA integration).

Requires separate explicit approval for execution. No source writes, no symlinks,
no arbitrary code execution, and no network access.
"""
from __future__ import annotations

from contextlib import closing

import csv
import hashlib
import json
import sqlite3
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


def _sha256_file(path: Path) -> str:
    """Bounded-memory digest for source and report evidence."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

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
    sources = [_inside(root, name, existing=True) for name in plan["sources"]]
    source_hashes = [_sha256_file(src) for src in sources]
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
                if (None in row or key is None or not isinstance(key, str)
                        or not key or len(key) > 255 or key.lstrip().startswith(("=", "+", "-", "@"))):
                    raise ReportRefused("Invalid or spreadsheet-unsafe grouping key")
                try:
                    value = Decimal(row[plan["amount"]])
                except (InvalidOperation, TypeError):
                    raise ReportRefused("Invalid numeric value") from None
                if not key or not value.is_finite():
                    raise ReportRefused("Invalid group or non-finite value")
                totals[key] = totals.get(key, Decimal(0)) + value
    if not totals:
        raise ReportRefused("No data rows")
    if any(_sha256_file(src) != digest for src, digest in zip(sources, source_hashes)):
        raise ReportRefused("Source changed during report computation")
    # Exclusive creation avoids overwriting any pre-existing output.
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([plan["group"], "total_" + plan["amount"]])
        for key in sorted(totals):
            writer.writerow([key, str(totals[key])])
    report_sha256 = _sha256_file(output)
    # Exact node IDs match the deterministic FlowPilot preview graph. This is
    # local evidence, NOT a SOVIA risk rating or an LA execution trace.
    node_trace = [
        {"node_id": f"read_{index}", "action": "csv_read", "status": "COMPLETED",
         "source_sha256": digest}
        for index, digest in enumerate(source_hashes, 1)
    ]
    node_trace.extend([
        {"node_id": "aggregate", "action": "decimal_group_sum", "status": "COMPLETED",
         "rows": rows, "groups": len(totals)},
        {"node_id": "write", "action": "csv_write_new", "status": "COMPLETED",
         "report_sha256": report_sha256},
        {"node_id": "audit", "action": "sqlite_audit", "status": "COMPLETED"},
    ])
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "output": plan["output"],
              "source_count": len(plan["sources"]), "rows": rows, "groups": len(totals),
              "report_sha256": report_sha256,
              "node_trace": node_trace,
              "audit_kind": "FLOWPILOT_LOCAL_EVIDENCE_NOT_SOVIA",
              "status": "LOCAL_REPORT_CREATED_NOT_NAS"}
    # This is a generic local SQLite trace, NOT a SOVIA/DBVORA integration.
    with closing(sqlite3.connect(audit_db)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS flowpilot_runs (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, record_json TEXT NOT NULL)")
        db.execute("INSERT INTO flowpilot_runs(timestamp, record_json) VALUES (?,?)",
                   (record["timestamp"], json.dumps(record, sort_keys=True)))
    return record
