"""G94: actual disposable LOCAL metadata reads with redacted review outputs."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_local_review import build_local_review, OwnerAuditError, SCHEMA


class G94LocalReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text("PRIVATE_SENTINEL", encoding="utf-8")
        (self.root / "release").mkdir()
        (self.root / "release" / "output_v2.pdf").write_bytes(b"PRIVATE_PDF")
        self.root_path = str(self.root)

    def test_no_consent_does_not_touch_even_missing_root(self):
        report = build_local_review(
            self.root / "missing-root", ["README.md"],
            metadata_consent=False,
        )
        self.assertEqual(report["source_status"], "WAITING_APPROVAL")
        self.assertFalse(report["metadata_inspection_executed"])
        self.assertEqual(report["review_queue"], [])
        self.assertEqual(report["decision"], "HOLD")

    def test_actual_local_lstat_present_and_missing_are_indexed(self):
        report = build_local_review(
            self.root, ["README.md", "missing.txt"], metadata_consent=True,
        )
        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["metadata_inspection_executed"])
        self.assertEqual([r["observed_state"] for r in report["review_queue"]],
                         ["PRESENT", "MISSING"])
        self.assertEqual(report["source_status"], "BLOCKED")
        self.assertEqual(report["finding_counts"]["MISSING"], 1)
        self.assertEqual(report["decision"], "HOLD")

    def test_actual_local_version_candidate_stays_review_not_verified(self):
        report = build_local_review(
            self.root, ["release/output.pdf"],
            version_candidates={"release/output.pdf": ["release/output_v2.pdf"]},
            goal="compare versions", metadata_consent=True,
        )
        self.assertEqual(report["review_queue"][0]["observed_state"],
                         "VERSION_REVIEW")
        self.assertEqual(report["source_status"], "NEEDS_REVIEW")
        self.assertFalse(report["registered_expert_invocation_verified"])
        self.assertFalse(report["real_nas_verified"])

    def test_no_raw_paths_contents_or_reference_leak(self):
        report = build_local_review(
            self.root, ["README.md", "release/output.pdf"],
            metadata_consent=True,
        )
        output = json.dumps(report, ensure_ascii=False)
        for secret in (self.root_path, "README.md", "release/output.pdf",
                       "PRIVATE_SENTINEL", "PRIVATE_PDF",
                       "local-metadata://"):
            self.assertNotIn(secret, output)
        self.assertFalse(report["file_contents_opened"])
        self.assertFalse(report["raw_paths_references_or_contents_returned"])

    def test_delete_intent_does_not_read_local_metadata(self):
        report = build_local_review(
            self.root / "non-existent", ["README.md"],
            goal="delete project files", metadata_consent=True,
        )
        self.assertEqual(report["source_status"], "BLOCKED")
        self.assertFalse(report["metadata_inspection_executed"])
        self.assertEqual(report["review_queue"], [])

    def test_non_boolean_consent_rejected(self):
        for value in (1, "yes", None, [], {}):
            with self.subTest(value=value), self.assertRaises(OwnerAuditError):
                build_local_review(self.root, ["README.md"],
                                   metadata_consent=value)

    def test_path_traversal_fails_before_root_access(self):
        with self.assertRaises(OwnerAuditError):
            build_local_review(
                self.root / "missing", ["../private.txt"],
                metadata_consent=True,
            )

    def test_invalid_version_candidate_fails_before_root_access(self):
        with self.assertRaises(OwnerAuditError):
            build_local_review(
                self.root / "missing", ["README.md"],
                version_candidates={"README.md": ["../private.txt"]},
                goal="compare versions", metadata_consent=True,
            )

    def test_bad_local_root_fails_closed_without_its_name(self):
        cmd = [
            sys.executable, str(ROOT / "tools/flowpilot_local_review.py"),
            "--root", str(self.root / "missing-root"),
            "--required", "README.md", "--approve-local-metadata",
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        self.assertEqual(output.returncode, 2, output.stderr)
        self.assertEqual(json.loads(output.stdout)["status"],
                         "G94_LOCAL_REVIEW_REFUSED")
        self.assertNotIn(self.root_path, output.stdout + output.stderr)

    def test_cli_real_metadata_success_and_explicit_consent(self):
        cmd = [
            sys.executable, str(ROOT / "tools/flowpilot_local_review.py"),
            "--root", str(self.root), "--required", "README.md",
        ]
        without = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        self.assertEqual(without.returncode, 0, without.stderr)
        self.assertFalse(json.loads(without.stdout)["metadata_inspection_executed"])
        with_consent = subprocess.run(
            cmd + ["--approve-local-metadata"],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(with_consent.returncode, 0, with_consent.stderr)
        payload = json.loads(with_consent.stdout)
        self.assertTrue(payload["metadata_inspection_executed"])
        self.assertEqual(payload["review_queue"][0]["observed_state"], "PRESENT")
        self.assertNotIn(str(self.root), with_consent.stdout)
        self.assertNotIn("README.md", with_consent.stdout)

    def test_cli_missing_file_reports_blocked_exit(self):
        cmd = [
            sys.executable, str(ROOT / "tools/flowpilot_local_review.py"),
            "--root", str(self.root), "--required", "missing.txt",
            "--approve-local-metadata",
        ]
        got = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        self.assertEqual(got.returncode, 1, got.stderr)
        self.assertEqual(json.loads(got.stdout)["decision"], "HOLD")
        self.assertNotIn("missing.txt", got.stdout)

    def test_local_symlink_is_not_a_verified_file(self):
        target = self.root / "README.md"
        link = self.root / "release" / "link.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Host cannot create symlinks")
        report = build_local_review(
            self.root, ["release/link.txt"], metadata_consent=True,
        )
        self.assertNotEqual(report["review_queue"][0]["observed_state"],
                            "PRESENT")
        self.assertEqual(report["decision"], "HOLD")

    def test_approved_local_reader_is_not_promoted_to_registered_expert(self):
        report = build_local_review(
            self.root, ["README.md"], metadata_consent=True,
        )
        for flag in ("registered_expert_invocation_verified", "real_nas_verified",
                     "official_creator_verified", "devpost_submitted"):
            self.assertFalse(report[flag], flag)
        self.assertEqual(report["release_gate"], "HOLD")
        self.assertIn("NOT_NAS", report["mode"])


if __name__ == "__main__":
    unittest.main()
