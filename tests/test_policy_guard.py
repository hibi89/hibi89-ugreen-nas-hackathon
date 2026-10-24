"""Pure simulated policy tests; never use user documents or run real NAS commands."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from projectready.policy_guard import Action, Policy, Result, assess

P = Policy(True, True, False, True)
class PolicyGuardTests(unittest.TestCase):
    def test_no_folder(self):
        self.assertEqual(Result.BLOCKED, assess(Action.LIST, replace(P,folder_selected=False)).decision)
    def test_no_metadata_permission(self):
        self.assertEqual(Result.BLOCKED, assess(Action.LIST, replace(P,authorized_metadata_read=False)).decision)
    def test_no_content_permission(self):
        self.assertEqual(Result.BLOCKED, assess(Action.READ,P).decision)
    def test_explicit_content_permission_policy_only(self):
        self.assertEqual(Result.ELIGIBLE_FOR_ADAPTER_CHECK,assess(Action.READ,replace(P,authorized_document_read=True)).decision)
    def test_unverified_adapter_not_checked(self):
        self.assertEqual(Result.NOT_CHECKED,assess(Action.LIST,replace(P,official_adapter_validated=False)).decision)
    def test_metadata_eligible_not_execution(self):
        o=assess(Action.LIST,P)
        self.assertEqual(Result.ELIGIBLE_FOR_ADAPTER_CHECK,o.decision)
        self.assertFalse(o.actual_tool_call_performed)
    def test_content_check_never_passed(self):
        for action in Action:
            self.assertEqual("NOT_CHECKED", assess(action,P).sensitive_content_check)
    def test_change_blocked(self):
        self.assertEqual(Result.BLOCKED,assess(Action.CHANGE,P).decision)
    def test_transfer_blocked(self):
        self.assertEqual(Result.BLOCKED,assess(Action.TRANSFER,P).decision)
    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError): assess("UNKNOWN",P)

if __name__ == "__main__":
    unittest.main()
