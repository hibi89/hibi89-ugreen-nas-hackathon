"""Synthetic adapter tests: fake LA facade, actual disposable SQLite files."""
from __future__ import annotations

import csv
from hashlib import sha256
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_la_synthetic_import import APPROVAL, LA_PLAN, run_demo


class FakeLA:
    calls = 0
    incorrect_rows = False
    corrupted_status = False
    corrupted_receipt = False
    execute_fails = False
    corrupted_payload = False
    corrupted_source_sha = False
    @staticmethod
    def capabilities():
        return {
            "api_version": "azent.api.v0", "native_ir_version": "azent.ir.v0",
            "scope": "synthetic-local-only", "external_connectors": [],
            "implemented_operations": ["csv_read", "sqlite_import_csv", "literal"],
        }

    @staticmethod
    def preflight(plan):
        assert plan == LA_PLAN
        return {"source_version": "azent.ir.v0", "runtime_version": "axflow.ir.v0",
                "step_count": 2, "requires_write_approval": True,
                "requires_input_root": True, "executes_workflow": False,
                "scope": "synthetic-local-only"}

    def __init__(self, state, business, *, input_root):
        self.state, self.business, self.root = Path(state), Path(business), Path(input_root)

    def execute(self, plan, run_id, *, approve_writes=False):
        type(self).calls += 1
        if type(self).execute_fails:
            raise RuntimeError("private-path/must-not-be-echoed")
        assert plan == LA_PLAN and run_id == "FlowPilotSyntheticImport" and approve_writes is True
        with (self.root / "sales.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.reader(stream))
        assert rows == [["customer", "amount"], ["alice", "1.25"], ["bob", "2.00"]]
        digest = sha256((self.root / "sales.csv").read_bytes()).hexdigest()
        with sqlite3.connect(self.business) as db:
            db.execute("CREATE TABLE IF NOT EXISTS csv_records("
                       "run_id TEXT, import_step_id TEXT, source_sha256 TEXT, "
                       "row_number INTEGER, payload_json TEXT, "
                       "PRIMARY KEY(run_id,import_step_id,row_number))")
            for i, (customer, amount) in enumerate(rows[1:], start=1):
                payload = json.dumps({"customer": customer, "amount": amount}, sort_keys=True)
                db.execute("INSERT OR IGNORE INTO csv_records VALUES (?,?,?,?,?)",
                           (run_id, "imported", digest, i, payload))
            if type(self).incorrect_rows:
                db.execute("DELETE FROM csv_records WHERE row_number=2")
            if type(self).corrupted_payload:
                db.execute("UPDATE csv_records SET payload_json=? WHERE row_number=1",
                           ('{"customer":"charlie","amount":"1.25"}',))
            if type(self).corrupted_source_sha:
                db.execute("UPDATE csv_records SET source_sha256=? WHERE row_number=1",
                           ("f" * 64,))
        return {"status": "completed"}

    def status(self, _run_id):
        return {"status": "failed" if type(self).corrupted_status else "completed"}

    def audit(self, _run_id):
        return {"run_id": "FlowPilotSyntheticImport",
                "events": [{"type": "synthetic"}],
                "approval_receipts": [{"scope": "synthetic-write"}]}

    def verify_receipts(self, _plan, _run_id):
        return {"verified": not type(self).corrupted_receipt}


def loader(_name):
    assert _name == "lightning_azent"
    return SimpleNamespace(LAExecutor=FakeLA)


class RealSQLiteAdapterBoundaryTests(unittest.TestCase):
    def setUp(self):
        FakeLA.calls = 0
        FakeLA.incorrect_rows = FakeLA.corrupted_status = False
        FakeLA.corrupted_receipt = FakeLA.execute_fails = False
        FakeLA.corrupted_payload = FakeLA.corrupted_source_sha = False

    def test_preview_never_imports_or_creates_workspace(self):
        def unexpected(*_a, **_kw):
            raise AssertionError("no workspace or imports allowed before approval")
        result = run_demo(loader=unexpected, workspace=unexpected)
        self.assertEqual(result["status"], "WAITING_EXECUTION_APPROVAL")
        self.assertFalse(result["la_executor_called"])

    def test_rejection_cannot_create_workspace(self):
        def unexpected(*_a, **_kw):
            raise AssertionError("rejected request must be side-effect-free")
        self.assertEqual(run_demo(approval="REJECT", loader=unexpected,
                                  workspace=unexpected)["status"], "DECLINED")

    def test_invalid_consent_types_and_values_are_refused(self):
        for consent in (True, 1, "APPROVE", "APPROVE_EXECUTION", {}, [], ""):
            with self.subTest(consent=consent):
                result = run_demo(approval=consent, loader=lambda _: 1)
                self.assertEqual(result["status"], "REFUSED_INVALID_APPROVAL")
                self.assertFalse(result["la_executor_called"])

    def test_absent_optional_la_is_blocked_without_write(self):
        def missing(_name):
            raise ModuleNotFoundError("no package")
        result = run_demo(approval=APPROVAL, loader=missing)
        self.assertEqual(result["status"], "BLOCKED_RUNTIME_UNAVAILABLE")
        self.assertFalse(result["la_executor_called"])

    def test_actual_local_sqlite_and_replay_are_verified_with_fake_facade(self):
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "SYNTHETIC_LA_SQLITE_VERIFIED")
        self.assertEqual(result["persisted_rows"], 2)
        self.assertTrue(result["source_hash_preserved"])
        self.assertTrue(result["metadata_audit_observed"])
        self.assertTrue(result["replay_verified"])
        self.assertEqual(FakeLA.calls, 2)
        self.assertFalse(result["uliya_or_nas_called"])
        self.assertFalse(result["hae_application_called"])

    def test_rows_missing_detected_despite_completed_receipt(self):
        FakeLA.incorrect_rows = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")
        self.assertFalse(result["la_execution_verified"])

    def test_same_row_count_wrong_payload_is_rejected(self):
        FakeLA.corrupted_payload = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")
        self.assertFalse(result["la_execution_verified"])

    def test_source_sha_mismatch_is_rejected_even_if_rows_match(self):
        FakeLA.corrupted_source_sha = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")
        self.assertFalse(result["source_hash_preserved"] is False
                         and result["la_execution_verified"])

    def test_failed_run_status_is_denied(self):
        FakeLA.corrupted_status = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")
        self.assertEqual(result["persisted_rows"], 0)

    def test_deleted_or_invalid_receipts_are_denied(self):
        FakeLA.corrupted_receipt = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")

    def test_runtime_exception_is_sanitized(self):
        FakeLA.execute_fails = True
        result = run_demo(approval=APPROVAL, loader=loader)
        self.assertEqual(result["status"], "BLOCKED_LA_EXECUTION_OR_AUDIT")
        self.assertNotIn("private-path", json.dumps(result))

    def test_contract_refuses_unsupported_api_version(self):
        class Unsupported(FakeLA):
            @staticmethod
            def capabilities():
                d = FakeLA.capabilities()
                d["api_version"] = "azent.api.v2"
                return d
        result = run_demo(approval=APPROVAL,
                          loader=lambda _: SimpleNamespace(LAExecutor=Unsupported))
        self.assertEqual(result["status"], "BLOCKED_RUNTIME_CONTRACT")
        self.assertFalse(result["la_executor_called"])

    def test_contract_refuses_unexpected_extra_network_connectors(self):
        class Network(FakeLA):
            @staticmethod
            def capabilities():
                d = FakeLA.capabilities()
                d["external_connectors"] = ["http"]
                return d
        result = run_demo(approval=APPROVAL,
                          loader=lambda _: SimpleNamespace(LAExecutor=Network))
        self.assertEqual(result["status"], "BLOCKED_RUNTIME_CONTRACT")

    def test_bad_preflight_prevents_execute(self):
        class Unsafe(FakeLA):
            @staticmethod
            def preflight(plan):
                d = FakeLA.preflight(plan)
                d["requires_write_approval"] = False
                return d
        result = run_demo(approval=APPROVAL,
                          loader=lambda _: SimpleNamespace(LAExecutor=Unsafe))
        self.assertEqual(result["status"], "BLOCKED_RUNTIME_CONTRACT")
        self.assertEqual(Unsafe.calls, 0)


if __name__ == "__main__":
    unittest.main()
