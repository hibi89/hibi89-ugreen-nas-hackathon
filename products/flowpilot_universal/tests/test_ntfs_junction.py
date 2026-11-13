"""Actual NTFS junction safety checks on Windows hosted runner.

Creates only synthetic local junctions in a TemporaryDirectory. Does not
change system share permissions, use SMB admin credentials or real NAS data.
On non-Windows these checks are explicitly skipped, not counted as proof.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

from flowpilot_universal.engine import InputError, load_manifest, scan
from flowpilot_universal.manifest_editor import create_approved_manifest
from flowpilot_universal.session import run_session


@unittest.skipUnless(os.name == "nt", "NTFS reparse/junction test requires hosted Windows")
class WindowsRealJunctionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / "source"
        self.external = self.base / "outside"
        self.report = self.base / "reports"
        for path in (self.source, self.external, self.report):
            path.mkdir()
        (self.source / "required.txt").write_bytes(b"approved bytes")
        (self.external / "private.txt").write_bytes(b"not in authorized root")
        self.manifest_file = self.base / "manifest.json"
        self.manifest_file.write_text(json.dumps({
            "schema_version": 1, "expected_files": [{"path": "required.txt"}]
        }), encoding="utf-8")

    def create_junction(self, name: str, target: Path) -> Path:
        link = self.base / name
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True, timeout=8)
        if proc.returncode != 0:
            self.skipTest("CI host refused test-only NTFS mklink junction: " + proc.stderr[:160])
        flags = getattr(link.lstat(), "st_file_attributes", 0)
        self.assertTrue(flags & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        self.addCleanup(lambda: link.exists() and link.rmdir())
        return link

    def test_nested_junction_is_never_traversed(self):
        link = self.source / "outside_link"
        proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.external)],
                              capture_output=True, text=True, timeout=8)
        if proc.returncode != 0:
            self.skipTest("test-only nested junction unavailable: " + proc.stderr[:160])
        self.addCleanup(lambda: link.exists() and link.rmdir())
        result = scan(self.source, load_manifest(self.manifest_file))
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("UNSAFE_LINK", {x["code"] for x in result["issues"]})
        self.assertNotIn("outside_link/private.txt", {x["path"] for x in result["files"]})
        self.assertEqual((self.external / "private.txt").read_bytes(), b"not in authorized root")

    def test_root_junction_rejected_for_scan_and_manifest_builder(self):
        link = self.create_junction("source_link", self.source)
        with self.assertRaises(InputError):
            scan(link, load_manifest(self.manifest_file))
        with self.assertRaises(InputError):
            run_session(link, self.manifest_file, self.report, consent=True)
        destination = self.report / "draft.json"
        with self.assertRaises(InputError):
            create_approved_manifest("Authorized", "required.txt", destination,
                                     link, approved=True)
        self.assertFalse(destination.exists())

    def test_output_junction_rejected_before_history_creation(self):
        link = self.create_junction("report_link", self.report)
        with self.assertRaises(InputError):
            run_session(self.source, self.manifest_file, link, consent=True)
        self.assertEqual(list(self.report.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
