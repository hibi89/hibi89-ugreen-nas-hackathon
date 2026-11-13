"""Synthetic final-read consistency checks on both CI operating systems.

Final source relist/lstat detects common after-hash edits; it is not an atomic
snapshot and cannot defeat an attacker able to forge timestamp/metadata.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from flowpilot_universal.engine import load_manifest, scan
from flowpilot_universal.session import run_session


class FinalRecheckTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base / "source"
        self.output = self.base / "output"
        self.root.mkdir()
        self.output.mkdir()
        (self.root / "a.txt").write_bytes(b"original first")
        (self.root / "b.txt").write_bytes(b"original second")
        self.manifest = self.base / "manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "expected_files": [{"path": "a.txt"}, {"path": "b.txt"}]
        }), encoding="utf-8")

    def test_first_file_changed_after_first_hash_is_incomplete(self):
        def change_first(scanned, seen):
            if scanned == 2:
                (self.root / "a.txt").write_bytes(b"AFTER-LAST-FILE-IS-HASHED-CHANGED")
        report = scan(self.root, load_manifest(self.manifest), progress=change_first)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("FILE_CHANGED_AFTER_SCAN",
                      {issue["code"] for issue in report["issues"]})
        first = next(rec for rec in report["files"] if rec["path"] == "a.txt")
        self.assertEqual(first["sha256"], hashlib.sha256(b"original first").hexdigest())

    def test_directory_addition_after_last_hash_is_incomplete(self):
        def change_dir(scanned, seen):
            if scanned == 2:
                (self.root / "new_unexpected.txt").write_bytes(b"new")
        report = scan(self.root, load_manifest(self.manifest), progress=change_dir)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertTrue({"DIRECTORY_CHANGED", "DIRECTORY_CHANGED_FINAL"}
                        & {issue["code"] for issue in report["issues"]})
        self.assertEqual(report["files_scanned"], 2)

    def test_no_mutation_stays_ready_and_session_evidence_matches(self):
        direct = scan(self.root, load_manifest(self.manifest))
        self.assertEqual(direct["status"], "READY")
        result = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertEqual(result.status, "READY")
        saved = json.loads(result.json_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "READY")
        self.assertEqual((self.root / "a.txt").read_bytes(), b"original first")

    def test_nested_directory_modified_during_scan_refused(self):
        folder = self.root / "nested"
        folder.mkdir()
        (folder / "c.txt").write_bytes(b"c")
        def change(scanned, seen):
            if scanned == 3:
                (self.root / "a.txt").write_bytes(b"another change longer than original")
        report = scan(self.root, load_manifest(self.manifest), progress=change)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("FILE_CHANGED_AFTER_SCAN",
                      {issue["code"] for issue in report["issues"]})


if __name__ == "__main__":
    unittest.main()
