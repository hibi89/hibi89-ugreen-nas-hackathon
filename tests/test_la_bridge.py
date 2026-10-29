import unittest

from integrations.la_bridge import LABridgeUnavailable, preflight_la, read_la_audit, inspect_la_capabilities

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



class LocalOnlyLA:
    calls = 0

    @classmethod
    def capabilities(cls):
        cls.calls += 1
        return {
            "api_version": "azent.api.v0",
            "scope": "synthetic-local-only",
            "external_connectors": [],
            "implemented_operations": ["literal", "csv_read", "sqlite_get"],
        }


class LACapabilityTests(unittest.TestCase):
    def test_local_capabilities_never_imply_nas(self):
        result = inspect_la_capabilities(REQUEST, LocalOnlyLA)
        self.assertEqual(result["state"], "LOCAL_PLAN_ONLY")
        self.assertFalse(result["can_read_nas"])
        self.assertFalse(result["can_delegate_uliya_experts"])
        self.assertEqual(result["nas_state"], "NOT_CHECKED")

    def test_gate_before_capability_call(self):
        LocalOnlyLA.calls = 0
        result = inspect_la_capabilities(
            {**REQUEST, "runtime_permissions_verified": False}, LocalOnlyLA
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(LocalOnlyLA.calls, 0)

    def test_missing_capability_method(self):
        with self.assertRaises(LABridgeUnavailable):
            inspect_la_capabilities(REQUEST, object())

    def test_unrecognized_api_version(self):
        class FutureLA(LocalOnlyLA):
            @staticmethod
            def capabilities():
                return {**LocalOnlyLA.capabilities(), "api_version": "azent.api.v99"}
        with self.assertRaises(LABridgeUnavailable):
            inspect_la_capabilities(REQUEST, FutureLA)

    def test_external_connector_requires_review(self):
        class ConnectorLA(LocalOnlyLA):
            @staticmethod
            def capabilities():
                return {**LocalOnlyLA.capabilities(), "external_connectors": ["nas"]}
        with self.assertRaises(LABridgeUnavailable):
            inspect_la_capabilities(REQUEST, ConnectorLA)

    def test_invalid_supported_operations(self):
        class CorruptLA(LocalOnlyLA):
            @staticmethod
            def capabilities():
                return {**LocalOnlyLA.capabilities(), "implemented_operations": [None]}
        with self.assertRaises(LABridgeUnavailable):
            inspect_la_capabilities(REQUEST, CorruptLA)


if __name__ == "__main__":
    unittest.main()
