"""UGREEN's real goal preview -> one LA preflight -> optional SOVIA advisory.

All sources are synthetic and in-memory. No LA execution, NAS or user-file access.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations.flowpilot_la_coordinator import compose_previews
from integrations.sovia_bridge import AdvisoryUnavailable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_goal_preview import process_goal, WorkflowRefused


REQUEST = {
    "intent": "CHECK_REQUIRED", "folder": "/synthetic-only",
    "required_paths": ["README.md"], "owner_approved_metadata": True,
    "runtime_permissions_verified": True, "processing_location_accepted": True,
}
POLICY = {"schema_version": "1.0", "policy": {
    "allowed_tools": ["la_literal", "la_sqlite_put"],
    "approved_destinations": [], "sensitive_targets": [],
}}


class StubLA:
    calls = 0
    operation = "sqlite_put"

    @classmethod
    def preflight(cls, plan):
        cls.calls += 1
        operation = cls.operation
        return {
            "source_version": "azent.ir.v0", "trigger_type": "manual",
            "step_count": 1, "requires_write_approval": operation == "sqlite_put",
            "requires_input_root": False, "executes_workflow": False,
            "scope": "synthetic-local-only",
            "steps": [{"id": "private_customer_identifier", "op": operation}],
        }


class StubSOVIA:
    calls = 0
    facts = None

    @classmethod
    def assess(cls, facts, policy):
        cls.calls += 1
        cls.facts = facts
        has_write = any(x["side_effect"] == "local_write" for x in facts["steps"])
        return {
            "schema_version": "sovia.plan_review.v1",
            "status": "FINDINGS_REVIEW_REQUIRED" if has_write else "NO_FINDINGS_STILL_UNVERIFIED",
            "finding_count": 1 if has_write else 0,
            "execution_authorized": False, "real_la_integration_verified": False,
            "offline_only": True,
        }


def review(*, root=Path("/synthetic-only"), required=None, request=None,
           la_api=StubLA, advisor=StubSOVIA.assess, policy=POLICY, goal="필수 파일 확인"):
    return compose_previews(
        goal, root=root, required=["README.md"] if required is None else required,
        candidates=None, la_plan={"version": "azent.ir.v0", "steps": []},
        owner_request=REQUEST if request is None else request,
        flowpilot_preview=process_goal, la_api=la_api,
        sovia_assess=advisor, sovia_policy=policy,
    )


class ThreeProductSyntheticIntegrationTests(unittest.TestCase):
    def setUp(self):
        StubLA.calls = 0
        StubLA.operation = "sqlite_put"
        StubSOVIA.calls = 0

    def test_actual_flowpilot_preview_la_and_sovia_one_pass(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("OWNER ROOT TOUCHED")):
            result = review()
        self.assertEqual(result["status"], "WAITING_APPROVAL")
        self.assertEqual(result["la"]["state"], "PLAN_PREFLIGHT_ONLY")
        self.assertEqual(result["la"]["sovia"]["state"], "ADVISORY_ONLY")
        self.assertEqual(result["la"]["sovia"]["finding_count"], 1)
        self.assertEqual(StubLA.calls, 1)
        self.assertEqual(StubSOVIA.calls, 1)
        self.assertFalse(result["owner_folder_metadata_accessed"])
        self.assertEqual(result["nas_state"], "NOT_CHECKED")

    def test_original_la_step_name_redacted(self):
        review()
        self.assertEqual(StubSOVIA.facts["steps"][0]["step_id"], "step_1")
        self.assertNotIn("private_customer_identifier", str(StubSOVIA.facts))

    def test_missing_input_skips_all_followup_engines(self):
        result = review(root=None)
        self.assertEqual(result["status"], "WAITING_USER")
        self.assertEqual(StubLA.calls, 0)
        self.assertEqual(StubSOVIA.calls, 0)

    def test_declined_owner_approval_skips_both_engines(self):
        result = review(request={**REQUEST, "owner_approved_metadata": False})
        self.assertFalse(result["la"]["allowed"])
        self.assertEqual(StubLA.calls, 0)
        self.assertEqual(StubSOVIA.calls, 0)

    def test_readonly_plan_has_zero_findings_but_not_approved(self):
        StubLA.operation = "literal"
        result = review()
        self.assertEqual(result["la"]["sovia"]["finding_count"], 0)
        self.assertFalse(result["la"]["sovia"]["execution_authorized"])

    def test_unavailable_advisor_rejected_after_la_preview(self):
        with self.assertRaises(AdvisoryUnavailable):
            review(advisor=None)
        self.assertEqual(StubLA.calls, 1)

    def test_unknown_la_operation_rejected_before_sovia(self):
        StubLA.operation = "external_payment"
        with self.assertRaises(AdvisoryUnavailable):
            review()
        self.assertEqual(StubSOVIA.calls, 0)

    def test_unrecognized_goal_stops_before_la(self):
        with self.assertRaises(WorkflowRefused):
            review(goal="파일 삭제해줘")
        self.assertEqual(StubLA.calls, 0)
        self.assertEqual(StubSOVIA.calls, 0)


if __name__ == "__main__":
    unittest.main()
