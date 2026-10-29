"""Integration with the real UGREEN bounded goal planner and a fake LA interface.

No NAS or file reads; both preview interfaces are passed explicitly.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations.flowpilot_la_coordinator import compose_previews, FlowPilotPreviewError
from integrations.la_bridge import LABridgeUnavailable
from integrations.approval_scope import ApprovalScopeMismatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_goal_preview import process_goal, WorkflowRefused

REQUEST = {
    "intent": "CHECK_REQUIRED",
    "folder": "/synthetic-preview",
    "required_paths": ["README.md"],
    "owner_approved_metadata": True,
    "runtime_permissions_verified": True,
    "processing_location_accepted": True,
}
PLAN = {"version": "azent.ir.v0", "steps": [{"id": "sample", "op": "literal", "value": "safe"}]}


class FakeLA:
    invoked = 0

    @classmethod
    def preflight(cls, plan):
        cls.invoked += 1
        return {
            "source_version": "azent.ir.v0", "trigger_type": "manual",
            "step_count": 1, "requires_write_approval": False,
            "requires_input_root": False, "scope": "synthetic-local-only",
            "executes_workflow": False, "steps": [{"payload": "PRIVATE"}],
        }


def combine(*, goal="파일 누락 확인", root=Path("/synthetic-preview"),
            required=None, owner_request=None, preview=process_goal, la_api=FakeLA):
    return compose_previews(
        goal, root=root, required=["README.md"] if required is None else required,
        candidates=None, la_plan=PLAN, owner_request=REQUEST if owner_request is None else owner_request,
        flowpilot_preview=preview, la_api=la_api,
    )


class FlowPilotLABridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        FakeLA.invoked = 0

    def test_actual_flowpilot_preview_with_la_metadata(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT ACCESSED")):
            row = combine()
        self.assertEqual(row["status"], "WAITING_APPROVAL")
        self.assertEqual(row["la"]["state"], "PLAN_PREFLIGHT_ONLY")
        self.assertEqual(row["flowpilot"]["planned_steps"], 1)
        self.assertFalse(row["owner_folder_metadata_accessed"])
        self.assertFalse(row["la_workflow_executed"])
        self.assertEqual(row["nas_state"], "NOT_CHECKED")
        self.assertEqual(FakeLA.invoked, 1)

    def test_missing_owner_inputs_do_not_touch_la(self):
        row = combine(root=None)
        self.assertEqual(row["status"], "WAITING_USER")
        self.assertEqual(row["la"]["state"], "NOT_CHECKED")
        self.assertEqual(FakeLA.invoked, 0)

    def test_metadata_not_approved_blocks_la(self):
        row = combine(owner_request={**REQUEST, "owner_approved_metadata": False})
        self.assertFalse(row["la"]["allowed"])
        self.assertEqual(FakeLA.invoked, 0)

    def test_la_not_installed_is_not_silent_success(self):
        with self.assertRaises(LABridgeUnavailable):
            combine(la_api=None)

    def test_unsupported_goal_fails_before_la(self):
        with self.assertRaises(WorkflowRefused):
            combine(goal="NAS 파일 모두 삭제해줘")
        self.assertEqual(FakeLA.invoked, 0)

    def test_malicious_provider_execution_claim_rejected(self):
        def bad_provider(*args, **kwargs):
            return {
                "status": "WAITING_APPROVAL", "executed_steps": 1,
                "owner_folder_metadata_accessed": False, "file_contents_opened": False,
                "registered_uliya_expert_invoked": False, "nas_verified": False,
                "planned_steps": 1, "missing_inputs": [],
            }
        with self.assertRaises(FlowPilotPreviewError):
            combine(preview=bad_provider)
        self.assertEqual(FakeLA.invoked, 0)

    def test_unexpected_preview_file_access_rejected(self):
        def bad_provider(*args, **kwargs):
            return {
                "status": "WAITING_APPROVAL", "executed_steps": 0,
                "owner_folder_metadata_accessed": True, "file_contents_opened": False,
                "registered_uliya_expert_invoked": False, "nas_verified": False,
                "planned_steps": 1, "missing_inputs": [],
            }
        with self.assertRaises(FlowPilotPreviewError):
            combine(preview=bad_provider)

    def test_other_folder_approval_never_reaches_la(self):
        with self.assertRaises(ApprovalScopeMismatch):
            combine(root=Path("/not-the-approved-folder"))
        self.assertEqual(FakeLA.invoked, 0)

    def test_other_file_approval_never_reaches_la(self):
        with self.assertRaises(ApprovalScopeMismatch):
            combine(required=["unexpected.md"])
        self.assertEqual(FakeLA.invoked, 0)

    def test_multi_action_requires_exact_authorized_intents(self):
        with self.assertRaises(ApprovalScopeMismatch):
            combine(goal="파일 누락 확인하고 인계 확인")
        self.assertEqual(FakeLA.invoked, 0)

    def test_private_file_names_never_echoed(self):
        row = combine()
        self.assertNotIn("/synthetic-preview", str(row))
        self.assertNotIn("README.md", str(row))
        self.assertNotIn("PRIVATE", str(row))


if __name__ == "__main__":
    unittest.main()
