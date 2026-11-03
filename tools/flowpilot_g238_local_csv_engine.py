"""G238: approval-gated LOCAL typed CSV workflow over owner-selected data.

Preview computes a deterministic contract without touching the filesystem.
An exact separate approval + matching plan digest permits ONE bounded read
of a single regular, non-link local CSV file. Fixed four-stage typed graph:
csv_read -> validate_decimal -> group_sum -> report. No shell, Docker, NAS,
Uliya calls, background work or user-source edits. Only explicit separate
consent writes a new local report OR redacted audit (never overwrites).
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = "flowpilot-g238-owner-local-typed-csv-v1"
STEPS = ("csv_read", "validate_decimal", "group_sum", "report")
GROUP_COLUMNS = frozenset(("customer", "department", "project"))
READ_ACK = "APPROVE_LOCAL_CSV_READ_ONCE"
EXPORT_ACK = "APPROVE_LOCAL_REPORT_CREATE"
AUDIT_ACK = "APPROVE_LOCAL_AUDIT_CREATE"
MAX_BYTES = 32768
MAX_ROWS = 256
MAX_GROUPS = 32
MAX_CENTS = 1000000
LABEL = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}\Z")
DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,6})\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class LocalCsvRefused(ValueError):
    """Never put owner-supplied paths, column values or file contents in errors."""


def _refuse(code: str):
    raise LocalCsvRefused(code)


def _hash(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _json_bytes(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _path(value: object) -> Path:
    if type(value) is not str or not 0 < len(value) <= 1024 or "\x00" in value:
        _refuse("G238_ABSOLUTE_PATH_REQUIRED")
    p = Path(value)
    if not p.is_absolute() or ".." in p.parts or not p.name:
        _refuse("G238_ABSOLUTE_PATH_REQUIRED")
    return p


def preview(input_path: str, group_column: str) -> dict:
    """Pure metadata-free preview: NEVER stat, open, read or inspect owner files."""
    p = _path(input_path)
    if type(group_column) is not str or group_column not in GROUP_COLUMNS:
        _refuse("G238_UNSUPPORTED_GROUP_COLUMN")
    contract = {
        "schema": SCHEMA,
        "source_scope_sha256": _hash(os.fsencode(str(p))),
        "group_column": group_column,
        "amount_column": "amount_cents",
        "typed_nodes": list(STEPS),
        "maximum_input_bytes": MAX_BYTES,
        "maximum_rows": MAX_ROWS,
        "maximum_groups": MAX_GROUPS,
        "read_only": True,
        "write_approval_independent": True,
        "nas_execution_available": False,
    }
    plan_sha = _hash(_json_bytes(contract))
    return {
        "schema": SCHEMA, "status": "WAITING_EXPLICIT_LOCAL_READ_APPROVAL",
        "plan_sha256": plan_sha,
        "typed_nodes": list(STEPS),
        "group_column": group_column,
        "input_scope_is_path_digest_only": True,
        "input_file_touched": False,
        "input_file_content_read": False,
        "input_sha256_known": False,
        "owner_data_may_be_read_after_separate_ack": True,
        "real_nas_verified": False, "release_gate": "HOLD",
    }


def _secure_parent_and_entry(path: Path, *, require_file: bool) -> None:
    """Refuse link parents and link/hardlink sources; no permission escalation."""
    for part in (path.parent, *path.parent.parents):
        try:
            if part.is_symlink() or not part.is_dir():
                _refuse("G238_UNSAFE_PARENT")
        except OSError:
            _refuse("G238_UNSAFE_PARENT")
    if require_file:
        try:
            s = path.lstat()
        except OSError:
            _refuse("G238_INPUT_NOT_REGULAR")
        if (not stat.S_ISREG(s.st_mode) or s.st_size <= 0
                or s.st_size > MAX_BYTES or
                (os.name != "nt" and s.st_nlink != 1)):
            _refuse("G238_INPUT_NOT_REGULAR")
    elif path.is_symlink():
        _refuse("G238_OUTPUT_LINK_REFUSED")


def _read_once(p: Path) -> bytes:
    _secure_parent_and_entry(p, require_file=True)
    fd = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        fd = os.open(p, flags)
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_BYTES
                or (os.name != "nt" and before.st_nlink != 1)):
            _refuse("G238_OPENED_FILE_INVALID")
        chunks = []
        used = 0
        while True:
            block = os.read(fd, min(8192, MAX_BYTES + 1 - used))
            if not block:
                break
            used += len(block)
            if used > MAX_BYTES:
                _refuse("G238_INPUT_TOO_LARGE")
            chunks.append(block)
        after = os.fstat(fd)
        now = p.lstat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
        if (not stat.S_ISREG(now.st_mode)
                or any(getattr(before, k) != getattr(after, k)
                       or getattr(after, k) != getattr(now, k) for k in fields)
                or used != before.st_size):
            _refuse("G238_INPUT_CHANGED_DURING_READ")
        return b"".join(chunks)
    except OSError:
        _refuse("G238_LOCAL_READ_FAILED")
    finally:
        if fd is not None:
            os.close(fd)


def _typed_run(raw: bytes, group_column: str) -> tuple[dict, bytes]:
    """Real row parsing + typed validation + grouping, not fixed expected totals."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        _refuse("G238_INVALID_BOUNDED_CSV")
    try:
        text = raw.decode("utf-8", errors="strict")
        records = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except (UnicodeError, csv.Error, ValueError):
        _refuse("G238_INVALID_CSV_ENCODING_OR_SYNTAX")
    if (not records or records[0] != [group_column, "amount_cents"]
            or not 1 <= len(records) - 1 <= MAX_ROWS):
        _refuse("G238_CSV_HEADER_OR_SIZE_REFUSED")
    totals: dict[str, list[int]] = {}
    for record in records[1:]:
        if len(record) != 2:
            _refuse("G238_CSV_FIELDS_REFUSED")
        name, amount = record
        if (LABEL.fullmatch(name) is None or
                DECIMAL.fullmatch(amount) is None):
            _refuse("G238_CSV_VALUE_REFUSED")
        value = int(amount)
        if value > MAX_CENTS:
            _refuse("G238_AMOUNT_OUT_OF_RANGE")
        if name not in totals:
            if len(totals) == MAX_GROUPS:
                _refuse("G238_GROUP_LIMIT")
            totals[name] = [0, 0]
        totals[name][0] += value
        totals[name][1] += 1
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow([group_column, "total_cents", "source_rows"])
    summary = []
    for i, (label, (total, count)) in enumerate(sorted(totals.items()), 1):
        writer.writerow([label, str(total), str(count)])
        summary.append({"group_index": i, "total_cents": total,
                        "source_rows": count})
    report = stream.getvalue().encode("utf-8")
    return {
        "source_rows": len(records) - 1, "group_count": len(totals),
        "redacted_group_totals": summary,
        "report_sha256": _hash(report),
    }, report


