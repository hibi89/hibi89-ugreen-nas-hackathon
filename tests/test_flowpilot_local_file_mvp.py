"""G60 filesystem-backed synthetic smoke and path boundaries, never NAS."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_local_file_mvp import inspect_exact_local_fixture, run_local_fixture


class G60ActualLocalFileMVP(unittest.TestCase):
    def test_real_local_file_is_present_in_ephemeral_fixture(self):
        r = run_local_fixture("complete_synthetic_handoff")
        self.assertEqual([x["state"] for x in r["items"]], ["PRESENT", "PRESENT"])
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual(r["filesystem_probe"], "OS_LSTAT_ONLY_ON_GENERATED_TEST_FILES")
        self.assertFalse(r["real_nas_verified"])

    def test_absent_real_local_file_classifies_missing(self):
        r = run_local_fixture("missing_required_synthetic")
        self.assertIn("MISSING", [x["state"] for x in r["items"]])
        self.assertEqual(r["status"], "BLOCKED")

    def test_two_actual_local_files_are_version_conflict(self):
        r = run_local_fixture("conflicting_versions_synthetic")
        self.assertEqual(r["items"][0]["state"], "VERSION_REVIEW")
        self.assertNotEqual(r["status"], "READY")

    def test_incomplete_simulation_does_not_claim_actual_denial(self):
        r = run_local_fixture("truncated_or_denied_synthetic")
        self.assertEqual(r["items"][0]["state"], "NOT_CHECKED")
        self.assertTrue(r["simulated_incomplete_or_denied"])
        self.assertFalse(r["registered_uliya_expert_invoked"])

    def test_actual_synthetic_symlink_is_not_followed(self):
        try:
            r = run_local_fixture("symlink_unknown_synthetic")
        except RuntimeError as exc:
            if "SYNTHETIC_SYMLINK_FIXTURE_UNAVAILABLE" in str(exc):
                self.skipTest("Host cannot create symlink fixtures")
            raise
        self.assertEqual(r["items"][0]["state"], "NOT_CHECKED")
        self.assertEqual(r["scratch_scope"], "AUTOMATICALLY_REMOVED")

    def test_invalid_request_does_not_contact_any_service(self):
        r = run_local_fixture("complete_synthetic_handoff", "파일 옮겨줘")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["planned_expert_steps_not_executed"], [])
        self.assertFalse(r["official_creator_invoked"])

    def test_korean_normal_request_plans_readonly(self):
        r = run_local_fixture("complete_synthetic_handoff", "납품 파일 확인해줘")
        self.assertEqual(r["goal_type"], "HANDOFF_AUDIT")
        self.assertEqual(r["items"][0]["state"], "PRESENT")

    def test_out_of_scope_path_rejected_before_any_file_access(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for relative in ("../outside.md", "/absolute/path", "a/../../escape", "secrets.txt"):
                with self.subTest(path=relative):
                    with self.assertRaises(ValueError):
                        inspect_exact_local_fixture(root, ("README.md", relative))

    def test_nested_symlink_does_not_follow_outside_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            allowed = root / "allowed"
            allowed.mkdir()
            external = root / "outside"
            external.mkdir()
            (external / "report.md").write_text("private synthetic")
            try:
                (allowed / "files").symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Host cannot create directory symlinks")
            observations, complete = inspect_exact_local_fixture(
                allowed, ("files/report.md",))
            self.assertTrue(complete)
            self.assertEqual(len(observations), 1)
            self.assertTrue(observations[0].is_symlink)
            self.assertEqual(observations[0].reference, "")

    def test_read_only_probe_preserves_file_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            contents = b"not a NAS file"
            (root / "report.md").write_bytes(contents)
            obs, complete = inspect_exact_local_fixture(root, ("report.md",))
            self.assertTrue(complete)
            self.assertEqual(len(obs), 1)
            self.assertEqual((root / "report.md").read_bytes(), contents)

    def test_root_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / "folder"
            folder.mkdir()
            link = root / "alias"
            try:
                link.symlink_to(folder, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("No directory symlinks")
            with self.assertRaises(ValueError):
                inspect_exact_local_fixture(link, ("report.md",))

    def test_no_user_supplied_folder_or_network_cli_argument(self):
        cmd = [sys.executable, str(ROOT / "tools" / "flowpilot_local_file_mvp.py"),
               "--scenario", "missing_required_synthetic"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        obj = json.loads(result.stdout)
        self.assertEqual(obj["mode"], "EPHEMERAL_LOCAL_FILESYSTEM_SYNTHETIC_MVP")
        self.assertEqual(obj["items"][-1]["state"], "MISSING")
        self.assertNotIn("customer", obj)
        self.assertEqual(obj["release_gate"], "HOLD")

    def test_invalid_fixture_name_rejected(self):
        with self.assertRaises(ValueError):
            run_local_fixture("not-a-scenario")

if __name__ == "__main__":
    unittest.main()
