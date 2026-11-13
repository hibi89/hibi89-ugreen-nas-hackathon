"""Persistent offline best-effort resumable SHA checkpoint (not trusted evidence).

A checkpoint can accelerate review, but metadata is not cryptographic proof of
unchanged source bytes. Any reused SHA forces NEEDS_REVIEW; a fresh full scan is
required before READY. Checkpoints are local mutable work data, not attestation.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat

from .engine import InputError, _is_link

CHECKPOINT_FILE = ".flowpilot-resume.sqlite3"
CHECKPOINT_APP = 1179669046
MAX_ROWS = 20_000


def _stamp(info: os.stat_result) -> tuple[int, int, int, int, int]:
    # Do not mix path and FD file IDs on Windows. All signatures here are
    # obtained from the same directory-enumeration stat interface.
    if os.name == "nt":
        return (0, 0, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class ResumeCheckpoint:
    """Separate consented report-folder checkpoint; refuse foreign databases."""

    def __init__(self, directory: Path, source: Path, manifest_sha256: str):
        if not re.fullmatch(r"[0-9a-f]{64}", manifest_sha256):
            raise InputError("invalid checkpoint manifest fingerprint")
        if not directory.is_dir() or _is_link(directory.lstat()):
            raise InputError("checkpoint output must be an existing non-reparse directory")
        if not source.is_dir() or _is_link(source.lstat()):
            raise InputError("checkpoint source must be an existing non-reparse directory")
        dest = directory.resolve(strict=True)
        root = source.resolve(strict=True)
        if dest == root or root in dest.parents:
            raise InputError("checkpoint cannot reside within source root")
        self.path = dest / CHECKPOINT_FILE
        existed = os.path.lexists(self.path)
        if existed:
            info = self.path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or bool(getattr(info, "st_file_attributes", 0) &
                            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))):
                raise InputError("refusing unsafe resume checkpoint")
        else:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
            os.close(fd)
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA trusted_schema=OFF")
            if not existed:
                db.execute(f"PRAGMA application_id={CHECKPOINT_APP}")
                db.execute("PRAGMA user_version=1")
                db.execute("CREATE TABLE meta (root TEXT NOT NULL, manifest TEXT NOT NULL)")
                db.execute("""CREATE TABLE entries (
                    path TEXT PRIMARY KEY, dev INTEGER NOT NULL, inode INTEGER NOT NULL,
                    size INTEGER NOT NULL, mtime INTEGER NOT NULL, ctime INTEGER NOT NULL,
                    sha256 TEXT NOT NULL)""")
                db.execute("INSERT INTO meta VALUES (?,?)", (str(root), manifest_sha256))
                db.commit()
            else:
                if (db.execute("PRAGMA application_id").fetchone()[0] != CHECKPOINT_APP
                        or db.execute("PRAGMA user_version").fetchone()[0] != 1):
                    raise InputError("unknown or incompatible checkpoint database")
                meta = db.execute("SELECT root, manifest FROM meta").fetchall()
                if meta != [(str(root), manifest_sha256)]:
                    raise InputError("resume scope or manifest changed; use new output folder")
            self.db = db
        except BaseException:
            db.close()
            raise

    def __enter__(self) -> "ResumeCheckpoint":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.db.close()

    def lookup(self, path: str, info: os.stat_result) -> str | None:
        if not stat.S_ISREG(info.st_mode):
            return None
        row = self.db.execute(
            "SELECT dev,inode,size,mtime,ctime,sha256 FROM entries WHERE path=?",
            (path,),
        ).fetchone()
        if row is None or tuple(row[:5]) != _stamp(info):
            return None
        digest = row[5]
        if not isinstance(digest, str) or re.fullmatch("[0-9a-f]{64}", digest) is None:
            raise InputError("corrupt cached SHA256; fail closed")
        return digest

    def save(self, path: str, info: os.stat_result, digest: str) -> None:
        if not stat.S_ISREG(info.st_mode) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise InputError("unsafe checkpoint record")
        fields = _stamp(info)
        if self.db.execute("SELECT COUNT(*) FROM entries").fetchone()[0] >= MAX_ROWS:
            existing = self.db.execute("SELECT 1 FROM entries WHERE path=?", (path,)).fetchone()
            if existing is None:
                raise InputError("checkpoint row limit")
        self.db.execute(
            """INSERT INTO entries(path,dev,inode,size,mtime,ctime,sha256)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(path) DO UPDATE SET dev=excluded.dev,inode=excluded.inode,
                 size=excluded.size,mtime=excluded.mtime,ctime=excluded.ctime,
                 sha256=excluded.sha256""",
            (path, *fields, digest),
        )
        # Every completed file is durable across a process crash.
        self.db.commit()

    def count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
