"""Verify the offline LA smoke verifier itself using a synthetic fake runtime.

These tests do not replace real HAE Lightning Azent execution; real HAE
source must be installed and separately verified for runtime compatibility.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from tools.verify_la_runtime_bridge import verify


class FakeApprovalRequired(Exception):
    pass


class SyntheticLA:
    """A narrow stand-in that exercises actual disposable SQLite persistence."""

    def __init__(self, state_path, business_path):
        self.state_path = Path(state_path)
        self.business_path = Path(business_path)
        self.history = {}

    @staticmethod
    def capabilities():
        return {
            "api_version": "azent.api.v0", "scope": "synthetic-local-only",
            "external_connectors": [], "implemented_operations": ["literal", "sqlite_put"],
        }

    @staticmethod
    def preflight(plan):
        operations = [{"id": s["id"], "op": s["op"]} for s in plan["steps"]]
        return {
            "source_version": plan["version"], "scope": "synthetic-local-only",
            "executes_workflow": False, "trigger_type": "manual",
            "step_count": len(operations), "steps": operations,
            "requires_write_approval": any(s["op"] == "sqlite_put" for s in operations),
            "requires_input_root": False,
        }

    def execute(self, plan, run_id, *, approve_writes=False):
        has_write = any(s["op"] == "sqlite_put" for s in plan["steps"])
        if has_write and not approve_writes:
            raise FakeApprovalRequired("explicit write approval required")
        if run_id in self.history:
            self.history[run_id]["events"].append({"event_type": "run_replayed"})
            return self.history[run_id]["result"]
        with closing(sqlite3.connect(self.state_path)) as state:
            state.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY)")
            state.execute("INSERT INTO runs VALUES (?)", (run_id,))
        with closing(sqlite3.connect(self.business_path)) as business:
            business.execute("CREATE TABLE IF NOT EXISTS records (run_id TEXT, step_id TEXT)")
            if has_write:
                business.execute("INSERT INTO records VALUES (?, ?)", (run_id, "store"))
                business.commit()
        self.history[run_id] = {
            "result": {"synthetic": True},
            "events": [{"event_type": "run_started"}, {"event_type": "run_completed"}],
            "approval_receipts": [{"method": "explicit"}] if has_write else [],
        }
        return self.history[run_id]["result"]

    def audit(self, run_id):
        return {"run_id": run_id, **self.history[run_id]}

    def status(self, run_id):
        return {"status": "completed" if run_id in self.history else "unavailable"}


class VerifyLARuntimeHarnessTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.source = Path(folder.name) / "trusted-LA"
        (self.source / "lightning_azent").mkdir(parents=True)
        (self.source / "lightning_azent" / "runtime.py").write_text(
            "# fake external package fixture, NOT real Lightning Azent", encoding="utf-8"
        )

    def run_with(self, implementation):
        module = types.ModuleType("lightning_azent")
        module.LAExecutor = implementation
        module.ApprovalRequired = FakeApprovalRequired
        with patch.dict(sys.modules, {"lightning_azent": module}):
            return verify(self.source)

    def test_synthetic_stub_smoke_harness_passes(self):
        result = self.run_with(SyntheticLA)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["approved_synthetic_write_rows"], 1)
        self.assertEqual(result["replay_duplicate_writes"], 0)
        self.assertFalse(result["denied_write_created_db"])
        self.assertEqual(result["nas"], "NOT_TESTED")

    def test_missing_explicit_write_guard_fails_closed(self):
        class UnsafeLA(SyntheticLA):
            def execute(self, plan, run_id, *, approve_writes=False):
                if run_id == "ugreen_denied":
                    return {"improperly_approved": True}
                return super().execute(plan, run_id, approve_writes=approve_writes)
        with self.assertRaisesRegex(RuntimeError, "without approval"):
            self.run_with(UnsafeLA)

    def test_synthetic_replay_double_write_fails_closed(self):
        class UnsafeReplayLA(SyntheticLA):
            def execute(self, plan, run_id, *, approve_writes=False):
                replaying = run_id in self.history and run_id == "ugreen_approved"
                result = super().execute(plan, run_id, approve_writes=approve_writes)
                if replaying:
                    with closing(sqlite3.connect(self.business_path)) as con:
                        con.execute("INSERT INTO records VALUES (?, ?)", (run_id, "store"))
                        con.commit()
                return result
        with self.assertRaisesRegex(RuntimeError, "duplicated"):
            self.run_with(UnsafeReplayLA)

    def test_mismatched_api_version_fails_closed(self):
        class WrongVersionLA(SyntheticLA):
            @staticmethod
            def capabilities():
                return {**SyntheticLA.capabilities(), "api_version": "azent.api.v99"}
        with self.assertRaisesRegex(RuntimeError, "API version mismatch"):
            self.run_with(WrongVersionLA)


if __name__ == "__main__":
    unittest.main()
