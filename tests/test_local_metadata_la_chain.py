"""Actual disposable local lstat -> bounded FlowPilot -> synthetic LA/SOVIA tests.

The file-inspection portion calls the OS on temporary synthetic files.
Injected LA and SOVIA are fakes: this does NOT verify private HAE/NAS/Uliya.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations.local_metadata_la_chain import (
    LocalObservationRefused,
    run_local_observation_chain,
)
from test_bounded_goal_runtime import FakeMultipleLA, fake_assess


class LocalMetadataLAChainTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ugreen-lstat-synthetic-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / "README.md").write_bytes(b"only disposable synthetic content")
        FakeMultipleLA.constructed = 0
        FakeMultipleLA.executed = 0

    def inspect(self, goal="파일 누락 확인", required=None, *, candidates=None,
                consent=False, approved=None, la=FakeMultipleLA, sovia=fake_assess):
        return run_local_observation_chain(
            goal, self.root, ["README.md"] if required is None else required,
            la, sovia, candidates=candidates,
            approve_local_metadata=consent, approve_plan_sha256=approved,
        )

    def test_no_consent_never_touches_local_root(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("ROOT ACCESSED WITHOUT APPROVAL")):
            row = self.inspect()
        self.assertEqual(row["status"], "WAITING_LOCAL_METADATA_APPROVAL")
        self.assertFalse(row["local_inspection_performed"])
        self.assertEqual(FakeMultipleLA.constructed, 0)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_metadata_consent_reads_present_state_but_never_runs_la(self):
        row = self.inspect(consent=True)
        self.assertEqual(row["status"], "WAITING_EXACT_LOCAL_PLAN_APPROVAL")
        self.assertEqual(row["local_state_counts"]["PRESENT"], 1)
        self.assertTrue(row["local_inspection_performed"])
        self.assertEqual(row["sovia_finding_count"], 1)
        self.assertEqual(row["synthetic_write_rows"], 0)
        self.assertEqual(FakeMultipleLA.constructed, 0)
        self.assertFalse(row["actual_nas_verified"])

    def test_explicit_hash_approved_present_metadata_persists_only_counts(self):
        preview = self.inspect(consent=True)
        row = self.inspect(consent=True, approved=preview["approve_plan_sha256"])
        self.assertEqual(row["status"], "PASS")
        self.assertTrue(row["la_execution_verified"])
        self.assertEqual(row["synthetic_write_rows"], 1)
        self.assertEqual(row["approval_receipts"], 1)
        self.assertEqual(row["replay_duplicate_writes"], 0)
        self.assertTrue(row["ephemeral_sqlite_deleted_after_run"])
        self.assertEqual(FakeMultipleLA.constructed, 1)
        self.assertEqual(FakeMultipleLA.executed, 2)
        self.assertFalse(row["file_contents_opened"])

    def test_two_intents_persist_two_sanitized_counts_after_sha(self):
        goal = "파일 누락 확인 그리고 인계 확인"
        preview = self.inspect(goal, consent=True)
        self.assertEqual(preview["intent_count"], 2)
        self.assertEqual(preview["local_state_counts"]["PRESENT"], 2)
        row = self.inspect(goal, consent=True, approved=preview["approve_plan_sha256"])
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["synthetic_write_rows"], 2)
        self.assertEqual(row["sovia_finding_count"], 2)

    def test_missing_file_blocks_la_and_returns_true_local_missing(self):
        row = self.inspect(required=["missing.txt"], consent=True)
        self.assertEqual(row["status"], "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED")
        self.assertEqual(row["local_state_counts"]["MISSING"], 1)
        self.assertTrue(row["local_inspection_performed"])
        self.assertEqual(row["synthetic_write_rows"], 0)
        self.assertFalse(row["la_execution_verified"])
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_version_conflict_yields_review_not_arbitrary_file_selection(self):
        (self.root / "README_final.md").write_bytes(b"new synthetic version")
        options = {"README.md": ["README_final.md"]}
        preview = self.inspect("버전 비교", candidates=options, consent=True)
        self.assertEqual(preview["status"], "WAITING_EXACT_LOCAL_PLAN_APPROVAL")
        self.assertEqual(preview["local_state_counts"]["VERSION_REVIEW"], 1)
        row = self.inspect(
            "버전 비교", candidates=options, consent=True,
            approved=preview["approve_plan_sha256"],
        )
        self.assertEqual(row["synthetic_write_rows"], 1)
        self.assertEqual(row["local_state_counts"]["VERSION_REVIEW"], 1)
        self.assertEqual(row["release_gate"], "HOLD")

    def test_changed_local_state_invalidates_existing_approval(self):
        (self.root / "README_final.md").write_bytes(b"new synthetic version")
        options = {"README.md": ["README_final.md"]}
        before = self.inspect("버전 비교", candidates=options, consent=True)
        (self.root / "README_final.md").unlink()
        with self.assertRaisesRegex(
                LocalObservationRefused, "LOCAL_PLAN_APPROVAL_HASH_MISMATCH"):
            self.inspect("버전 비교", candidates=options, consent=True,
                         approved=before["approve_plan_sha256"])
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_renamed_missing_file_does_not_reuse_prior_approval(self):
        preview = self.inspect(consent=True)
        (self.root / "README.md").unlink()
        blocked = self.inspect(consent=True, approved=preview["approve_plan_sha256"])
        self.assertEqual(blocked["status"], "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED")
        self.assertEqual(blocked["local_state_counts"]["MISSING"], 1)
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_traversal_and_mutating_goal_rejected_before_root_inspection(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("ROOT WAS TOUCHED")):
            with self.assertRaisesRegex(LocalObservationRefused, "FLOWPILOT_LOCAL_PREVIEW_REFUSED"):
                self.inspect(required=["../secret.key"], consent=True)
            with self.assertRaisesRegex(LocalObservationRefused, "FLOWPILOT_LOCAL_PREVIEW_REFUSED"):
                self.inspect("파일 삭제해줘", consent=True)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_plan_approval_without_metadata_consent_refused(self):
        with self.assertRaisesRegex(LocalObservationRefused, "METADATA_CONSENT_REQUIRED"):
            self.inspect(approved="a" * 64)
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_nonboolean_consent_and_invalid_hash_fail_closed(self):
        with self.assertRaisesRegex(LocalObservationRefused, "INVALID_LOCAL_METADATA_CONSENT"):
            self.inspect(consent="true")
        with self.assertRaisesRegex(LocalObservationRefused, "INVALID_PLAN_APPROVAL_HASH"):
            self.inspect(consent=True, approved=True)
        with self.assertRaisesRegex(LocalObservationRefused, "INVALID_PLAN_APPROVAL_HASH"):
            self.inspect(consent=True, approved="A" * 64)

    def test_sovia_missing_advisory_blocks_sqlite(self):
        def lying_assess(plan, policy):
            return {**fake_assess(plan, policy), "finding_count": 0}
        with self.assertRaisesRegex(LocalObservationRefused, "LOCAL_LA_SOVIA_ADVISORY_NOT_PROVEN"):
            self.inspect(consent=True, sovia=lying_assess)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_untrusted_observation_claiming_content_access_is_refused(self):
        # Preview from real FlowPilot; subsequent inspection tampered to
        # claim contents were opened. The bridge must refuse to persist.
        from tools.flowpilot_ecosystem_showcase import process_goal
        actual_preview = process_goal(
            "파일 누락 확인", root=self.root, required=["README.md"],
            metadata_consent=False,
        )
        forged = {
            "status": "NEEDS_REVIEW", "planned_steps": 1,
            "executed_steps": 1,
            "observed": [{"index": 1, "status": "NEEDS_REVIEW",
                          "inspected_local_metadata": True,
                          "items": [{"index": 1, "state": "PRESENT",
                                     "local_reference_count": 1}]}],
            "owner_folder_metadata_accessed": True,
            "file_contents_opened": True,
            "raw_paths_returned": False, "nas_verified": False,
            "registered_uliya_expert_invoked": False,
        }
        with patch("integrations.local_metadata_la_chain.process_goal",
                   side_effect=[actual_preview, forged]):
            with self.assertRaisesRegex(LocalObservationRefused, "UNVERIFIED_LOCAL_METADATA"):
                self.inspect(consent=True)
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_one_missing_item_in_multi_goal_never_runs_next_la(self):
        row = self.inspect("파일 누락 확인 그리고 인계 확인",
                           required=["README.md", "missing.csv"], consent=True)
        self.assertEqual(row["status"], "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED")
        self.assertEqual(row["local_state_counts"]["PRESENT"], 1)
        self.assertEqual(row["local_state_counts"]["MISSING"], 1)
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_missing_version_candidates_only_asks_for_inputs(self):
        row = self.inspect("버전 비교", consent=False)
        self.assertEqual(row["status"], "WAITING_USER")
        self.assertFalse(row["local_inspection_performed"])
        self.assertIn("version_candidate_mapping", row["missing_slots"])

    def test_invalid_root_fails_without_exposing_root_path(self):
        missing_root = self.root / "unavailable"
        with self.assertRaisesRegex(LocalObservationRefused, "UNVERIFIED_LOCAL_METADATA"):
            run_local_observation_chain(
                "파일 누락 확인", missing_root, ["README.md"],
                FakeMultipleLA, fake_assess, approve_local_metadata=True,
            )

    def test_metadata_only_no_actual_vendor_invocation(self):
        row = self.inspect(consent=True)
        out = json.dumps(row, ensure_ascii=False)
        self.assertNotIn(str(self.root), out)
        self.assertNotIn("README.md", out)
        self.assertNotIn("only disposable synthetic content", out)
        self.assertFalse(row["registered_uliya_expert_invoked"])
        self.assertFalse(row["actual_nas_verified"])
        self.assertEqual(row["release_gate"], "HOLD")

    def test_symlink_file_is_blocked_without_following_target(self):
        secret = self.root / "private.txt"
        secret.write_bytes(b"never open")
        link = self.root / "alias.txt"
        try:
            link.symlink_to(secret)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable in this environment")
        row = self.inspect(required=["alias.txt"], consent=True)
        self.assertEqual(row["status"], "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED")
        self.assertEqual(row["local_state_counts"]["NOT_CHECKED"], 1)
        self.assertEqual(FakeMultipleLA.executed, 0)


if __name__ == "__main__":
    unittest.main()
