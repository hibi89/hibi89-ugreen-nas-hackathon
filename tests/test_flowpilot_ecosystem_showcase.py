"""Executable, bounded synthetic showcase regression cases.

The default LA is a clearly labeled simulator. The separate CI step runs
the same demo against actual public SOVIA source pinned to one commit.
"""
import json
import unittest
from unittest.mock import patch
from tools.flowpilot_ecosystem_showcase import showcase, SimulatedLA


class SpyLA(SimulatedLA):
    called = 0

    @classmethod
    def preflight(cls, plan):
        cls.called += 1
        return SimulatedLA.preflight(plan)


class FakeSOVIA:
    called = 0
    last_facts = None

    @classmethod
    def assess(cls, facts, policy):
        cls.called += 1
        cls.last_facts = facts
        is_write = any(x["side_effect"] == "local_write" for x in facts["steps"])
        return {
            "schema_version": "sovia.plan_review.v1",
            "status": "FINDINGS_REVIEW_REQUIRED" if is_write else "NO_FINDINGS_STILL_UNVERIFIED",
            "finding_count": 1 if is_write else 0,
            "execution_authorized": False, "real_la_integration_verified": False,
            "offline_only": True,
        }


class ShowcaseTests(unittest.TestCase):
    def setUp(self):
        SpyLA.called = 0
        FakeSOVIA.called = 0
        FakeSOVIA.last_facts = None

    def test_read_only_preview(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT ACCESSED")):
            row = showcase("read_only", FakeSOVIA.assess, la_api=SpyLA)
        self.assertEqual(row["flowpilot"], "WAITING_APPROVAL")
        self.assertEqual(row["la"], "PLAN_PREFLIGHT_ONLY")
        self.assertEqual(row["advisory_finding_count"], 0)
        self.assertEqual(SpyLA.called, 1)
        self.assertFalse(row["execution_authorized"])

    def test_write_risk_is_advisory_not_approval(self):
        row = showcase("write_review", FakeSOVIA.assess, la_api=SpyLA)
        self.assertEqual(row["sovia"], "ADVISORY_ONLY")
        self.assertEqual(row["advisory_finding_count"], 1)
        self.assertEqual(FakeSOVIA.last_facts["steps"][1]["side_effect"], "local_write")
        self.assertFalse(row["la_workflow_executed"])
        self.assertEqual(row["release_gate"], "HOLD")

    def test_missing_input_never_calls_la_or_sovia(self):
        row = showcase("missing_input", FakeSOVIA.assess, la_api=SpyLA)
        self.assertEqual(row["flowpilot"], "WAITING_USER")
        self.assertEqual(row["la"], "NOT_CHECKED")
        self.assertEqual(SpyLA.called, 0)
        self.assertEqual(FakeSOVIA.called, 0)

    def test_declined_approval_never_calls_la_or_sovia(self):
        row = showcase("declined", FakeSOVIA.assess, la_api=SpyLA)
        self.assertEqual(row["flowpilot"], "WAITING_APPROVAL")
        self.assertEqual(row["la"], "NOT_CHECKED")
        self.assertEqual(SpyLA.called, 0)
        self.assertEqual(FakeSOVIA.called, 0)

    def test_no_paths_or_run_data_exposed(self):
        row = showcase("write_review", FakeSOVIA.assess, la_api=SpyLA)
        serialized = json.dumps(row, ensure_ascii=False)
        self.assertNotIn("README.md", serialized)
        self.assertNotIn("ugreen-showcase-", serialized)
        self.assertNotIn("sqlite_put", serialized)
        self.assertFalse(row["actual_nas_verified"])
        self.assertFalse(row["registered_uliya_expert_invoked"])
        self.assertEqual(row["la_preflight_source"], "SIMULATED_LA_PREFLIGHT")

    def test_no_unknown_scenario(self):
        with self.assertRaises(ValueError):
            showcase("delete_all", FakeSOVIA.assess, la_api=SpyLA)


if __name__ == "__main__":
    unittest.main()
