"""Create-only local QA sessions and a consented SQLite audit trail.

No file under the scanned source root is written. Local history may contain filenames.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import stat
from typing import Callable
from uuid import uuid4

from .engine import InputError, _is_link, _manifest_bytes, create_only, load_manifest, render_html, scan
from .checkpoint import ResumeCheckpoint
from .pdf_report import ensure_pdf_support, render_pdf, create_pdf_only

APP_ID = 1179669045
HISTORY_FILE = ".flowpilot-history.sqlite3"


@dataclass(frozen=True)
class SessionResult:
    session_id: str
    status: str
    scanned: int
    issues: int
    json_path: Path
    html_path: Path
    history_path: Path
    pdf_path: Path | None = None


def _safe_output(root: Path, directory: Path) -> Path:
    if not root.is_dir() or _is_link(root.lstat()):
        raise InputError("source must be an authorized real non-reparse directory")
    if not directory.is_dir() or _is_link(directory.lstat()):
        raise InputError("output must be an existing real non-reparse directory")
    source = root.resolve(strict=True)
    output = directory.resolve(strict=True)
    if output == source or source in output.parents:
        raise InputError("reports/history cannot be stored inside source")
    return output


def _history_connection(path: Path) -> sqlite3.Connection:
    # Never follow a symlink or overwrite a preexisting unrelated file.
    existed = os.path.lexists(path)
    if existed:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise InputError("history path must be an unlinked regular file")
    else:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(path, flags, 0o600)
        os.close(fd)
    try:
        db = sqlite3.connect(str(path), timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA trusted_schema=OFF")
        actual_app = int(db.execute("PRAGMA application_id").fetchone()[0])
        version = int(db.execute("PRAGMA user_version").fetchone()[0])
        if existed and (actual_app != APP_ID or version != 1):
            raise InputError("refusing unknown or incompatible history database")
        if not existed:
            db.execute("PRAGMA application_id=" + str(APP_ID))
            db.execute("PRAGMA user_version=1")
            db.execute("""CREATE TABLE scans (
                session_id TEXT PRIMARY KEY, created_utc TEXT NOT NULL,
                source_root TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,
                status TEXT NOT NULL, scanned_files INTEGER NOT NULL,
                issue_count INTEGER NOT NULL, json_path TEXT NOT NULL,
                html_path TEXT NOT NULL, report_sha256 TEXT NOT NULL
            )""")
            db.commit()
        return db
    except BaseException:
        # Connection is closed by the caller only on the successful return path.
        if "db" in locals():
            db.close()
        raise


def recent_history(output_dir: Path, limit: int = 50) -> list[dict]:
    if not 1 <= limit <= 200:
        raise InputError("history limit must be 1..200")
    path = output_dir / HISTORY_FILE
    if not os.path.lexists(path):
        return []
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
        raise InputError("unsafe history file")
    db = _history_connection(path)
    try:
        rows = db.execute(
            """SELECT session_id, created_utc, status, scanned_files, issue_count,
                      json_path, html_path FROM scans
               ORDER BY created_utc DESC, session_id DESC LIMIT ?""", (limit,)
        ).fetchall()
        return [dict(zip(("session_id", "created_utc", "status", "scanned",
                          "issues", "json_path", "html_path"), row)) for row in rows]
    finally:
        db.close()


def run_session(
    root: Path, manifest_path: Path, output_dir: Path, *,
    consent: bool = False, cancel: Callable[[], bool] | None = None,
    progress: Callable[[int, int], None] | None = None,
    resume: bool = False, pdf: bool = False,
) -> SessionResult:
    if consent is not True:
        raise InputError("explicit operator scope/permission confirmation required")
    output = _safe_output(root, output_dir)
    if pdf:
        ensure_pdf_support()  # Refuse before reading source or creating reports when PDF is unavailable.
    manifest, original_manifest = load_manifest(manifest_path, include_bytes=True)
    manifest_sha = hashlib.sha256(original_manifest).hexdigest()
    if resume:
        with ResumeCheckpoint(output, root, manifest_sha) as checkpoint:
            report = scan(root, manifest, cancel=cancel, progress=progress,
                          resume_lookup=checkpoint.lookup, checkpoint_save=checkpoint.save)
    else:
        report = scan(root, manifest, cancel=cancel, progress=progress)
    if _manifest_bytes(manifest_path) != original_manifest:
        raise InputError("requirements manifest changed during scan; no report published")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    session_id = stamp + "-" + uuid4().hex[:12]
    json_path = output / ("flowpilot-" + session_id + ".json")
    html_path = output / ("flowpilot-" + session_id + ".html")
    pdf_path = output / ("flowpilot-" + session_id + ".pdf") if pdf else None
    pdf_bytes = render_pdf(report) if pdf else None
    report_text = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    report_digest = hashlib.sha256(report_text.encode("utf-8")).hexdigest()

    # Validate report destinations again after scanning, before first write.
    _safe_output(root, output)
    create_only(json_path, report_text, root)
    # If the second write fails, retain the first evidence file for manual review.
    create_only(html_path, render_html(report), root)
    if pdf_path is not None and pdf_bytes is not None:
        create_pdf_only(pdf_path, pdf_bytes, root)
    history_path = output / HISTORY_FILE
    db = _history_connection(history_path)
    try:
        db.execute(
            """INSERT INTO scans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, stamp, str(root.resolve()), manifest_sha,
             report["status"], report["files_scanned"], len(report["issues"]),
             str(json_path), str(html_path), report_digest)
        )
        if pdf_path is not None and pdf_bytes is not None:
            db.execute("""CREATE TABLE IF NOT EXISTS pdf_evidence (
                session_id TEXT PRIMARY KEY, pdf_path TEXT NOT NULL,
                pdf_sha256 TEXT NOT NULL
            )""")
            db.execute("INSERT INTO pdf_evidence VALUES (?,?,?)",
                       (session_id, str(pdf_path), hashlib.sha256(pdf_bytes).hexdigest()))
        db.commit()
    finally:
        db.close()
    return SessionResult(session_id, report["status"], report["files_scanned"],
                         len(report["issues"]), json_path, html_path, history_path, pdf_path)


