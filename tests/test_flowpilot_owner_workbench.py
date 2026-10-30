"""Real owner-local disposable metadata read with explicit preview and consent."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.flowpilot_owner_workbench import (
    CONSENT, OwnerWorkbench, OwnerWorkbenchRefused,
)


class OwnerWorkbenchTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="ugreen-owner-consented-test-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "README.md").write_text("test-only bytes, never read by workbench")
        self.controller = OwnerWorkbench()

    def request(self, *, goal="파일 누락 확인", required=None, candidates=None):
        return {"goal": goal, "root": str(self.root),
                "required": ["README.md"] if required is None else required,
                "candidates": candidates, "confirm_local_only": True}

    def test_preview_zero_root_metadata_then_real_consent_runs(self):
        req = self.request()
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("PREVIEW TOUCHED ROOT")):
            preview = self.controller.preview(req)
        self.assertFalse(preview["metadata_accessed"])
        self.assertEqual(preview["planned_actions"],
                         [{"step_index": 1, "action": "check required files"}])
        result = self.controller.execute(preview["approval_token"], CONSENT)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["finding_counts"]["PRESENT"], 1)
        self.assertEqual(result["executed_steps"], 1)
        self.assertEqual(result["stage_results"][0]["items"],
                         [{"item_index": 1, "state": "PRESENT"}])
        self.assertEqual(result["stage_results"][0]["step_index"], 1)
        self.assertFalse(result["actual_nas_verified"])
        raw = json.dumps(result)
        self.assertNotIn(str(self.root), raw)
        self.assertNotIn("README.md", raw)

    def test_preview_is_not_a_metadata_read_even_if_root_does_not_exist(self):
        request = self.request()
        request["root"] = str(self.root / "nonexistent-child")
        ticket = self.controller.preview(request)
        self.assertFalse(ticket["metadata_accessed"])
        # Missing roots fail closed as BLOCKED, not as a successful inspection.
        result = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["finding_counts"]["PRESENT"], 0)
        self.assertFalse(result["actual_nas_verified"])

    def test_multi_stage_output_redacts_all_owner_paths_and_names(self):
        (self.root / "README_final.md").write_text("test-only fixture")
        req = self.request(
            goal="파일 누락 확인 그리고 인계 확인 그리고 버전 비교",
            candidates={"README.md": ["README_final.md"]},
        )
        ticket = self.controller.preview(req)
        self.assertEqual(len(ticket["planned_actions"]), 3)
        row = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(len(row["stage_results"]), 3)
        self.assertEqual(row["stage_results"][2]["items"][0]["state"], "VERSION_REVIEW")
        serialized = json.dumps(row, ensure_ascii=False)
        for secret in (str(self.root), "README.md", "README_final.md", "test-only"):
            self.assertNotIn(secret, serialized)

    def test_mutated_observed_item_with_raw_filename_is_never_forwarded(self):
        from tools.flowpilot_owner_workbench import _safe_stage_results
        rows = [{"index": 1, "status": "NEEDS_REVIEW",
                 "inspected_local_metadata": True,
                 "items": [{"index": 1, "state": "PRESENT",
                            "local_reference_count": 1,
                            "secret_filename": "sensitive-secret.txt"}]}]
        safe = _safe_stage_results(rows, 1)
        self.assertNotIn("sensitive-secret.txt", json.dumps(safe))
        rows[0]["items"][0]["state"] = "FORGED_SUCCESS"
        with self.assertRaisesRegex(OwnerWorkbenchRefused, "INVALID_LOCAL_STAGE_EVIDENCE"):
            _safe_stage_results(rows, 1)

    def test_missing_required_is_blocked_with_real_os_lstat(self):
        ticket = self.controller.preview(self.request(required=["absent.txt"]))
        result = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["finding_counts"]["MISSING"], 1)

    def test_three_intents_and_competing_version_report_review(self):
        (self.root / "README_final.md").write_text("synthetic version only")
        ticket = self.controller.preview(self.request(
            goal="파일 누락 확인 그리고 인계 확인 그리고 버전 비교",
            candidates={"README.md": ["README_final.md"]},
        ))
        result = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(result["executed_steps"], 3)
        self.assertEqual(result["finding_counts"]["VERSION_REVIEW"], 1)

    def test_refuse_without_exact_consent_and_no_replay(self):
        ticket = self.controller.preview(self.request())
        with self.assertRaisesRegex(OwnerWorkbenchRefused, "LOCAL_APPROVAL_REFUSED"):
            self.controller.execute(ticket["approval_token"], "decline")
        result = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        with self.assertRaisesRegex(OwnerWorkbenchRefused, "NO_PENDING_LOCAL_APPROVAL"):
            self.controller.execute(ticket["approval_token"], CONSENT)

    def test_changed_preview_invalidates_prior_token(self):
        first = self.controller.preview(self.request())
        second = self.controller.preview(self.request(required=["absent.txt"]))
        with self.assertRaisesRegex(OwnerWorkbenchRefused, "LOCAL_APPROVAL_REFUSED"):
            self.controller.execute(first["approval_token"], CONSENT)
        actual = self.controller.execute(second["approval_token"], CONSENT)
        self.assertEqual(actual["status"], "BLOCKED")

    def test_restricted_path_refused_before_root_stat(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("ROOT ACCESSED")):
            for bad in ("../private.txt", ".env", "README.md/../../secret"):
                with self.subTest(bad=bad), self.assertRaises(OwnerWorkbenchRefused):
                    self.controller.preview(self.request(required=[bad]))

    def test_preview_requires_explicit_local_only_not_nas_acknowledgement(self):
        req = self.request()
        req["confirm_local_only"] = False
        with self.assertRaisesRegex(OwnerWorkbenchRefused, "LOCAL_SCOPE_CONFIRMATION_REQUIRED"):
            self.controller.preview(req)

    def test_symlink_file_never_followed_or_counted_present(self):
        private = self.root / "never-read.txt"
        private.write_text("sensitive fixture")
        link = self.root / "alias.txt"
        try:
            link.symlink_to(private)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink unavailable")
        ticket = self.controller.preview(self.request(required=["alias.txt"]))
        actual = self.controller.execute(ticket["approval_token"], CONSENT)
        self.assertEqual(actual["finding_counts"]["PRESENT"], 0)
        self.assertEqual(actual["finding_counts"]["NOT_CHECKED"], 1)


if __name__ == "__main__":
    unittest.main()
