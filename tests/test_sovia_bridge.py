import unittest

from integrations.sovia_bridge import AdvisoryUnavailable, assess_la_preview

REQUEST = {"intent": "CHECK_REQUIRED", "folder": "/synthetic",
           "required_paths": ["README.md"], "owner_approved_metadata": True,
           "runtime_permissions_verified": True, "processing_location_accepted": True}
PREVIEW = {"source_version": "azent.ir.v0", "scope": "synthetic-local-only",
           "executes_workflow": False, "step_count": 1, "requires_write_approval": True,
           "steps": [{"id": "user_private_name", "op": "sqlite_put"}]}
POLICY = {"schema_version": "1.0", "policy": {"allowed_tools": ["la_sqlite_put"],
          "approved_destinations": [], "sensitive_targets": []}}


class FakeAdvisor:
    invoked = 0
    received = None

    @classmethod
    def assess(cls, plan, policy):
        cls.invoked += 1
        cls.received = plan
        return {"schema_version": "sovia.plan_review.v1",
                "status": "FINDINGS_REVIEW_REQUIRED",
                "finding_count": 1, "execution_authorized": False,
                "real_la_integration_verified": False, "offline_only": True}


class SOVIABridgeTests(unittest.TestCase):
    def setUp(self):
        FakeAdvisor.invoked = 0

    def test_approved_advisory_only(self):
        result = assess_la_preview(REQUEST, PREVIEW, POLICY, FakeAdvisor.assess)
        self.assertEqual(result["state"], "ADVISORY_ONLY")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["nas_state"], "NOT_CHECKED")

    def test_redacts_real_step_identifier(self):
        assess_la_preview(REQUEST, PREVIEW, POLICY, FakeAdvisor.assess)
        self.assertEqual(FakeAdvisor.received["steps"][0]["step_id"], "step_1")
        self.assertNotIn("user_private_name", str(FakeAdvisor.received))

    def test_block_before_advisor(self):
        row = assess_la_preview({**REQUEST, "owner_approved_metadata": False},
                                PREVIEW, POLICY, FakeAdvisor.assess)
        self.assertFalse(row["allowed"])
        self.assertEqual(FakeAdvisor.invoked, 0)

    def test_no_advisor(self):
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, PREVIEW, POLICY, None)

    def test_unsupported_operation(self):
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, {**PREVIEW, "steps": [{"id": "a", "op": "http_post"}]},
                              POLICY, FakeAdvisor.assess)

    def test_write_approval_mismatch(self):
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, {**PREVIEW, "requires_write_approval": False},
                              POLICY, FakeAdvisor.assess)

    def test_advisor_must_not_authorize_run(self):
        def wrong(*args):
            return {**FakeAdvisor.assess(*args), "execution_authorized": True}
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, PREVIEW, POLICY, wrong)

    def test_unverified_scope_rejected(self):
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, {**PREVIEW, "scope": "real-nas"},
                              POLICY, FakeAdvisor.assess)

    def test_negative_finding_count_rejected(self):
        def negative(*args):
            return {**FakeAdvisor.assess(*args), "finding_count": -1}
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, PREVIEW, POLICY, negative)

    def test_boolean_finding_count_rejected(self):
        def boolean(*args):
            return {**FakeAdvisor.assess(*args), "finding_count": True}
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, PREVIEW, POLICY, boolean)

    def test_excessive_finding_count_rejected(self):
        def excessive(*args):
            return {**FakeAdvisor.assess(*args), "finding_count": 1025}
        with self.assertRaises(AdvisoryUnavailable):
            assess_la_preview(REQUEST, PREVIEW, POLICY, excessive)


if __name__ == "__main__":
    unittest.main()
