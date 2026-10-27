"""G62 owner-chosen actual local filesystem pilot, no NAS or Uliya calls."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_owner_local_audit import inspect_owner_folder, OwnerAuditError


class G62OwnerLocalAudit(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name)
        (self.root / "README.md").write_bytes(b"owner-synthetic local contents")
        (self.root / "release").mkdir()
        (self.root / "release" / "final.pdf").write_bytes(b"v1")

    def audit(self, items=("README.md",), *, approval=True, goal="check required files", versions=None):
        return inspect_owner_folder(
            self.root, items, version_candidates=versions,
            goal=goal, metadata_consent=approval)

    def test_real_user_selected_local_file_checks_present_without_content(self):
        before = (self.root / "README.md").read_bytes()
        row = self.audit()
        self.assertEqual(row["items"], [{"index": 1, "state": "PRESENT", "local_reference_count": 1}])
        self.assertEqual(row["status"], "NEEDS_REVIEW")
        self.assertTrue(row["inspected_local_metadata"])
        self.assertFalse(row["file_contents_opened"])
        self.assertFalse(row["registered_uliya_agent_invoked"])
        self.assertEqual(before, (self.root / "README.md").read_bytes())

    def test_missing_is_reported_as_blocked(self):
        row = self.audit(("README.md", "missing.docx"))
        self.assertEqual([x["state"] for x in row["items"]], ["PRESENT", "MISSING"])
        self.assertEqual(row["status"], "BLOCKED")
        self.assertFalse(row["nas_verified"])

    def test_version_conflict_when_both_files_exist(self):
        (self.root / "release" / "final_v2.pdf").write_bytes(b"v2")
        row = self.audit(("release/final.pdf",),
                         versions={"release/final.pdf": ("release/final_v2.pdf",)},
                         goal="compare versions")
        self.assertEqual(row["items"][0]["state"], "VERSION_REVIEW")
        self.assertEqual(row["release_gate"], "HOLD")

    def test_unselected_version_candidate_not_scanned(self):
        with patch("flowpilot_owner_local_audit._inspect_one") as probe:
            probe.return_value = (None, True)
            self.audit()
            self.assertEqual(probe.call_count, 1)
            self.assertEqual(probe.call_args.args[1], "README.md")

    def test_without_explicit_consent_no_filesystem_access(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT ACCESSED")):
            row = self.audit(approval=False)
            self.assertEqual(row["status"], "WAITING_APPROVAL")
            self.assertFalse(row["inspected_local_metadata"])

    def test_mutating_goal_stops_before_filesystem_access(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT ACCESSED")):
            row = self.audit(goal="delete these files")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertFalse(row["inspected_local_metadata"])

    def test_missing_root_fails_without_leaking_name(self):
        with self.assertRaises(OwnerAuditError):
            inspect_owner_folder(self.root / "no-folder", ["README.md"], metadata_consent=True)

    def test_traversal_and_secrets_rejected_before_root_touch(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT ACCESSED")):
            for path in ("../escape", "/etc/passwd", ".env", "secret.key", "folder//x"):
                with self.subTest(path=path), self.assertRaises(OwnerAuditError):
                    self.audit((path,))

    def test_symlink_file_is_not_read(self):
        dest = self.root / "outside.txt"
        dest.write_bytes(b"synthetic restricted data")
        link = self.root / "linked.txt"
        try:
            link.symlink_to(dest)
        except (OSError, NotImplementedError):
            self.skipTest("File symlinks unavailable")
        row = self.audit(("linked.txt",))
        self.assertEqual(row["items"][0]["state"], "NOT_CHECKED")
        self.assertNotIn("outside", json.dumps(row))

    def test_symlink_directory_is_not_followed(self):
        (self.root / "other").mkdir()
        (self.root / "other" / "data.csv").write_bytes(b"outside")
        link = self.root / "alias"
        try:
            link.symlink_to(self.root / "other", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlinks unavailable")
        row = self.audit(("alias/data.csv",))
        self.assertEqual(row["items"][0]["state"], "NOT_CHECKED")

    def test_root_symlink_rejected(self):
        link = self.root.parent / (self.root.name + "-linked")
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Root symlinks unavailable")
        self.addCleanup(lambda: link.unlink(missing_ok=True))
        with self.assertRaises(OwnerAuditError):
            inspect_owner_folder(link, ["README.md"], metadata_consent=True)

    def test_cannot_provide_unbounded_or_unauthorized_candidates(self):
        with self.assertRaises(OwnerAuditError):
            self.audit(versions={"not-required.md": ("README.md",)})
        with self.assertRaises(OwnerAuditError):
            self.audit(versions={"README.md": ("README.md",)})
        with self.assertRaises(OwnerAuditError):
            self.audit(items=("README.md", "README.md"))
        with self.assertRaises(OwnerAuditError):
            self.audit(items=tuple(f"file{i}.txt" for i in range(101)))

    def test_nonboolean_consent_does_not_unlock_scan(self):
        with self.assertRaises(OwnerAuditError):
            inspect_owner_folder(self.root, ["README.md"], metadata_consent="true")

    def test_real_local_cli_runs_when_owner_opted_in(self):
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_owner_local_audit.py"),
               "--root", str(self.root), "--required", "README.md",
               "--required", "release/final.pdf", "--approve-local-metadata"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        record = json.loads(res.stdout)
        self.assertEqual([x["state"] for x in record["items"]], ["PRESENT", "PRESENT"])
        self.assertNotIn(str(self.root), res.stdout)
        self.assertNotIn("README.md", res.stdout)
        self.assertTrue(record["inspected_local_metadata"])
        self.assertFalse(record["nas_verified"])

    def test_cli_without_consent_refuses_to_read_any_content(self):
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_owner_local_audit.py"),
               "--root", str(self.root), "--required", "README.md"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        record = json.loads(res.stdout)
        self.assertEqual(record["status"], "WAITING_APPROVAL")
        self.assertFalse(record["inspected_local_metadata"])

    def test_cli_rejects_unsafe_request_without_echoing_input(self):
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_owner_local_audit.py"),
               "--root", str(self.root), "--required", "../DO_NOT_ECHO", "--approve-local-metadata"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("DO_NOT_ECHO", r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "LOCAL_AUDIT_REFUSED")

    def test_local_directory_metadata_error_is_fail_closed(self):
        with patch("flowpilot_owner_local_audit._inspect_one", return_value=(None, False)):
            r = self.audit(("README.md",))
            self.assertEqual(r["items"][0]["state"], "NOT_CHECKED")
            self.assertIn("ONE_OR_MORE_LOCAL_METADATA_CHECKS_FAILED", r["limitations"])


if __name__ == "__main__":
    unittest.main()
