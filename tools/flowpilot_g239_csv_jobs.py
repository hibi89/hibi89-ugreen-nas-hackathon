"""G239: separately-approved, redacted, durable LOCAL CSV job gateway.

Preview holds owner-selected paths in server memory for <=600s only.
A new create-only companion SQLite records only job IDs, plan digests and
redacted receipts, never paths, source CSV, group labels or report bytes.
Reserve before any real read; uncertain/failed states MUST NOT auto-retry.
No NAS, Uliya, cloud, Docker, input writes, export or background tasks.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import threading
import time

from flowpilot_g238_local_csv_engine import (
    LocalCsvRefused, READ_ACK, execute, preview,
)

SCHEMA = "flowpilot-g239-local-csv-job-v1"
IDENTITY = "flowpilot-g239-local-csv-jobs-v1"
REQUEST = re.compile(r"csv_[0-9a-f]{24}\Z")
PREVIEW = re.compile(r"cpre_[0-9a-f]{32}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TTL_SECONDS = 600


class CsvJobRefused(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


def _json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("ascii")).hexdigest()


class LocalCsvJobs:
    def __init__(self, original_db: Path):
        # The G161 database itself is NEVER migrated by G239.
        self.path = original_db.with_name(original_db.stem + "-csv-g239.sqlite")
        self.lock = threading.RLock()
        self.tickets: dict[str, tuple[str, str, str, float]] = {}

    def _guard(self, *, required: bool) -> None:
        path = self.path
        if (not path.is_absolute() or path.suffix != ".sqlite" or
                str(path).startswith(("//", "\\\\"))):
            raise CsvJobRefused("G239_SIDECAR_PATH_REFUSED")
        for part in (path.parent, *path.parent.parents):
            if part.is_symlink() or not part.is_dir():
                raise CsvJobRefused("G239_SIDECAR_PARENT_REFUSED")
        if not required and not path.exists() and not path.is_symlink():
            return
        try:
            item = path.lstat()
        except OSError as exc:
            raise CsvJobRefused("G239_SIDECAR_NOT_FOUND", 404) from exc
        if (not stat.S_ISREG(item.st_mode) or item.st_size > 4 * 1024 * 1024
                or (os.name != "nt" and item.st_nlink != 1)):
            raise CsvJobRefused("G239_SIDECAR_UNSAFE")

    def _connect(self):
        self._guard(required=True)
        try:
            db = sqlite3.connect(self.path.as_uri() + "?mode=rw",
                                 uri=True, timeout=3)
            db.execute("PRAGMA busy_timeout=3000")
            identity = db.execute(
                "SELECT value FROM g239_meta WHERE key='identity'").fetchone()
            if identity != (IDENTITY,):
                db.close()
                raise CsvJobRefused("G239_SIDECAR_IDENTITY_MISMATCH")
            return db
        except sqlite3.Error as exc:
            raise CsvJobRefused("G239_SIDECAR_OPEN_REFUSED") from exc

    def _initialize_only_on_approval(self) -> None:
        self._guard(required=False)
        if self.path.exists():
            # No schema migration or source overwrite, even on legacy data.
            with closing(self._connect()):
                return
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self.path, flags, 0o600)
        except FileExistsError:
            with closing(self._connect()):
                return
        except OSError as exc:
            raise CsvJobRefused("G239_EXCLUSIVE_SIDECAR_CREATE_REFUSED") from exc
        os.close(fd)
        try:
            with closing(sqlite3.connect(self.path)) as db:
                db.execute("CREATE TABLE g239_meta (key TEXT PRIMARY KEY,"
                           " value TEXT NOT NULL)")
                db.execute("INSERT INTO g239_meta VALUES ('identity',?)",
                           (IDENTITY,))
                db.execute("CREATE TABLE g239_jobs ("
                           "job_id TEXT PRIMARY KEY, plan_sha TEXT NOT NULL,"
                           " state TEXT NOT NULL, receipt_json TEXT,"
                           " receipt_sha TEXT)")
                db.commit()
        except sqlite3.Error as exc:
            raise CsvJobRefused("G239_SIDECAR_INITIALIZATION_REFUSED") from exc

    def preview(self, input_path: str, group_column: str) -> dict:
        # G238 preview never even stats the operator-selected input.
        contract = preview(input_path, group_column)
        with self.lock:
            now = time.monotonic()
            self.tickets = {
                key: value for key, value in self.tickets.items()
                if value[3] > now
            }
            if len(self.tickets) >= 8:
                raise CsvJobRefused("G239_TOO_MANY_LIVE_PREVIEWS", 429)
            ticket = "cpre_" + secrets.token_hex(16)
            self.tickets[ticket] = (
                input_path, group_column, contract["plan_sha256"],
                now + TTL_SECONDS,
            )
        return {
            **contract, "preview_id": ticket,
            "status": "WAITING_EXPLICIT_LOCAL_CSV_JOB_APPROVAL",
            "read_consent_includes_redacted_local_receipt": True,
            "raw_input_path_in_response": False,
            "preview_expires_after_seconds": TTL_SECONDS,
        }

    @staticmethod
    def _decode(row: tuple, job_id: str) -> dict:
        stored_id, plan_sha, state, payload, checksum = row
        if (stored_id != job_id or not REQUEST.fullmatch(stored_id)
                or not SHA.fullmatch(plan_sha)
                or state not in ("RESERVED", "COMPLETE", "BLOCKED")):
            raise CsvJobRefused("G239_RECEIPT_STATE_CORRUPT")
        if state == "RESERVED":
            if payload is not None or checksum is not None:
                raise CsvJobRefused("G239_RESERVATION_CORRUPT")
            return {
                "schema": SCHEMA, "request_id": job_id,
                "plan_sha256": plan_sha,
                "status": "RUN_RESERVED_UNCERTAIN_NO_AUTORETRY",
                "nas_verified": False, "release_gate": "HOLD",
            }
        if state == "BLOCKED":
            if payload is not None or checksum is not None:
                raise CsvJobRefused("G239_BLOCKED_RECEIPT_CORRUPT")
            return {
                "schema": SCHEMA, "request_id": job_id,
                "plan_sha256": plan_sha,
                "status": "LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY",
                "nas_verified": False, "release_gate": "HOLD",
            }
        if (type(payload) is not str or type(checksum) is not str
                or not SHA.fullmatch(checksum) or
                _hash(payload) != checksum or len(payload) > 8192):
            raise CsvJobRefused("G239_RECEIPT_DIGEST_MISMATCH")
        try:
            result = json.loads(payload)
        except ValueError as exc:
            raise CsvJobRefused("G239_INVALID_RECEIPT") from exc
        if (type(result) is not dict or result.get("schema") != SCHEMA
                or result.get("status") != "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS"
                or result.get("request_id") != job_id
                or result.get("plan_sha256") != plan_sha
                or result.get("path_and_labels_persisted") is not False
                or result.get("nas_verified") is not False
                or result.get("release_gate") != "HOLD"
                or type(result.get("result")) is not dict
                or result["result"].get("nas_verified") is not False
                or result["result"].get("owner_source_modified") is not False):
            raise CsvJobRefused("G239_RECEIPT_CLAIM_REFUSED")
        return result

    def recent(self) -> dict:
        """Authenticated operator review: last 10 persisted IDs, no owner CSV I/O.

        Never create a companion DB for a read-only history request. Validate
        every selected receipt with the existing G239 integrity gate, and
        expose only allowlisted status/count metadata.
        """
        with self.lock:
            self._guard(required=False)
            entries = []
            if self.path.exists():
                with closing(self._connect()) as connection:
                    rows = connection.execute(
                        "SELECT job_id,plan_sha,state,receipt_json,receipt_sha"
                        " FROM g239_jobs ORDER BY rowid DESC LIMIT 10").fetchall()
                for row in rows:
                    verified = self._decode(row, row[0])
                    summary = {
                        "request_id": verified["request_id"],
                        "status": verified["status"],
                    }
                    if verified["status"] == "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS":
                        data = verified["result"]
                        if (type(data.get("group_count")) is not int or
                                type(data.get("source_rows")) is not int or
                                not 1 <= data["group_count"] <= 32 or
                                not 1 <= data["source_rows"] <= 256):
                            raise CsvJobRefused("G243_RECEIPT_COUNTS_REFUSED")
                        summary["group_count"] = data["group_count"]
                        summary["source_rows"] = data["source_rows"]
                    entries.append(summary)
            return {
                "schema": "flowpilot-g243-csv-history-v1",
                "status": "LOCAL_CSV_HISTORY_NOT_NAS",
                "jobs": entries,
                "count": len(entries),
                "max_returned": 10,
                "read_only": True,
                "source_files_accessed": False,
                "nas_verified": False,
                "release_gate": "HOLD",
            }

    def readback(self, job_id: str) -> dict:
        if type(job_id) is not str or not REQUEST.fullmatch(job_id):
            raise CsvJobRefused("G239_INVALID_REQUEST_ID", 400)
        with self.lock:
            self._guard(required=False)
            if not self.path.exists():
                raise CsvJobRefused("G239_JOB_NOT_FOUND", 404)
            with closing(self._connect()) as db:
                row = db.execute(
                    "SELECT job_id,plan_sha,state,receipt_json,receipt_sha"
                    " FROM g239_jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise CsvJobRefused("G239_JOB_NOT_FOUND", 404)
            return self._decode(row, job_id)

    def run(self, preview_id: str, request_id: str, plan_sha256: str,
            acknowledgement: str) -> dict:
        # Validate exact user approval BEFORE any disk creation/read.
        if (type(preview_id) is not str or not PREVIEW.fullmatch(preview_id)
                or type(request_id) is not str or not REQUEST.fullmatch(request_id)
                or type(plan_sha256) is not str or not SHA.fullmatch(plan_sha256)
                or type(acknowledgement) is not str or
                acknowledgement != READ_ACK):
            raise CsvJobRefused("G239_EXACT_APPROVAL_REQUIRED", 403)
        with self.lock:
            # First reconcile a lost response by ID. NEVER rerun the source.
            try:
                existing = self.readback(request_id)
            except CsvJobRefused as exc:
                if exc.code != "G239_JOB_NOT_FOUND":
                    raise
                existing = None
            if existing is not None:
                if existing["plan_sha256"] != plan_sha256:
                    raise CsvJobRefused("G239_IDEMPOTENCY_CONFLICT")
                return existing
            ticket = self.tickets.get(preview_id)
            if (ticket is None or ticket[3] <= time.monotonic()
                    or ticket[2] != plan_sha256):
                raise CsvJobRefused("G239_STALE_OR_MISMATCHED_TICKET", 403)
            # One use, even if the subsequent I/O returns an uncertain result.
            del self.tickets[preview_id]
            source, group, _, _ = ticket
            self._initialize_only_on_approval()
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                # SQLite UNIQUE prevents duplicates even across processes.
                old = db.execute(
                    "SELECT job_id,plan_sha,state,receipt_json,receipt_sha"
                    " FROM g239_jobs WHERE job_id=?", (request_id,)).fetchone()
                if old is not None:
                    db.commit()
                    if old[1] != plan_sha256:
                        raise CsvJobRefused("G239_IDEMPOTENCY_CONFLICT")
                    return self._decode(old, request_id)
                db.execute(
                    "INSERT INTO g239_jobs VALUES (?,?, 'RESERVED',NULL,NULL)",
                    (request_id, plan_sha256))
                db.commit()
            try:
                report = execute(source, group, plan_sha256, READ_ACK)
                if report.get("nas_verified") is not False:
                    raise CsvJobRefused("G239_NATIVE_CLAIM_REFUSED")
                receipt = {
                    "schema": SCHEMA,
                    "status": "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS",
                    "request_id": request_id,
                    "plan_sha256": plan_sha256,
                    "result": report,
                    "path_and_labels_persisted": False,
                    "source_file_reopened_on_readback": False,
                    "attempts": 1,
                    "nas_verified": False, "release_gate": "HOLD",
                }
                body = _json(receipt)
                with closing(self._connect()) as db:
                    db.execute("BEGIN IMMEDIATE")
                    count = db.execute(
                        "UPDATE g239_jobs SET state='COMPLETE',"
                        " receipt_json=?, receipt_sha=?"
                        " WHERE job_id=? AND state='RESERVED'",
                        (body, _hash(body), request_id)).rowcount
                    if count != 1:
                        raise CsvJobRefused("G239_RESERVATION_LOST")
                    db.commit()
                return receipt
            except (LocalCsvRefused, CsvJobRefused, OSError, sqlite3.Error):
                # A failed/ambiguous run becomes permanently BLOCKED. Manual
                # re-preview + new job ID is required; never autoretry.
                try:
                    with closing(self._connect()) as db:
                        db.execute("UPDATE g239_jobs SET state='BLOCKED'"
                                   " WHERE job_id=? AND state='RESERVED'",
                                   (request_id,))
                        db.commit()
                except (CsvJobRefused, OSError, sqlite3.Error):
                    pass
                raise CsvJobRefused("G239_LOCAL_CSV_EXECUTION_BLOCKED")
