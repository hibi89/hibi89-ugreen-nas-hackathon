"""Six-scenario local-lstat matrix contracts, fake HAE LA and fake SOVIA.

The OS really reads metadata of disposable test files. These tests do NOT
supply real private HAE source; owner-local pinned HAE command does that.
"""
from __future__ import annotations

import unittest

from test_bounded_goal_runtime import FakeMultipleLA, fake_assess
from tools.verify_local_lstat_matrix import MatrixRefused, run_matrix


class LocalLstatMatrixTests(unittest.TestCase):
    def setUp(self):
        FakeMultipleLA.constructed = 0
        FakeMultipleLA.executed = 0

    def test_default_six_scenarios_require_no_db_execution(self):
        result = run_matrix(FakeMultipleLA, fake_assess)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["scenario_count"], 6)
        self.assertEqual(result["synthetic_sqlite_execution"], "NOT_RUN_NO_WRITE_APPROVAL")
        self.assertEqual(result["actual_local_present"], "PASS")
        self.assertEqual(result["actual_local_missing"], "BLOCKED_AS_EXPECTED")
        self.assertEqual(result["actual_local_version_conflict"], "REVIEW_REQUIRED")
        self.assertEqual(result["changed_observation_reused_approval"], "REFUSED_AS_EXPECTED")
        self.assertEqual(result["synthetic_write_rows"], 0)
        self.assertEqual(FakeMultipleLA.constructed, 0)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_explicit_synthetic_write_produces_two_receipts_without_duplicates(self):
        result = run_matrix(
            FakeMultipleLA, fake_assess, approve_synthetic_writes=True,
        )
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["synthetic_sqlite_execution"], "PASS")
        self.assertEqual(result["synthetic_write_rows"], 2)
        self.assertEqual(result["approval_receipts"], 1)
        self.assertEqual(result["replay_duplicate_writes"], 0)
        self.assertTrue(result["disposable_fixture_deleted_after_run"])
        self.assertEqual(FakeMultipleLA.constructed, 1)
        self.assertEqual(FakeMultipleLA.executed, 2)

    def test_claimed_nas_and_customer_data_never_promoted(self):
        result = run_matrix(
            FakeMultipleLA, fake_assess, approve_synthetic_writes=True,
        )
        self.assertFalse(result["actual_nas_verified"])
        self.assertFalse(result["registered_uliya_expert_invoked"])
        self.assertFalse(result["user_project_folders_accessed"])
        self.assertFalse(result["customer_data_used"])
        self.assertFalse(result["file_contents_opened"])
        self.assertFalse(result["devpost_submitted"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_string_consent_refused_before_access(self):
        with self.assertRaisesRegex(MatrixRefused, "INVALID_SYNTHETIC_WRITE_CONSENT"):
            run_matrix(FakeMultipleLA, fake_assess, approve_synthetic_writes="true")
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_missing_sovia_interface_refused(self):
        with self.assertRaisesRegex(MatrixRefused, "MISSING_REAL_OR_INJECTED_ENGINES"):
            run_matrix(FakeMultipleLA, None, approve_synthetic_writes=True)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_false_sovia_advisory_never_runs_la(self):
        def fake_no_findings(facts, policy):
            return {**fake_assess(facts, policy), "finding_count": 0}
        with self.assertRaises(ValueError):
            run_matrix(FakeMultipleLA, fake_no_findings, approve_synthetic_writes=True)
        self.assertEqual(FakeMultipleLA.constructed, 0)
        self.assertEqual(FakeMultipleLA.executed, 0)


if __name__ == "__main__":
    unittest.main()
