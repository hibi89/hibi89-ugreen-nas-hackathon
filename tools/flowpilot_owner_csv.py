"""Owner-consented LOCAL CSV aggregation with a real output and audit receipt.

This is a file-content feature (unlike read-only lstat). Source CSV content is
read ONLY after explicit independent execution consent; metadata preview is
separately acknowledged. No NAS/Uliya, internet, private repositories, uploads,
customer rows in API responses, or overwrites.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import secrets
import sys
from tempfile import TemporaryDirectory
from threading import RLock

PROJECT = Path(__file__).resolve().parents[1]
for folder in (PROJECT, PROJECT / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from flowpilot_csv_e2e import run_session
from flowpilot_csv_report import ReportRefused
from flowpilot_owner_local_audit import _valid_root, OwnerAuditError

GOAL = "고객별 매출 보고서 만들어줘"
CONSENT = "APPROVE_LOCAL_CSV_CONTENT_READ_AND_NEW_OUTPUT_WRITE"
FILE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.csv\Z")
COL = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")
MAX_REPORT_BYTES = 4_000_000


class OwnerCSVRefused(ValueError):
    """Privacy-safe error code; does not echo private paths or contents."""


def _request_fields(raw: object) -> tuple[Path, tuple[str, ...], str, str, str]:
    if type(raw) is not dict or set(raw) != {
        "root", "sources", "output", "group", "amount", "local_metadata_ack"
    } or raw["local_metadata_ack"] is not True:
        raise OwnerCSVRefused("LOCAL_METADATA_PREVIEW_ACK_REQUIRED")
    root, sources, output, group, amount = (
        raw["root"], raw["sources"], raw["output"], raw["group"], raw["amount"]
    )
    if type(root) is not str or not 0 < len(root) <= 2048 or root != root.strip():
        raise OwnerCSVRefused("INVALID_LOCAL_ROOT")
    if type(sources) is not list or not 1 <= len(sources) <= 5:
        raise OwnerCSVRefused("INVALID_SOURCE_COUNT")
    if (any(type(x) is not str or FILE.fullmatch(x) is None for x in sources)
            or len(set(sources)) != len(sources)
            or type(output) is not str or FILE.fullmatch(output) is None
            or output in sources
            or type(group) is not str or COL.fullmatch(group) is None
            or type(amount) is not str or COL.fullmatch(amount) is None
            or group == amount):
        raise OwnerCSVRefused("INVALID_BOUNDED_CSV_FIELDS")
    path = Path(root)
    if not path.is_absolute():
        raise OwnerCSVRefused("ABSOLUTE_LOCAL_DIRECTORY_REQUIRED")
    return path, tuple(sources), output, group, amount


def _stat_source(root: Path, name: str) -> tuple[int, int, int, int]:
    path = root / name
    try:
        if path.is_symlink() or not path.is_file():
            raise OwnerCSVRefused("SOURCE_NOT_SAFE")
        info = path.lstat()
        if not 0 < info.st_size <= 8_000_000:
            raise OwnerCSVRefused("SOURCE_BYTES_OUT_OF_BOUNDS")
    except OSError:
        raise OwnerCSVRefused("SOURCE_UNAVAILABLE") from None
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


class OwnerCSV:
    """Local process memory keeps the exact approved scope and a one-use token."""

    def __init__(self):
        self._lock = RLock()
        self._temp = TemporaryDirectory(prefix="flowpilot-owner-local-csv-audit-")
        self._audit_db = Path(self._temp.name) / "audit.sqlite"
        self._pending = None
        self._executed = False
        self._complete = None
        self._closed = False

    def close(self):
        with self._lock:
            if not self._closed:
                self._closed = True
                self._pending = None
                self._temp.cleanup()

    def preview(self, request: object) -> dict:
        root, sources, output, group, amount = _request_fields(request)
        with self._lock:
            if self._closed or self._executed:
                raise OwnerCSVRefused("START_NEW_SESSION_FOR_ANOTHER_CSV_REPORT")
            self._pending = None
            try:
                _valid_root(root)  # explicitly acknowledged metadata inspection
                stats = tuple(_stat_source(root, name) for name in sources)
                result = run_session(
                    GOAL, root=root, sources=list(sources), output=output,
                    group=group, amount=amount,
                )
            except (OwnerAuditError, OSError, ReportRefused, ValueError, TypeError):
                raise OwnerCSVRefused("LOCAL_CSV_PREVIEW_REFUSED") from None
            if (result.get("status") != "WAITING_EXECUTION_APPROVAL"
                    or result.get("executed") is not False
                    or (root / output).exists()):
                raise OwnerCSVRefused("UNSAFE_LOCAL_CSV_PLAN")
            token = secrets.token_hex(24)
            self._pending = (root, sources, output, group, amount, stats, token)
            return {
                "status": "WAITING_EXPLICIT_CSV_CONTENT_APPROVAL",
                "approval_token": token,
                "source_count": len(sources),
                "output_will_be_new": True,
                "group_column_defined": True,
                "amount_column_defined": True,
                "source_contents_read": False,
                "created_output": False,
                "actual_nas_verified": False,
                "release_gate": "HOLD",
            }

    def execute(self, approval_token: object, consent: object) -> dict:
        with self._lock:
            if self._closed or self._executed or self._pending is None:
                raise OwnerCSVRefused("NO_PENDING_CSV_APPROVAL")
            root, sources, output, group, amount, stats, expected = self._pending
            if (type(approval_token) is not str or type(consent) is not str
                    or not secrets.compare_digest(approval_token, expected)
                    or consent != CONSENT):
                raise OwnerCSVRefused("EXPLICIT_CSV_CONTENT_CONSENT_REQUIRED")
            self._pending = None
            self._executed = True  # consume even if source fails or changes
            try:
                _valid_root(root)
                if tuple(_stat_source(root, name) for name in sources) != stats:
                    raise OwnerCSVRefused("SOURCE_CHANGED_AFTER_PREVIEW")
                if (root / output).exists() or (root / output).is_symlink():
                    raise OwnerCSVRefused("OUTPUT_WOULD_OVERWRITE")
                row = run_session(
                    GOAL, root=root, sources=list(sources), output=output,
                    group=group, amount=amount, approval="APPROVE_EXECUTION",
                    audit_db=self._audit_db,
                )
                receipt = row.get("execution", {}).get("result", {})
                audit = row.get("audit", {})
                digest = receipt.get("report_sha256")
                if (row.get("status") != "LOCAL_REPORT_CREATED_NOT_NAS"
                        or row.get("executed") is not True
                        or row.get("nas_verified") is not False
                        or type(audit) is not dict or audit.get("count") != 1
                        or type(digest) is not str
                        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
                        or type(receipt.get("rows")) is not int
                        or type(receipt.get("groups")) is not int
                        or not 0 < receipt["rows"] <= 100_000
                        or not 0 < receipt["groups"] <= receipt["rows"]):
                    raise OwnerCSVRefused("LOCAL_CSV_RECEIPT_UNVERIFIED")
                file = root / output
                if file.is_symlink() or not file.is_file() or not (
                    0 < file.stat().st_size <= MAX_REPORT_BYTES
                ):
                    raise OwnerCSVRefused("LOCAL_CSV_OUTPUT_UNAVAILABLE")
                if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                    raise OwnerCSVRefused("LOCAL_CSV_DIGEST_MISMATCH")
                self._complete = (file, digest)
                return {
                    "status": "LOCAL_CSV_CREATED_WITH_SQLITE_AUDIT",
                    "source_count": len(sources), "rows_read": receipt["rows"],
                    "groups_written": receipt["groups"],
                    "report_sha256": digest,
                    "audit_recorded": True, "local_csv_download_ready": True,
                    "report_contains_owner_data": True,
                    "actual_la_integrated": False, "actual_sovia_integrated": False,
                    "actual_dbvora_integrated": False, "actual_nas_verified": False,
                    "registered_uliya_expert_invoked": False, "release_gate": "HOLD",
                }
            except OwnerCSVRefused:
                raise
            except (OwnerAuditError, ReportRefused, OSError, TypeError, ValueError):
                raise OwnerCSVRefused("LOCAL_CSV_EXECUTION_REFUSED") from None

    def cancel(self) -> dict:
        with self._lock:
            if self._pending is None or self._executed:
                raise OwnerCSVRefused("NO_CSV_PLAN_TO_CANCEL")
            self._pending = None
            return {
                "status": "LOCAL_CSV_PLAN_CANCELLED", "output_created": False,
                "actual_nas_verified": False, "release_gate": "HOLD",
            }

    def start_new_report(self) -> dict:
        """Explicitly re-arm a new approval after a completed/failed run.

        Keep previous owner output untouched. Previous report download
        becomes unavailable; a fresh isolated audit database is used.
        """
        with self._lock:
            if self._closed:
                raise OwnerCSVRefused("CLOSED_LOCAL_CSV_SESSION")
            if not self._executed:
                raise OwnerCSVRefused("NO_PREVIOUS_CSV_EXECUTION")
            self._pending = None
            self._complete = None
            self._audit_db = Path(self._temp.name) / (
                "audit-" + secrets.token_hex(12) + ".sqlite"
            )
            self._executed = False
            return {
                "status": "READY_FOR_NEW_LOCAL_CSV_PREVIEW",
                "approval_required_again": True,
                "previous_owner_output_preserved": True,
                "previous_download_revoked": True,
                "actual_nas_verified": False,
                "release_gate": "HOLD",
            }

    def download(self) -> bytes:
        with self._lock:
            if self._closed or self._complete is None:
                raise OwnerCSVRefused("NO_APPROVED_CSV_OUTPUT")
            path, expected = self._complete
            if (path.is_symlink() or not path.is_file() or not
                    (0 < path.stat().st_size <= MAX_REPORT_BYTES)):
                raise OwnerCSVRefused("CSV_OUTPUT_MODIFIED")
            contents = path.read_bytes()
            if hashlib.sha256(contents).hexdigest() != expected:
                raise OwnerCSVRefused("CSV_OUTPUT_MODIFIED")
            return contents
