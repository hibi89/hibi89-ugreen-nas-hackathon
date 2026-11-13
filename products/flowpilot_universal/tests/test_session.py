"""P70 synthetic-only desktop/session regressions, no real NAS or customer data."""
import json
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowpilot_universal.engine import InputError, load_manifest, scan
from flowpilot_universal.session import (
    APP_ID, HISTORY_FILE, backup_history, recent_history, run_session
)


class UniversalSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "프로젝트"
        self.output = self.base / "보고서"
        self.root.mkdir()
        self.output.mkdir()
        self.manifest = self.base / "요구.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "expected_files": [{"path": "납품.txt"}]
        }), encoding="utf-8")
        (self.root / "납품.txt").write_bytes(b"final bytes")

    def test_consent_gate(self):
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_report_and_database_roundtrip(self):
        before = (self.root / "납품.txt").read_bytes()
        result = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertEqual(result.status, "READY")
        self.assertEqual((self.root / "납품.txt").read_bytes(), before)
        self.assertTrue(result.html_path.is_file())
        self.assertIn("default-src 'none'", result.html_path.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(result.json_path.read_text(encoding="utf-8"))["status"], "READY")
        records = recent_history(self.output)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "READY")
        with closing(sqlite3.connect(result.history_path)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("PRAGMA application_id").fetchone()[0], APP_ID)

    def test_repeat_is_create_only_and_preserves_old_reports(self):
        first = run_session(self.root, self.manifest, self.output, consent=True)
        original = first.json_path.read_bytes()
        second = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertNotEqual(first.json_path, second.json_path)
        self.assertEqual(first.json_path.read_bytes(), original)
        self.assertEqual(len(recent_history(self.output)), 2)

    def test_cancel_creates_incomplete_evidence_no_ready(self):
        result = run_session(self.root, self.manifest, self.output, consent=True, cancel=lambda: True)
        data = json.loads(result.json_path.read_text(encoding="utf-8"))
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertIn("SCAN_INTERRUPTED", [i["code"] for i in data["issues"]])
        self.assertEqual(recent_history(self.output)[0]["status"], "INCOMPLETE")
        self.assertEqual((self.root / "납품.txt").read_bytes(), b"final bytes")

    def test_cancel_during_read_is_incomplete(self):
        chunks = [False, True, True, True]
        def cancellation():
            return chunks.pop(0) if chunks else True
        result = run_session(self.root, self.manifest, self.output, consent=True, cancel=cancellation)
        self.assertEqual(result.status, "INCOMPLETE")

    def test_progress_is_counted_without_source_mutation(self):
        seen = []
        run_session(self.root, self.manifest, self.output, consent=True,
                    progress=lambda count, size: seen.append((count, size)))
        self.assertEqual(seen[-1], (1, len(b"final bytes")))

    def test_output_inside_source_refused(self):
        inside = self.root / "reports"
        inside.mkdir()
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, inside, consent=True)
        self.assertEqual(list(inside.iterdir()), [])

    def test_symlink_output_refused(self):
        pointer = self.base / "pointer"
        try:
            pointer.symlink_to(self.output, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable on runner")
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, pointer, consent=True)

    def test_unsafe_history_refused_no_overwrite(self):
        foreign = self.output / HISTORY_FILE
        foreign.write_bytes(b"not our SQLite database")
        before = foreign.read_bytes()
        with self.assertRaises((InputError, sqlite3.DatabaseError)):
            run_session(self.root, self.manifest, self.output, consent=True)
        self.assertEqual(foreign.read_bytes(), before)

    def test_unknown_sqlite_history_refused(self):
        foreign = self.output / HISTORY_FILE
        with closing(sqlite3.connect(foreign)) as db:
            db.execute("CREATE TABLE unrelated (id INTEGER)")
        with self.assertRaises(InputError):
            run_session(self.root, self.manifest, self.output, consent=True)
        with closing(sqlite3.connect(foreign)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM unrelated").fetchone()[0], 0)

    def test_directory_change_detection(self):
        cfg = load_manifest(self.manifest)
        original = os.scandir
        calls = [0]
        def injected(path):
            # The synthetic fixture has only this one scanned directory.
            # Windows resolve() may change 8.3 spelling, so count scandir calls.
            calls[0] += 1
            if calls[0] == 2:
                (self.root / "late.txt").write_text("late", encoding="utf-8")
            return original(path)
        with patch("flowpilot_universal.engine.os.scandir", side_effect=injected):
            report = scan(self.root, cfg)
        # Final post-scan verification may perform a third scandir on Windows.
        self.assertGreaterEqual(calls[0], 2)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("DIRECTORY_CHANGED", [i["code"] for i in report["issues"]])

    def test_history_backup_create_only(self):
        run_session(self.root, self.manifest, self.output, consent=True)
        first = backup_history(self.output)
        original = first.read_bytes()
        second = backup_history(self.output)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        with closing(sqlite3.connect(first)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM scans").fetchone()[0], 1)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_history_backup_requires_existing_history(self):
        with self.assertRaises(InputError):
            backup_history(self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_directory_count_bound(self):
        (self.root / "sub").mkdir()
        cfg = load_manifest(self.manifest)
        with patch("flowpilot_universal.engine.MAX_DIRECTORIES", 1):
            self.assertEqual(scan(self.root, cfg)["status"], "INCOMPLETE")

    def test_python_desktop_module_import_headless(self):
        from flowpilot_universal import gui
        self.assertTrue(callable(gui.main))
        self.assertTrue(hasattr(gui, "App"))


if __name__ == "__main__":
    unittest.main()
