"""Offline source-only pilot ZIP and fresh-extraction runtime verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.build_flowpilot_pilot_zip import build_offline_pilot, PilotBundleRefused, PREFIX


class OfflinePilotZIPTests(unittest.TestCase):
    def test_zip_contains_exact_source_only_and_runs_from_extracted_location(self):
        with tempfile.TemporaryDirectory(prefix="flowpilot-zip-test-") as temp:
            output = Path(temp) / "pilot.zip"
            report = build_offline_pilot(output)
            self.assertEqual(report["status"], "OFFLINE_LOCAL_PILOT_ZIP_BUILT")
            self.assertFalse(report["actual_nas_verified"])
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn(f"{PREFIX}/tools/START_FLOWPILOT_DEMO.cmd", names)
                self.assertIn(f"{PREFIX}/tools/flowpilot_owner_csv.py", names)
                self.assertFalse(any(
                    "/tests/" in name or "/.git/" in name or "/evidence/" in name
                    or name.endswith(".env") for name in names
                ))
                manifest = json.loads(archive.read(f"{PREFIX}/MANIFEST.json"))
                for name, digest in manifest["files"].items():
                    self.assertEqual(
                        hashlib.sha256(archive.read(f"{PREFIX}/{name}")).hexdigest(),
                        digest,
                    )
                archive.extractall(Path(temp) / "extracted")
            start = (Path(temp) / "extracted" / PREFIX / "tools")
            with tempfile.TemporaryDirectory(prefix="flowpilot-different-cwd-") as cwd:
                check = subprocess.run(
                    [sys.executable, str(start / "flowpilot_local_acceptance.py")],
                    cwd=cwd, capture_output=True, text=True, timeout=90,
                )
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertEqual(json.loads(check.stdout)["passed"], 4)

    def test_final_delivery_blocked_when_extracted_bundle_has_missing_module(self):
        from unittest.mock import patch
        from tools import build_flowpilot_pilot_zip as bundler
        original = bundler._collect
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "no-broken-pilot.zip"
            def remove_required_module(root):
                files = original(root)
                self.assertIn("tools/flowpilot_owner_csv.py", files)
                files.pop("tools/flowpilot_owner_csv.py")
                return files
            with patch.object(bundler, "_collect", side_effect=remove_required_module):
                with self.assertRaises(PilotBundleRefused):
                    bundler.build_offline_pilot(path)
            self.assertFalse(path.exists())

    def test_release_receipt_requires_extracted_four_check_and_ui_demo(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "verified.zip"
            row = build_offline_pilot(target)
            self.assertTrue(row["extracted_four_capability_acceptance_passed"])
            self.assertTrue(row["extracted_ui_demo_check_passed"])
            self.assertFalse(row["actual_nas_verified"])

    def test_existing_bundle_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "existing.zip"
            out.write_bytes(b"never overwrite")
            with self.assertRaisesRegex(PilotBundleRefused, "ZIP_DESTINATION_OCCUPIED"):
                build_offline_pilot(out)
            self.assertEqual(out.read_bytes(), b"never overwrite")

    def test_racing_destination_creator_cannot_be_deleted_by_zip_failure(self):
        from tools.build_flowpilot_pilot_zip import _write_zip
        from unittest.mock import patch
        real_open = Path.open
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "racing.zip"
            def racing_open(instance, mode="r", *args, **kwargs):
                if instance == target and mode == "xb":
                    with real_open(target, "wb") as foreign:
                        foreign.write(b"another-process-owned-file")
                    raise FileExistsError("race")
                return real_open(instance, mode, *args, **kwargs)
            with patch.object(Path, "open", racing_open):
                with self.assertRaisesRegex(PilotBundleRefused, "ZIP_BUILD_FAILED"):
                    _write_zip(target, {"tools/sample.py": b"pass\\n"})
            self.assertEqual(target.read_bytes(), b"another-process-owned-file")

    def test_manifest_does_not_claim_vendor_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "pilot.zip"
            build_offline_pilot(target)
            with zipfile.ZipFile(target) as archive:
                meta = json.loads(archive.read(f"{PREFIX}/MANIFEST.json"))
            self.assertFalse(meta["actual_nas_verified"])
            self.assertFalse(meta["registered_uliya_expert_invoked"])
            self.assertEqual(meta["release_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
