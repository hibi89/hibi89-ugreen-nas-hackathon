import unittest
from pathlib import Path
from integrations.approval_scope import ApprovalScopeMismatch, require_exact_approval_scope

BASE = {"intent": "CHECK_REQUIRED", "folder": "/preview", "required_paths": ["README.md"]}
P = {"status": "WAITING_APPROVAL", "plan": [{"index": 1, "read_only_action": "check required files"}]}


def check(request=BASE, preview=P, root=Path('/preview'), required=None, candidates=None):
    return require_exact_approval_scope(request, root=root,
        required=["README.md"] if required is None else required,
        candidates=candidates, preview=preview)


class ApprovalScopeTests(unittest.TestCase):
    def test_exact_scope(self):
        self.assertTrue(check())

    def test_folder_mismatch(self):
        with self.assertRaises(ApprovalScopeMismatch):
            check(root=Path('/other'))

    def test_checklist_mismatch(self):
        with self.assertRaises(ApprovalScopeMismatch):
            check(required=["other.md"])

    def test_intent_mismatch(self):
        with self.assertRaises(ApprovalScopeMismatch):
            check(request={**BASE, "intent": "HANDOFF_AUDIT"})

    def test_multi_action_requires_all_intents(self):
        multi={"status": "WAITING_APPROVAL", "plan": [
            {"index": 1, "read_only_action": "check required files"},
            {"index": 2, "read_only_action": "check handoff deliverables"}]}
        with self.assertRaises(ApprovalScopeMismatch):
            check(preview=multi)
        self.assertTrue(check(preview=multi, request={**BASE,
            "authorized_intents": ["CHECK_REQUIRED", "HANDOFF_AUDIT"]}))

    def test_version_options_require_exact_approval(self):
        version={"status": "WAITING_APPROVAL", "plan": [
            {"index": 1, "read_only_action": "compare versions"}]}
        choices={"final.pdf": ["final_v2.pdf"]}
        req={**BASE, "intent": "REVIEW_VERSIONS"}
        with self.assertRaises(ApprovalScopeMismatch):
            check(request=req, preview=version, candidates=choices)
        self.assertTrue(check(request={**req, "version_candidates": choices},
                              preview=version, candidates=choices))

    def test_invalid_preview_steps(self):
        with self.assertRaises(ApprovalScopeMismatch):
            check(preview={"status": "WAITING_APPROVAL", "plan": [
                {"index": 2, "read_only_action": "check required files"}]})

    def test_malformed_labels_rejected(self):
        with self.assertRaises(ApprovalScopeMismatch):
            check(preview={"status": "WAITING_APPROVAL", "plan": [
                {"index": 1, "read_only_action": "delete"}]})

    def test_no_fs_inspection(self):
        self.assertTrue(check(root=Path('/preview')))

if __name__ == '__main__':
    unittest.main()
