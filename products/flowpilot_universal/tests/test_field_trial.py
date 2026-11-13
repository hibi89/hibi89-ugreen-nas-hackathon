"""Synthetic-only F09 readiness. No real USB/SMB or customer data is accessed."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from flowpilot_universal.engine import InputError
from flowpilot_universal.field_trial import run_field_trial, main
from flowpilot_universal.session import run_session


class FieldTrialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root, self.out = self.base / "src", self.base / "out"
        self.root.mkdir()
        self.out.mkdir()
        self.file = self.root / "sample.txt"
        self.file.write_bytes(b"sample")
        self.manifest = self.base / "contract.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "expected_files": [{"path": "sample.txt"}]
        }), encoding="utf-8")

    def test_three_verified_full_scans_no_source_write(self):
        before = self.file.read_bytes()
        result = run_field_trial(self.root, self.manifest, self.out,
                                 consent=True, medium="usb")
        self.assertEqual(result["verdict"], "REPEATABILITY_PASS_NOT_FIELD_ACCEPTANCE")
        self.assertEqual(len(result["rounds"]), 3)
        self.assertTrue(all(r["status"] == "READY" and r["reports_verified"] == 2
                            for r in result["rounds"]))
        self.assertEqual(len({r["file_list_sha256"] for r in result["rounds"]}), 1)
        self.assertFalse(result["customer_hardware_verified"])
        self.assertEqual(self.file.read_bytes(), before)
        self.assertTrue(Path(result["summary_path"]).is_file())
        self.assertEqual(main(["--root", str(self.root), "--manifest", str(self.manifest),
                               "--output", str(self.out), "--medium", "pc", "--consent"]), 0)

    def test_desktop_entry_field_trial_route_synthetic(self):
        from desktop_entry import main as desktop_main
        args = ["--field-trial", "--root", str(self.root),
                "--manifest", str(self.manifest), "--output", str(self.out),
                "--medium", "pc"]
        self.assertEqual(desktop_main(args), 2)
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertEqual(desktop_main(args + ["--consent"]), 0)
        summaries = list(self.out.glob("flowpilot-field-trial-*.json"))
        self.assertEqual(len(summaries), 1)
        trial = json.loads(summaries[0].read_text(encoding="utf-8"))
        self.assertEqual(trial["verdict"], "REPEATABILITY_PASS_NOT_FIELD_ACCEPTANCE")
        self.assertEqual(len(trial["rounds"]), 3)
        self.assertFalse(trial["customer_hardware_verified"])

    def test_desktop_entry_handles_windowed_no_console(self):
        from desktop_entry import main as desktop_main
        args = ["--field-trial", "--root", str(self.root),
                "--manifest", str(self.manifest), "--output", str(self.out),
                "--medium", "pc"]
        with patch("flowpilot_universal.field_trial.sys.stdout", None), \
             patch("flowpilot_universal.field_trial.sys.stderr", None):
            self.assertEqual(desktop_main(args), 2)
            self.assertEqual(desktop_main(args + ["--consent"]), 0)
        self.assertEqual(len(list(self.out.glob("flowpilot-field-trial-*.json"))), 1)

    def test_no_consent_no_outputs(self):
        with self.assertRaises(InputError):
            run_field_trial(self.root, self.manifest, self.out, medium="smb")
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertEqual(main(["--root", str(self.root), "--manifest", str(self.manifest),
                               "--output", str(self.out), "--medium", "smb"]), 2)

    def test_source_change_between_rounds_refuses_pass(self):
        real = run_session
        calls = [0]
        def changed(*args, **kwargs):
            session = real(*args, **kwargs)
            calls[0] += 1
            if calls[0] == 1:
                self.file.write_bytes(b"changed")
            return session
        with patch("flowpilot_universal.field_trial.run_session", side_effect=changed):
            result = run_field_trial(self.root, self.manifest, self.out,
                                     consent=True, medium="pc")
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertEqual(len(result["rounds"]), 2)
        self.assertIn("differs", result["reason"])

    def test_missing_requirement_never_passes(self):
        self.file.unlink()
        result = run_field_trial(self.root, self.manifest, self.out,
                                 consent=True, medium="pc")
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertEqual(result["rounds"][0]["status"], "BLOCKED")
        self.assertEqual(len(result["rounds"]), 1)

    def test_manifest_change_between_rounds_refuses_pass(self):
        real = run_session
        def changed(*args, **kwargs):
            session = real(*args, **kwargs)
            self.manifest.write_text(json.dumps({
                "schema_version": 1, "expected_files": [{"path": "sample.txt"}],
                "title": "contract modified"
            }), encoding="utf-8")
            return session
        with patch("flowpilot_universal.field_trial.run_session", side_effect=changed):
            result = run_field_trial(self.root, self.manifest, self.out,
                                     consent=True, medium="pc")
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertIn("manifest changed", result["reason"])

    def test_verification_failure_never_passes(self):
        with patch("flowpilot_universal.field_trial.verify_history_entry", side_effect=InputError("bad")):
            result = run_field_trial(self.root, self.manifest, self.out,
                                     consent=True, medium="pc")
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertEqual(len(result["rounds"]), 0)
        self.assertTrue(Path(result["summary_path"]).is_file())

    def test_output_inside_source_and_unsupported_medium_refused(self):
        with self.assertRaises(InputError):
            run_field_trial(self.root, self.manifest, self.root,
                            consent=True, medium="pc")
        with self.assertRaises(InputError):
            run_field_trial(self.root, self.manifest, self.out,
                            consent=True, medium="unknown")


if __name__ == "__main__":
    unittest.main()
