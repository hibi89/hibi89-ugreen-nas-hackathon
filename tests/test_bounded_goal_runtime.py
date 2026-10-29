"""Bounded 1-3 intent compiler and SHA-bound synthetic LA/SOVIA regression.

Tests use a clearly simulated LA and SOVIA. Real HAE code is NOT in public CI.
"""
from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from integrations.bounded_goal_runtime import (
    BoundedGoalExecutionRefused, run_bounded_compiled_goal,
)


class FakeMultipleLA:
    constructed = 0
    executed = 0

    def __init__(self, runtime_path, business_path):
        type(self).constructed += 1
        self.runtime_path = Path(runtime_path)
        self.business_path = Path(business_path)
        self.runs = {}

    @staticmethod
    def preflight(plan):
        return {
            "source_version": plan["version"],
            "trigger_type": plan.get("trigger", {"type": "manual"})["type"],
            "step_count": len(plan["steps"]),
            "steps": [{"id": s["id"], "op": s["op"]} for s in plan["steps"]],
            "requires_write_approval": any(s["op"] == "sqlite_put" for s in plan["steps"]),
            "requires_input_root": False,
            "executes_workflow": False,
            "scope": "synthetic-local-only",
        }

    def execute(self, plan, run_id, *, approve_writes=False):
        type(self).executed += 1
        if not approve_writes:
            raise AssertionError("write not approved")
        if run_id in self.runs:
            self.runs[run_id]["events"].append({"event_type": "run_replayed"})
            return {"synthetic": True}
        self.runtime_path.touch()
        with closing(sqlite3.connect(self.business_path)) as conn:
            conn.execute("CREATE TABLE records (run_id TEXT, step_id TEXT, payload_json TEXT)")
            literals = {}
            for step in plan["steps"]:
                if step["op"] == "literal":
                    literals[step["id"]] = step["value"]
                elif step["op"] == "sqlite_put":
                    conn.execute(
                        "INSERT INTO records VALUES (?,?,?)",
                        (run_id, step["id"], json.dumps(literals[step["from"]])),
                    )
            conn.commit()
        self.runs[run_id] = {
            "events": [{"event_type": "run_completed"}],
            "approval_receipts": [{}],
        }
        return {"synthetic": True}

    def status(self, run_id):
        return {"status": "completed" if run_id in self.runs else "missing"}

    def audit(self, run_id):
        return {"run_id": run_id, **self.runs[run_id]}

    def verify_receipts(self, plan, run_id):
        with closing(sqlite3.connect(self.business_path)) as con:
            rows = con.execute(
                "SELECT step_id FROM records WHERE run_id=?",
                (run_id,),
            ).fetchall()
        expected = {s["id"] for s in plan["steps"] if s["op"] == "sqlite_put"}
        return {"run_id": run_id, "verified": {r[0] for r in rows} == expected
                and len(rows) == len(expected)}


def fake_assess(plan, policy):
    count = sum(s["side_effect"] == "local_write" for s in plan["steps"])
    return {
        "schema_version": "sovia.plan_review.v1",
        "status": "FINDINGS_REVIEW_REQUIRED" if count else "NO_FINDINGS_STILL_UNVERIFIED",
        "finding_count": count,
        "execution_authorized": False,
        "real_la_integration_verified": False,
        "offline_only": True,
    }


def evaluate(goal="파일 누락 확인", required=None, *, advisor=fake_assess,
             api=FakeMultipleLA, candidates=None, approved=None):
    return run_bounded_compiled_goal(
        goal, api, advisor,
        required=["README.md"] if required is None else required,
        candidates=candidates, approve_plan_sha256=approved,
    )


