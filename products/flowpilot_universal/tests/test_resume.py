"""Offline resume safety: reuse gives NEEDS_REVIEW, never READY without rehash."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from flowpilot_universal.checkpoint import CHECKPOINT_FILE, ResumeCheckpoint
from flowpilot_universal.engine import InputError
from flowpilot_universal.session import run_session


class ResumeSafetyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "source"
        self.output = self.base / "reports"
        self.root.mkdir()
        self.output.mkdir()
        (self.root / "a.txt").write_bytes(b"first")
        (self.root / "b.txt").write_bytes(b"second")
        self.manifest = self.base / "requirements.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "expected_files": [{"path": "a.txt"}, {"path": "b.txt"}]
        }), encoding="utf-8")

    def test_cancel_resume_review_then_full_ready(self):
        state = [False]
        def progress(count, _bytes):
            if count == 1:
                state[0] = True
        result = run_session(
            self.root, self.manifest, self.output, consent=True, resume=True,
            cancel=lambda: state[0], progress=progress
        )
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual((self.root / "a.txt").read_bytes(), b"first")
        with closing(sqlite3.connect(self.output / CHECKPOINT_FILE)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM entries").fetchone()[0], 1)
        from flowpilot_universal import engine
        real_hash = engine._hash_file
        hashed: list[str] = []
        def track(path, info, cancel=None):
            hashed.append(path.name)
            return real_hash(path, info, cancel)
        with patch("flowpilot_universal.engine._hash_file", side_effect=track):
            resumed = run_session(self.root, self.manifest, self.output,
                                  consent=True, resume=True)
        self.assertEqual(resumed.status, "NEEDS_REVIEW")
        self.assertEqual(hashed, ["b.txt"])
        report = json.loads(resumed.json_path.read_text(encoding="utf-8"))
        self.assertIn("RESUME_CACHE_REVIEW", [i["code"] for i in report["issues"]])
        self.assertEqual(report["safety"]["cached_files_unverified"], 1)
        fresh = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertEqual(fresh.status, "READY")
        self.assertNotEqual(fresh.json_path, result.json_path)

    def test_changed_file_rehashed_not_reused(self):
        run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        (self.root / "a.txt").write_bytes(b"changed contents")
        result = run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        self.assertEqual(result.status, "NEEDS_REVIEW")  # b.txt still cached
        report = json.loads(result.json_path.read_text(encoding="utf-8"))
        sha_a = next(r["sha256"] for r in report["files"] if r["path"] == "a.txt")
        self.assertEqual(sha_a, hashlib.sha256(b"changed contents").hexdigest())
        self.assertEqual(report["safety"]["cached_files_unverified"], 1)

    def test_manifest_scope_change_rejected_without_new_report(self):
        run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        reports = set(self.output.glob("flowpilot-*.json"))
        self.manifest.write_text(json.dumps({"schema_version": 1,
                                            "expected_files": [{"path": "a.txt"}]}), encoding="utf-8")
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        self.assertEqual(set(self.output.glob("flowpilot-*.json")), reports)

    def test_checkpoint_symlink_rejected(self):
        external = self.base / "outside.sqlite3"
        external.write_bytes(b"important")
        try:
            (self.output / CHECKPOINT_FILE).symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable on runner")
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        self.assertEqual(external.read_bytes(), b"important")

    def test_foreign_database_rejected(self):
        with closing(sqlite3.connect(self.output / CHECKPOINT_FILE)) as db:
            db.execute("CREATE TABLE foreign_data(data TEXT)")
            db.execute("INSERT INTO foreign_data VALUES ('preserve')")
            db.commit()
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        with closing(sqlite3.connect(self.output / CHECKPOINT_FILE)) as db:
            self.assertEqual(db.execute("SELECT data FROM foreign_data").fetchone()[0], "preserve")

    def test_corrupted_cached_sha_rejected(self):
        run_session(self.root, self.manifest, self.output, consent=True, resume=True)
        with closing(sqlite3.connect(self.output / CHECKPOINT_FILE)) as db:
            db.execute("UPDATE entries SET sha256='not-sha' WHERE path='a.txt'")
            db.commit()
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output, consent=True, resume=True)

    def test_resume_disabled_does_not_require_checkpoint(self):
        (self.output / CHECKPOINT_FILE).write_bytes(b"not a database")
        result = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertEqual(result.status, "READY")
        self.assertEqual((self.output / CHECKPOINT_FILE).read_bytes(), b"not a database")

    def test_checkpoint_rejects_inside_source(self):
        inside = self.root / "reports"
        inside.mkdir()
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, inside, consent=True, resume=True)


if __name__ == "__main__":
    unittest.main()
