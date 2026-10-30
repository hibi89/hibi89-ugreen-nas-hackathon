"""Source doctor regressions, using mock Git checks rather than private source."""
from __future__ import annotations

import unittest
import json
from contextlib import redirect_stdout
from io import StringIO
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from tools.flowpilot_source_doctor import SOURCES, inspect_sources, main
from tools.verify_private_hae_chain import ProofRefused


class SourceDoctorTests(unittest.TestCase):
    def setUp(self):
        self.roots = (Path("/hae"), Path("/sovia"), Path("/dbvora"))

    def test_three_clean_checkouts_are_preview_ready_but_not_executed(self):
        calls = []
        def fake_verify(root, sha, paths):
            calls.append((root, sha, paths))
            return Path("/trusted")
        with (patch("tools.flowpilot_source_doctor.verify_checkout",
                    side_effect=fake_verify),
              patch("tools.flowpilot_source_doctor.Path.is_file", return_value=True),
              patch("tools.flowpilot_source_doctor.Path.is_symlink", return_value=False),
              patch("tools.flowpilot_source_doctor.shutil.which", return_value="/bin/git")):
            row = inspect_sources(*self.roots)
        self.assertEqual(row["status"], "READY_FOR_LOCAL_SYNTHETIC_PREVIEW")
        self.assertEqual(len(calls), 3)
        self.assertFalse(row["private_source_executed"])
        self.assertFalse(row["actual_nas_verified"])
        self.assertEqual(row["release_gate"], "HOLD")

    def test_bad_dbvora_revision_refused_without_source_paths(self):
        def fake(root, sha, paths):
            if sha == SOURCES[2][1]:
                raise ProofRefused("SOURCE_SHA_MISMATCH")
            return Path("/trusted")
        with (patch("tools.flowpilot_source_doctor.verify_checkout", side_effect=fake),
              patch("tools.flowpilot_source_doctor.Path.is_file", return_value=True),
              patch("tools.flowpilot_source_doctor.Path.is_symlink", return_value=False),
              patch("tools.flowpilot_source_doctor.shutil.which", return_value="/bin/git")):
            row = inspect_sources(*self.roots)
        self.assertEqual(row["sources"]["dbvora"]["status"], "SOURCE_SHA_MISMATCH")
        self.assertEqual(row["status"], "READY_FOR_LOCAL_SYNTHETIC_PREVIEW")
        self.assertTrue(row["owner_local_synthetic_preview_readiness"])
        self.assertFalse(row["owner_local_synthetic_execution_readiness"])
        self.assertFalse(row["owner_local_synthetic_source_readiness"])
        self.assertNotIn("/dbvora", str(row))

    def test_path_concrete_subclasses_are_accepted_by_type_gate(self):
        """Path(...) returns PosixPath/WindowsPath, never type Path itself."""
        self.assertIsNot(type(self.roots[0]), Path)
        with (patch("tools.flowpilot_source_doctor.verify_checkout",
                    return_value=Path("/trusted")) as checked,
              patch("tools.flowpilot_source_doctor.Path.is_file", return_value=True),
              patch("tools.flowpilot_source_doctor.Path.is_symlink", return_value=False),
              patch("tools.flowpilot_source_doctor.shutil.which", return_value="/bin/git")):
            row = inspect_sources(*self.roots)
        self.assertEqual(checked.call_count, 3)
        self.assertTrue(row["owner_local_synthetic_source_readiness"])

    def test_absent_dbvora_allows_preview_but_not_execution(self):
        def fake(root, sha, paths):
            if sha == SOURCES[2][1]:
                raise ProofRefused("SOURCE_ROOT_MISSING")
            return Path("/trusted")
        with (patch("tools.flowpilot_source_doctor.verify_checkout", side_effect=fake),
              patch("tools.flowpilot_source_doctor.Path.is_file", return_value=True),
              patch("tools.flowpilot_source_doctor.Path.is_symlink", return_value=False),
              patch("tools.flowpilot_source_doctor.shutil.which", return_value="/bin/git")):
            result = inspect_sources(*self.roots)
        self.assertTrue(result["owner_local_synthetic_preview_readiness"])
        self.assertFalse(result["owner_local_synthetic_execution_readiness"])
        self.assertEqual(result["status"], "READY_FOR_LOCAL_SYNTHETIC_PREVIEW")

    def test_cli_success_exit_means_preview_ready_not_private_execution(self):
        evidence = {
            "status": "READY_FOR_LOCAL_SYNTHETIC_PREVIEW",
            "owner_local_synthetic_preview_readiness": True,
            "owner_local_synthetic_execution_readiness": False,
            "actual_nas_verified": False,
            "release_gate": "HOLD",
        }
        output = StringIO()
        with (patch("tools.flowpilot_source_doctor.inspect_sources",
                    return_value=evidence),
              redirect_stdout(output)):
            rc = main(["--hae-root", "/hae", "--sovia-root", "/sovia",
                       "--dbvora-root", "/dbvora"])
        self.assertEqual(rc, 0)
        row = json.loads(output.getvalue())
        self.assertFalse(row["owner_local_synthetic_execution_readiness"])

    def test_missing_git_skips_all_checkout_invocations(self):
        with (patch("tools.flowpilot_source_doctor.shutil.which", return_value=None),
              patch("tools.flowpilot_source_doctor.verify_checkout",
                    side_effect=AssertionError("GIT CALLED")) as checked):
            row = inspect_sources(*self.roots)
        checked.assert_not_called()
        self.assertEqual(row["status"], "BLOCKED")

    def test_untrusted_exception_text_never_reaches_status(self):
        with (patch("tools.flowpilot_source_doctor.verify_checkout",
                    side_effect=ProofRefused("PRIVATE_CUSTOMER_C_PATH")),
              patch("tools.flowpilot_source_doctor.shutil.which", return_value="/bin/git")):
            row = inspect_sources(*self.roots)
        self.assertEqual(row["sources"]["hae_la"]["status"], "LOCAL_SOURCE_UNVERIFIED")
        self.assertNotIn("PRIVATE_CUSTOMER", str(row))

    def test_direct_launcher_from_unrelated_working_directory(self):
        """Regression: script entrypoint must find tools even outside repo."""
        script = Path(__file__).resolve().parents[1] / "tools" / "flowpilot_source_doctor.py"
        with tempfile.TemporaryDirectory(prefix="ugreen-doctor-cwd-") as tmp:
            proc = subprocess.run(
                [sys.executable, str(script),
                 "--hae-root", str(Path(tmp) / "no-hae"),
                 "--sovia-root", str(Path(tmp) / "no-sovia"),
                 "--dbvora-root", str(Path(tmp) / "no-dbvora")],
                cwd=tmp, capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        row = json.loads(proc.stdout)
        self.assertEqual(row["status"], "BLOCKED")
        self.assertFalse(row["actual_nas_verified"])
        self.assertEqual(row["release_gate"], "HOLD")

    def test_missing_checkout_never_claims_real_execution(self):
        with patch("tools.flowpilot_source_doctor.verify_checkout",
                   side_effect=ProofRefused("SOURCE_ROOT_MISSING")):
            row = inspect_sources(*self.roots)
        self.assertEqual(row["status"], "BLOCKED")
        self.assertFalse(row["private_source_executed"])
        self.assertFalse(row["registered_uliya_expert_invoked"])


if __name__ == "__main__":
    unittest.main()
