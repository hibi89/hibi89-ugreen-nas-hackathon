"""Contiguous synthetic UGREEN goal -> LA -> SOVIA -> SQLite regression.

CI injects a fake LA executor. It does not import private HAE or verify NAS.
The dedicated owner-local CLI separately imports exact Git-pinned real sources.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import unittest

from integrations.goal_la_sovia_runtime import (
    SyntheticChainRefused, run_connected_synthetic,
)
from test_verify_la_runtime_bridge import SyntheticLA


class ReceiptCapableLA(SyntheticLA):
    constructed = 0
    executed = 0
    previewed = 0

    def __init__(self, state_path, business_path):
        type(self).constructed += 1
        super().__init__(state_path, business_path)

    @classmethod
    def preflight(cls, plan):
        cls.previewed += 1
        return super().preflight(plan)

    def execute(self, plan, run_id, *, approve_writes=False):
        type(self).executed += 1
        return super().execute(plan, run_id, approve_writes=approve_writes)

    def verify_receipts(self, plan, run_id):
        if run_id not in self.history:
            return {"run_id": run_id, "verified": False}
        with closing(sqlite3.connect(self.business_path)) as con:
            count = con.execute(
                "SELECT COUNT(*) FROM records WHERE run_id=? AND step_id=?",
                (run_id, "store")
            ).fetchone()[0]
        return {"run_id": run_id, "verified": count == 1}


def assess(facts, policy):
    has_write = any(step["side_effect"] == "local_write" for step in facts["steps"])
    return {
        "schema_version": "sovia.plan_review.v1",
        "status": "FINDINGS_REVIEW_REQUIRED" if has_write else "NO_FINDINGS_STILL_UNVERIFIED",
        "finding_count": 1 if has_write else 0,
        "execution_authorized": False,
        "real_la_integration_verified": False,
        "offline_only": True,
    }


class ConnectedSyntheticGoalRuntimeTests(unittest.TestCase):
    def setUp(self):
        ReceiptCapableLA.constructed = 0
        ReceiptCapableLA.executed = 0
        ReceiptCapableLA.previewed = 0

    def test_default_no_write_and_sovia_reviewed(self):
        report = run_connected_synthetic(ReceiptCapableLA, assess)
        self.assertEqual(report["status"], "WAITING_EXPLICIT_SYNTHETIC_WRITE_APPROVAL")
        self.assertFalse(report["la_execution_verified"])
        self.assertTrue(report["sovia_advisory_reviewed"])
        self.assertEqual(ReceiptCapableLA.previewed, 1)
        self.assertEqual(ReceiptCapableLA.constructed, 0)
        self.assertEqual(ReceiptCapableLA.executed, 0)
        self.assertFalse(report["actual_nas_verified"])

    def test_explicit_synthetic_write_audited_and_idempotent(self):
        report = run_connected_synthetic(
            ReceiptCapableLA, assess, approve_synthetic_write=True,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["la_execution_verified"])
        self.assertTrue(report["sovia_advisory_reviewed"])
        self.assertEqual(report["synthetic_write_rows"], 1)
        self.assertEqual(report["approval_receipts"], 1)
        self.assertEqual(report["replay_duplicate_writes"], 0)
        self.assertEqual(ReceiptCapableLA.executed, 2)
        self.assertFalse(report["customer_data_used"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_output_redacts_private_paths_and_values(self):
        result = run_connected_synthetic(
            ReceiptCapableLA, assess, approve_synthetic_write=True,
        )
        out = json.dumps(result)
        for forbidden in ("README.md", "sqlite_put", "flowpilot-connected-synthetic-",
                          "ugreen-private-sentinel", "business.sqlite"):
            self.assertNotIn(forbidden, out)

    def test_unsupported_goal_rejected_before_preflight_or_execution(self):
        with self.assertRaisesRegex(SyntheticChainRefused, "UNSUPPORTED_SYNTHETIC_GOAL"):
            run_connected_synthetic(ReceiptCapableLA, assess, goal="파일 전체 삭제")
        self.assertEqual(ReceiptCapableLA.previewed, 0)
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_string_approval_not_accepted(self):
        with self.assertRaisesRegex(SyntheticChainRefused, "INVALID_APPROVAL_TYPE"):
            run_connected_synthetic(ReceiptCapableLA, assess, approve_synthetic_write="true")
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_missing_sovia_refused_before_execution(self):
        with self.assertRaisesRegex(SyntheticChainRefused, "MISSING_LA_OR_SOVIA_INTERFACE"):
            run_connected_synthetic(ReceiptCapableLA, None, approve_synthetic_write=True)
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_sovia_does_not_authorize_execution(self):
        def unsafe(facts, policy):
            return {**assess(facts, policy), "execution_authorized": True}
        with self.assertRaisesRegex(SyntheticChainRefused, "CONNECTED_PREFLIGHT_REFUSED"):
            run_connected_synthetic(ReceiptCapableLA, unsafe, approve_synthetic_write=True)
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_sovia_missed_write_finding_blocks(self):
        def missed(facts, policy):
            return {**assess(facts, policy), "finding_count": 0}
        with self.assertRaisesRegex(SyntheticChainRefused, "CONNECTED_PREFLIGHT_NOT_PROVEN"):
            run_connected_synthetic(ReceiptCapableLA, missed, approve_synthetic_write=True)
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_preflight_claims_execution_blocks(self):
        class UnsafePreviewLA(ReceiptCapableLA):
            @staticmethod
            def preflight(plan):
                return {**SyntheticLA.preflight(plan), "executes_workflow": True}
        with self.assertRaisesRegex(SyntheticChainRefused, "CONNECTED_PREFLIGHT_REFUSED"):
            run_connected_synthetic(UnsafePreviewLA, assess, approve_synthetic_write=True)
        self.assertEqual(ReceiptCapableLA.executed, 0)

    def test_missing_receipt_verifier_blocks(self):
        with self.assertRaisesRegex(SyntheticChainRefused, "RECEIPT_INTEGRITY_CHECK_UNAVAILABLE"):
            run_connected_synthetic(SyntheticLA, assess, approve_synthetic_write=True)

    def test_false_receipt_integrity_blocks(self):
        class LyingReceiptLA(ReceiptCapableLA):
            def verify_receipts(self, plan, run_id):
                return {"run_id": run_id, "verified": False}
        with self.assertRaisesRegex(SyntheticChainRefused, "RECEIPT_INTEGRITY_CHECK_FAILED"):
            run_connected_synthetic(LyingReceiptLA, assess, approve_synthetic_write=True)

    def test_duplicate_replay_is_detected(self):
        class DuplicateOnReplayLA(ReceiptCapableLA):
            def execute(self, plan, run_id, *, approve_writes=False):
                replaying = run_id in self.history
                result = super().execute(plan, run_id, approve_writes=approve_writes)
                if replaying:
                    with closing(sqlite3.connect(self.business_path)) as con:
                        con.execute("INSERT INTO records VALUES (?, ?)", (run_id, "store"))
                        con.commit()
                return result
        with self.assertRaisesRegex(SyntheticChainRefused, "REPLAY_NOT_IDEMPOTENT"):
            run_connected_synthetic(DuplicateOnReplayLA, assess, approve_synthetic_write=True)


if __name__ == "__main__":
    unittest.main()