def backup_history(output_dir: Path) -> Path:
    """User-triggered create-only online SQLite backup; never modifies prior backups.

    A failed copy stays on disk for inspection rather than being silently deleted.
    Restore is deliberately manual into a fresh location (no destructive restore).
    """
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise InputError("backup destination must be an existing local directory")
    history = output_dir / HISTORY_FILE
    if not os.path.lexists(history):
        raise InputError("no audit history to back up")
    source = _history_connection(history)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = output_dir / ("flowpilot-history-backup-" + stamp + "-" + uuid4().hex[:8] + ".sqlite3")
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(backup, flags, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(str(backup), timeout=5)) as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise InputError("backup integrity check failed")
            if (int(target.execute("PRAGMA application_id").fetchone()[0]) != APP_ID
                    or int(target.execute("PRAGMA user_version").fetchone()[0]) != 1):
                raise InputError("backup format check failed")
        return backup
    finally:
        source.close()



def _evidence_bytes(path: Path, output_dir: Path) -> bytes:
    """Read bounded local evidence with no symlink/hardlink or path escape."""
    if path.parent.resolve(strict=True) != output_dir.resolve(strict=True):
        raise InputError("historical report path escapes output directory")
    try:
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or bool(getattr(info, "st_file_attributes", 0) &
                        getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
                or info.st_size > 20 * 1024 * 1024):
            raise InputError("unsafe historical report")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != info.st_size:
                raise InputError("historical report changed before read")
            payload = stream.read(20 * 1024 * 1024 + 1)
            if (len(payload) != info.st_size or
                    os.fstat(stream.fileno()).st_size != info.st_size):
                raise InputError("historical report changed during read")
        return payload
    except OSError as exc:
        raise InputError("historical report is missing or inaccessible") from exc


def verify_history_entry(output_dir: Path, session_id: str) -> dict:
    """Recheck saved JSON SHA and HTML parity without touching source files.

    This is local report integrity, NOT source authenticity or signed evidence.
    """
    if not re.fullmatch(r"\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{12}", session_id):
        raise InputError("invalid session identifier")
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise InputError("invalid history destination")
    path = output_dir / HISTORY_FILE
    if not os.path.lexists(path):
        raise InputError("no audit history found")
    db = _history_connection(path)
    try:
        row = db.execute(
            """SELECT status, scanned_files, issue_count, json_path,
                      html_path, report_sha256 FROM scans WHERE session_id=?""",
            (session_id,)
        ).fetchone()
        pdf_row = None
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pdf_evidence'").fetchone():
            pdf_row = db.execute("SELECT pdf_path, pdf_sha256 FROM pdf_evidence WHERE session_id=?",
                                 (session_id,)).fetchone()
    finally:
        db.close()
    if row is None:
        raise InputError("audit session was not found")
    status, count, issue_count, json_path, html_path, stored_sha = row
    raw = _evidence_bytes(Path(json_path), output_dir)
    if not isinstance(stored_sha, str) or hashlib.sha256(raw).hexdigest() != stored_sha:
        raise InputError("historical JSON evidence SHA mismatch")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("historical JSON evidence invalid") from exc
    if (not isinstance(report, dict) or report.get("status") != status
            or report.get("files_scanned") != count
            or len(report.get("issues", [])) != issue_count):
        raise InputError("historical JSON and audit row disagree")
    html = _evidence_bytes(Path(html_path), output_dir)
    if html != render_html(report).encode("utf-8"):
        raise InputError("historical HTML differs from its JSON evidence")
    verified = 2
    if pdf_row is not None:
        pdf_path, expected_pdf_sha = pdf_row
        if not isinstance(pdf_path, str) or not isinstance(expected_pdf_sha, str):
            raise InputError("invalid PDF ledger fields")
        raw_pdf = _evidence_bytes(Path(pdf_path), output_dir)
        if (not raw_pdf.startswith(b"%PDF-") or b"%%EOF" not in raw_pdf[-128:]
                or hashlib.sha256(raw_pdf).hexdigest() != expected_pdf_sha):
            raise InputError("PDF evidence checksum or structure mismatch")
        verified += 1
    return {"session_id": session_id, "status": status,
            "sha256": stored_sha, "reports_verified": verified}