def _create_only(destination: str, content: bytes, source: Path) -> None:
    target = _path(destination)
    if target == source:
        _refuse("G238_NO_OVERWRITE_OR_SOURCE_MUTATION")
    _secure_parent_and_entry(target, require_file=False)
    if target.exists():
        _refuse("G238_NO_OVERWRITE_OR_SOURCE_MUTATION")
    fd = None
    try:
        fd = os.open(target,
                     os.O_RDWR | os.O_CREAT | os.O_EXCL |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            _refuse("G238_OUTPUT_NOT_REGULAR")
        with os.fdopen(fd, "r+b", closefd=False) as f:
            f.write(content)
            f.flush()
            os.fsync(fd)
            f.seek(0)
            if f.read(len(content) + 1) != content:
                _refuse("G238_OUTPUT_READBACK_FAILED")
    except OSError:
        _refuse("G238_EXCLUSIVE_CREATE_FAILED")
    finally:
        if fd is not None:
            os.close(fd)


def execute(input_path: str, group_column: str, plan_sha256: str,
            approval: str, *, export_to: str | None = None,
            export_approval: str | None = None,
            audit_to: str | None = None,
            audit_approval: str | None = None) -> dict:
    plan = preview(input_path, group_column)
    if (type(plan_sha256) is not str or SHA.fullmatch(plan_sha256) is None or
            plan_sha256 != plan["plan_sha256"] or
            type(approval) is not str or approval != READ_ACK):
        _refuse("G238_EXACT_PLAN_BOUND_LOCAL_READ_APPROVAL_REQUIRED")
    if export_to is not None and audit_to is not None:
        _refuse("G238_ONLY_ONE_NEW_FILE_PER_RUN")
    if ((export_to is not None and export_approval != EXPORT_ACK)
            or (audit_to is not None and audit_approval != AUDIT_ACK)
            or (export_to is None and export_approval is not None)
            or (audit_to is None and audit_approval is not None)):
        _refuse("G238_SEPARATE_WRITE_APPROVAL_REQUIRED")
    input_file = _path(input_path)
    raw = _read_once(input_file)
    result, full_report = _typed_run(raw, group_column)
    receipt = {
        "schema": SCHEMA,
        "status": "APPROVED_LOCAL_TYPED_WORKFLOW_COMPLETE_NOT_NAS",
        "plan_sha256": plan_sha256,
        "source_sha256": _hash(raw),
        "report_sha256": result["report_sha256"],
        "typed_nodes_executed": list(STEPS),
        "source_rows": result["source_rows"],
        "group_count": result["group_count"],
        "redacted_group_totals": result["redacted_group_totals"],
        "owner_file_read_only_after_exact_approval": True,
        "owner_source_modified": False,
        "raw_group_names_in_response": False,
        "external_calls_performed": False, "docker_used": False,
        "uliya_expert_invoked": False, "nas_verified": False,
        "release_gate": "HOLD",
    }
    receipt_sha = _hash(_json_bytes(receipt))
    if export_to is not None:
        _create_only(export_to, full_report, input_file)
    if audit_to is not None:
        # Full redacted proof remains local and requires distinct create consent.
        _create_only(audit_to, _json_bytes({**receipt,
                                            "receipt_sha256": receipt_sha}) + b"\n",
                     input_file)
    return {**receipt, "receipt_sha256": receipt_sha,
            "report_file_created": export_to is not None,
            "local_audit_file_created": audit_to is not None}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local bounded typed CSV only; no NAS")
    p.add_argument("--mode", required=True, choices=("preview", "run"))
    p.add_argument("--input", required=True)
    p.add_argument("--group-column", required=True, choices=tuple(sorted(GROUP_COLUMNS)))
    p.add_argument("--plan-sha256")
    p.add_argument("--approval")
    p.add_argument("--export-to")
    p.add_argument("--export-approval")
    p.add_argument("--audit-to")
    p.add_argument("--audit-approval")
    args = p.parse_args(argv)
    try:
        if args.mode == "preview":
            if any(getattr(args, k) is not None for k in (
                    "plan_sha256", "approval", "export_to",
                    "export_approval", "audit_to", "audit_approval")):
                _refuse("G238_PREVIEW_READ_AND_WRITE_FREE_ONLY")
            output = preview(args.input, args.group_column)
        else:
            output = execute(args.input, args.group_column,
                             args.plan_sha256, args.approval,
                             export_to=args.export_to,
                             export_approval=args.export_approval,
                             audit_to=args.audit_to,
                             audit_approval=args.audit_approval)
        print(json.dumps(output, sort_keys=True))
        return 0
    except (LocalCsvRefused, OSError, UnicodeError, TypeError) as exc:
        code = str(exc) if isinstance(exc, LocalCsvRefused) else "G238_LOCAL_IO_REFUSED"
        print(json.dumps({"schema": SCHEMA, "status": "G238_REFUSED",
                          "reason_code": code,
                          "nas_verified": False, "release_gate": "HOLD"},
                         sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
