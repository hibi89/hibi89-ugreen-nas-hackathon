import unittest

from integrations.la_bridge import LABridgeUnavailable, preflight_la, read_la_audit

REQUEST = {
    "intent": "CHECK_REQUIRED",
    "folder": "/approved",
    "required_paths": ["README.md"],
    "owner_approved_metadata": True,
    "runtime_permissions_verified": True,
    "processing_location_accepted": True,
}


class FakeLA:
    invoked = 0

    @classmethod
    def preflight(cls, plan):
        cls.invoked += 1
        return {
            "source_version": "azent.ir.v0",
            "trigger_type": "manual",
            "step_count": 2,
            "requires_write_approval": False,
            "requires_input_root": False,
            "executes_workflow": False,
            "scope": "synthetic-local-only",
            "steps": [{"id": "private"}],
        }

    @staticmethod
    def audit(run_id):
        return {
            "run_id": run_id,
            "events": [{"details": "private"}],
            "approval_receipts": [{"scope": "private"}],
            "plan_sha256": "private",
        }


class LABridgeTests(unittest.TestCase):
    def test_plan_preview(self):
        result = preflight_la(REQUEST, {}, FakeLA)
        self.assertEqual(result["state"], "PLAN_PREFLIGHT_ONLY")
        self.assertEqual(result["preview"]["step_count"], 2)
        self.assertNotIn("steps", result["preview"])

    def test_missing_approval_never_invokes_la(self):
        FakeLA.invoked = 0
        result = preflight_la({**REQUEST, "owner_approved_metadata": False}, {}, FakeLA)
        self.assertFalse(result["allowed"])
        self.assertEqual(FakeLA.invoked, 0)

    def test_no_installed_runtime(self):
        with self.assertRaises(LABridgeUnavailable):
            preflight_la(REQUEST, {}, None)

    def test_unexpected_scope_rejected(self):
        class InvalidLA(FakeLA):
            @staticmethod
            def preflight(plan):
                return {**FakeLA.preflight(plan), "scope": "remote"}
        with self.assertRaises(LABridgeUnavailable):
            preflight_la(REQUEST, {}, InvalidLA)

    def test_audit_redacted(self):
        result = read_la_audit(REQUEST, "run_1", FakeLA())
        self.assertEqual(result["audit"], {
            "run_id": "run_1", "event_count": 1, "approval_count": 1,
        })

    def test_invalid_run_identifier(self):
        with self.assertRaises(ValueError):
            read_la_audit(REQUEST, "../run", FakeLA())

    def test_execution_flag_rejected(self):
        self.assertFalse(preflight_la({**REQUEST, "execute": True}, {}, FakeLA)["allowed"])


if __name__ == "__main__":
    unittest.main()
