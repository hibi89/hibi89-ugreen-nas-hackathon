import unittest
from integrations.ecosystem_contract import preflight_request, normalize_audit_receipt


class IntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.request = {"intent": "CHECK_REQUIRED", "folder": "/approved", "required_paths": ["README.md"], "owner_approved_metadata": True, "runtime_permissions_verified": True, "processing_location_accepted": True}

    def test_approved_preflight_is_not_execution(self):
        self.assertEqual(preflight_request(self.request).state, "READY_FOR_ADAPTER")

    def test_no_consent(self):
        self.assertFalse(preflight_request({**self.request, "owner_approved_metadata": False}).allowed)

    def test_no_runtime_permission(self):
        self.assertFalse(preflight_request({**self.request, "runtime_permissions_verified": False}).allowed)

    def test_reject_write(self):
        self.assertFalse(preflight_request({**self.request, "write": True}).allowed)

    def test_content_needs_separate_approval(self):
        r = {**self.request, "intent": "SUMMARIZE_SELECTED"}
        self.assertEqual(preflight_request(r).state, "CONTENT_NOT_CHECKED")

    def test_receipt_redacts_payload(self):
        self.assertEqual(normalize_audit_receipt({"run_id": "abc", "payload": "secret", "status": "completed"}), {"run_id": "abc", "status": "completed"})


if __name__ == "__main__":
    unittest.main()