class BoundedGoalCompilationTests(unittest.TestCase):
    def setUp(self):
        FakeMultipleLA.constructed = 0
        FakeMultipleLA.executed = 0

    def test_single_intent_preview_has_stable_scope_hash_and_no_database(self):
        a = evaluate()
        b = evaluate()
        self.assertEqual(a["status"], "WAITING_PLAN_SHA256_APPROVAL")
        self.assertEqual(a["approve_plan_sha256"], b["approve_plan_sha256"])
        self.assertEqual(a["intents"], ["CHECK_REQUIRED"])
        self.assertEqual(a["la_step_count"], 2)
        self.assertEqual(a["sovia_finding_count"], 1)
        self.assertEqual(FakeMultipleLA.constructed, 0)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_explicit_exact_sha_executes_one_synthetic_receipt_and_replay(self):
        pending = evaluate()
        row = evaluate(approved=pending["approve_plan_sha256"])
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["synthetic_write_rows"], 1)
        self.assertEqual(row["approval_receipts"], 1)
        self.assertEqual(row["duplicate_replay_writes"], 0)
        self.assertTrue(row["la_execution_verified"])
        self.assertEqual(FakeMultipleLA.constructed, 1)
        self.assertEqual(FakeMultipleLA.executed, 2)

    def test_two_distinct_natural_intents_compile_into_two_receipts(self):
        goal = "파일 누락 확인 그리고 인계 확인"
        pending = evaluate(goal)
        self.assertEqual(pending["intents"], ["CHECK_REQUIRED", "HANDOFF_AUDIT"])
        self.assertEqual(pending["la_step_count"], 4)
        row = evaluate(goal, approved=pending["approve_plan_sha256"])
        self.assertEqual(row["synthetic_write_rows"], 2)
        self.assertEqual(row["sovia_finding_count"], 2)
        self.assertEqual(row["status"], "PASS")

    def test_three_intents_require_version_candidates_and_three_writes(self):
        goal = "파일 누락 확인 그리고 인계 확인 그리고 버전 비교"
        args = {"candidates": {"README.md": ["README_final.md"]}}
        pending = evaluate(goal, **args)
        self.assertEqual(pending["intents"], [
            "CHECK_REQUIRED", "HANDOFF_AUDIT", "REVIEW_VERSIONS",
        ])
        self.assertEqual(pending["version_candidate_count"], 1)
        self.assertEqual(pending["la_step_count"], 6)
        row = evaluate(goal, approved=pending["approve_plan_sha256"], **args)
        self.assertEqual(row["synthetic_write_rows"], 3)
        self.assertEqual(row["sovia_finding_count"], 3)

    def test_changed_goal_cannot_reuse_previous_approval(self):
        pending = evaluate()
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "APPROVAL_SCOPE_SHA256_MISMATCH"):
            evaluate("인계 확인", approved=pending["approve_plan_sha256"])
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_changed_required_path_cannot_reuse_previous_approval(self):
        pending = evaluate()
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "APPROVAL_SCOPE_SHA256_MISMATCH"):
            evaluate(required=["other.md"], approved=pending["approve_plan_sha256"])
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_changed_version_candidates_cannot_reuse_previous_approval(self):
        goal = "버전 비교"
        pending = evaluate(goal, candidates={"README.md": ["draft.md"]})
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "APPROVAL_SCOPE_SHA256_MISMATCH"):
            evaluate(goal, candidates={"README.md": ["final.md"]},
                     approved=pending["approve_plan_sha256"])
        self.assertEqual(FakeMultipleLA.constructed, 0)

    def test_unapproved_or_unsafe_goal_rejected_before_lasql(self):
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "FLOWPILOT_GOAL_REFUSED"):
            evaluate("폴더 삭제해줘")
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "FLOWPILOT_GOAL_REFUSED"):
            evaluate("버전 비교")
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "FLOWPILOT_GOAL_REFUSED"):
            evaluate("파일 누락 확인 그리고 파일 누락 확인")
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_path_escape_refused_without_file_open(self):
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "FLOWPILOT_GOAL_REFUSED"):
            evaluate(required=["../secrets.env"])
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_approval_hash_validation_is_strict(self):
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "INVALID_APPROVAL_SHA256"):
            evaluate(approved=True)
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "INVALID_APPROVAL_SHA256"):
            evaluate(approved="A" * 64)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_sovia_risk_finding_cannot_be_skipped(self):
        def bypass(plan, policy):
            return {**fake_assess(plan, policy), "finding_count": 0}
        pending = evaluate()
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "LA_SOVIA_SYNTHETIC_PREFLIGHT_NOT_PROVEN"):
            evaluate(advisor=bypass, approved=pending["approve_plan_sha256"])
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_sovia_fake_execution_authorization_rejected(self):
        def unsafe(plan, policy):
            return {**fake_assess(plan, policy), "execution_authorized": True}
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "LA_SOVIA_PREFLIGHT_REFUSED"):
            evaluate(advisor=unsafe)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_la_preflight_execution_claim_rejected(self):
        class UnsafeLA(FakeMultipleLA):
            @staticmethod
            def preflight(plan):
                return {**FakeMultipleLA.preflight(plan), "executes_workflow": True}
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "LA_SOVIA_PREFLIGHT_REFUSED"):
            evaluate(api=UnsafeLA)
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_no_filenames_goal_or_local_paths_in_output(self):
        goal = "파일 누락 확인 그리고 인계 확인"
        pending = evaluate(goal, required=["private-plan.txt"])
        row = evaluate(goal, required=["private-plan.txt"],
                       approved=pending["approve_plan_sha256"])
        serialized = json.dumps(row, ensure_ascii=False)
        for secret in ("private-plan.txt", "C:", "flowpilot-compiled-", goal, "sqlite_put"):
            self.assertNotIn(secret, serialized)
        self.assertFalse(row["actual_nas_verified"])
        self.assertFalse(row["registered_uliya_expert_invoked"])
        self.assertEqual(row["release_gate"], "HOLD")

    def test_missing_receipt_checker_fails_closed(self):
        class NoVerifier(FakeMultipleLA):
            verify_receipts = None
        pending = evaluate()
        with self.assertRaisesRegex(BoundedGoalExecutionRefused, "RECEIPT_VERIFIER_REQUIRED"):
            evaluate(api=NoVerifier, approved=pending["approve_plan_sha256"])


if __name__ == "__main__":
    unittest.main()
