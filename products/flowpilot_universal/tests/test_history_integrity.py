"""P85 report ledger cross-check: never trust edited evidence or report paths."""
from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from flowpilot_universal.engine import InputError
from flowpilot_universal.session import (
    HISTORY_FILE, run_session, verify_history_entry
)


class HistoricalEvidenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.source = self.base / "원본"
        self.output = self.base / "증거"
        self.source.mkdir()
        self.output.mkdir()
        (self.source / "한글 문서.txt").write_bytes(b"important unchanged source")
        self.manifest = self.base / "요구.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "expected_files": [{"path": "한글 문서.txt"}]
        }, ensure_ascii=False), encoding="utf-8")
        self.result = run_session(self.source, self.manifest, self.output, consent=True)

    def test_verified_ledger_roundtrip(self):
        checked = verify_history_entry(self.output, self.result.session_id)
        self.assertEqual(checked["status"], "READY")
        self.assertEqual(checked["reports_verified"], 2)
        self.assertEqual((self.source / "한글 문서.txt").read_bytes(),
                         b"important unchanged source")

    def test_modified_json_rejected(self):
        with self.result.json_path.open("ab") as out:
            out.write(b"\n")
        with self.assertRaises(InputError):
            verify_history_entry(self.output, self.result.session_id)

    def test_modified_html_rejected(self):
        with self.result.html_path.open("ab") as out:
            out.write(b"<script>alert('x')</script>")
        with self.assertRaises(InputError):
            verify_history_entry(self.output, self.result.session_id)

    def test_missing_session_rejected(self):
        with self.assertRaises(InputError):
            verify_history_entry(self.output, "20261113T000000.000000Z-000000000000")

    def test_invalid_session_rejected(self):
        for value in ("", "../../attack", "' OR 1=1 --", "x"*100):
            with self.assertRaises(InputError):
                verify_history_entry(self.output, value)

    def test_report_redirect_outside_folder_rejected(self):
        forged = self.base / "forged.json"
        forged.write_bytes(self.result.json_path.read_bytes())
        with closing(sqlite3.connect(self.output / HISTORY_FILE)) as db:
            db.execute("UPDATE scans SET json_path=? WHERE session_id=?",
                       (str(forged), self.result.session_id))
            db.commit()
        with self.assertRaises(InputError):
            verify_history_entry(self.output, self.result.session_id)

    def test_report_symlink_rejected(self):
        safe = self.result.html_path.read_bytes()
        self.result.html_path.unlink()
        external = self.base / "external.html"
        external.write_bytes(safe)
        try:
            self.result.html_path.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        with self.assertRaises(InputError):
            verify_history_entry(self.output, self.result.session_id)


if __name__ == "__main__":
    unittest.main()
