"""Create-only local QA sessions and a consented SQLite audit trail.

No file under the scanned source root is written. Local history may contain filenames.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import Callable
from uuid import uuid4

from .engine import InputError, create_only, load_manifest, render_html, scan

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


def _safe_output(root: Path, directory: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise InputError("source must be a non-symlink authorized directory")
    if directory.is_symlink() or not directory.is_dir():
        raise InputError("output must be an existing non-symlink directory")
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
    if not path.exists():
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
) -> SessionResult:
    if consent is not True:
        raise InputError("explicit operator scope/permission confirmation required")
    output = _safe_output(root, output_dir)
    manifest = load_manifest(manifest_path)
    original_manifest = manifest_path.read_bytes()
    if len(original_manifest) > 1_048_576:
        raise InputError("manifest too large")
    manifest_sha = hashlib.sha256(original_manifest).hexdigest()
    report = scan(root, manifest, cancel=cancel, progress=progress)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    session_id = stamp + "-" + uuid4().hex[:12]
    json_path = output / ("flowpilot-" + session_id + ".json")
    html_path = output / ("flowpilot-" + session_id + ".html")
    report_text = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    report_digest = hashlib.sha256(report_text.encode("utf-8")).hexdigest()

    # Validate report destinations again after scanning, before first write.
    _safe_output(root, output)
    create_only(json_path, report_text, root)
    # If the second write fails, retain the first evidence file for manual review.
    create_only(html_path, render_html(report), root)
    history_path = output / HISTORY_FILE
    db = _history_connection(history_path)
    try:
        db.execute(
            """INSERT INTO scans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, stamp, str(root.resolve()), manifest_sha,
             report["status"], report["files_scanned"], len(report["issues"]),
             str(json_path), str(html_path), report_digest)
        )
        db.commit()
    finally:
        db.close()
    return SessionResult(session_id, report["status"], report["files_scanned"],
                         len(report["issues"]), json_path, html_path, history_path)
