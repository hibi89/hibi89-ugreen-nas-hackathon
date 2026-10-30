"""Offline capability-handshake tests: no NAS, LA execution or owner files."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from flowpilot_la_runtime_probe import PROBE_PLAN, probe_installed_la
from flowpilot_la_capabilities import FLOWPILOT_LOCAL_TYPES


LEGACY_OPS = [
    "literal", "field", "map", "condition", "branch", "csv_read",
    "csv_normalize", "csv_filter", "sqlite_put", "sqlite_import_csv",
    "sqlite_get",
]


def stub(*, operations=None, api="azent.api.v0", connectors=None,
         preview_override=None):
    calls = {"capabilities": 0, "preflight": 0, "execute": 0}
    class FakeExecutor:
        @staticmethod
        def capabilities():
            calls["capabilities"] += 1
            return {
                "api_version": api,
                "native_ir_version": "azent.ir.v0",
                "legacy_ir_version": "axflow.ir.v0",
                "scope": "synthetic-local-only",
                "external_connectors": [] if connectors is None else connectors,
                "implemented_operations": copy.deepcopy(
                    LEGACY_OPS if operations is None else operations),
            }

        @staticmethod
        def preflight(plan):
            calls["preflight"] += 1
            assert plan == PROBE_PLAN
            return preview_override if preview_override is not None else {
                "source_version": "azent.ir.v0",
                "runtime_version": "axflow.ir.v0",
                "step_count": 1,
                "requires_write_approval": False,
                "requires_input_root": False,
                "executes_workflow": False,
                "scope": "synthetic-local-only",
            }

        @staticmethod
        def execute(*_args, **_kwargs):
            calls["execute"] += 1
            raise AssertionError("The probe must never execute an engine")

    return SimpleNamespace(LAExecutor=FakeExecutor), calls


class InstalledRuntimeProbeTests(unittest.TestCase):
    def test_not_installed_is_blocked_without_execution(self):
        def absent(_name):
            raise ModuleNotFoundError("No installed LA package")
        response = probe_installed_la(loader=absent)
        self.assertEqual(response["status"], "BLOCKED_RUNTIME_UNAVAILABLE")
        self.assertFalse(response["installed_la_module_imported"])
        self.assertFalse(response["execution_allowed"])

    def test_real_v0_capabilities_are_insufficient_for_flowpilot_csv(self):
        package, calls = stub()
        response = probe_installed_la(loader=lambda _: package)
        self.assertEqual(response["status"], "BLOCKED_MISSING_OPERATIONS")
        self.assertEqual(
            response["missing_operations"],
            ["csv_write_new", "decimal_group_sum", "sqlite_audit"],
        )
        self.assertTrue(response["installed_la_preflight_called"])
        self.assertEqual(calls, {"capabilities": 1, "preflight": 1, "execute": 0})
        self.assertFalse(response["actual_la_workflow_executed"])
        self.assertFalse(response["execution_allowed"])

    def test_declaring_all_nodes_does_not_prove_runtime_execution(self):
        package, calls = stub(operations=LEGACY_OPS + sorted(FLOWPILOT_LOCAL_TYPES))
        # Duplicated csv_read must be rejected rather than silently deduped.
        response = probe_installed_la(loader=lambda _: package)
        self.assertEqual(response["status"], "BLOCKED_RUNTIME_CONTRACT")
        self.assertEqual(calls["execute"], 0)

        package, calls = stub(
            operations=sorted(set(LEGACY_OPS).union(FLOWPILOT_LOCAL_TYPES)))
        response = probe_installed_la(loader=lambda _: package)
        self.assertEqual(response["status"], "PREFLIGHT_COMPATIBLE_NOT_EXECUTED")
        self.assertFalse(response["execution_allowed"])
        self.assertFalse(response["actual_la_workflow_executed"])
        self.assertEqual(calls, {"capabilities": 1, "preflight": 1, "execute": 0})

    def test_wrong_version_or_external_connectors_fail_closed(self):
        for options in ({"api": "azent.api.v9"},
                        {"connectors": ["http"]},
                        {"operations": ["csv_read", {"unsafe": True}]}):
            with self.subTest(options=options):
                package, calls = stub(**options)
                response = probe_installed_la(loader=lambda _: package)
                self.assertEqual(response["status"], "BLOCKED_RUNTIME_CONTRACT")
                self.assertEqual(calls["preflight"], 0)
                self.assertEqual(calls["execute"], 0)

    def test_bad_preflight_refuses_instead_of_faking_integration(self):
        package, calls = stub(
            preview_override={"source_version": "azent.ir.v0",
                              "executes_workflow": True})
        response = probe_installed_la(loader=lambda _: package)
        self.assertEqual(response["status"], "BLOCKED_RUNTIME_CONTRACT")
        self.assertEqual(calls, {"capabilities": 1, "preflight": 1, "execute": 0})
        self.assertFalse(response["execution_allowed"])

    def test_import_errors_are_sanitized(self):
        def broken(_name):
            raise RuntimeError("/private/owner-token-is-not-a-public-error")
        response = probe_installed_la(loader=broken)
        self.assertEqual(response["status"], "BLOCKED_RUNTIME_CONTRACT")
        self.assertNotIn("owner-token", str(response))
        self.assertFalse(response["execution_allowed"])

    def test_no_private_paths_secrets_or_false_nas_claims(self):
        package, _ = stub()
        result = probe_installed_la(loader=lambda _: package)
        self.assertFalse(result["hae_application_called"])
        self.assertFalse(result["uliya_or_nas_called"])
        self.assertFalse(result["sovia_called"])
        self.assertFalse(result["dbvora_called"])
        self.assertEqual(result["release_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
