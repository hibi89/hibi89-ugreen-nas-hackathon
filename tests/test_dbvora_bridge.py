"""Optional DBVORA P0 synthetic schema integration; no private source imported."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from integrations.dbvora_bridge import (
    DBVORABridgeRefused, inspect_disposable_la_ledger,
    summarize_synthetic_dbvora_inventory,
)
from integrations.local_metadata_la_chain import run_local_observation_chain
from test_bounded_goal_runtime import FakeMultipleLA, fake_assess


def synthetic_inventory(path: Path) -> dict:
    # Simulated P0 response, not an invocation of the private DBVORA product.
    assert path.name == "business.sqlite" and path.is_file()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE name='records'").fetchone()
    return {
        "contract_version": "p0-01.v1", "engine": "sqlite",
        "size_bytes": path.stat().st_size,
        "size_scope": "main_database_file_only_excludes_wal_and_shm",
        "db_id": "SECRET_SYNTHETIC_IDENTIFIER",
        "provenance": {"tables": "measured_sqlite_catalog",
                       "size_bytes": "measured_local_filesystem"},
        "tables": [{"name": "records", "columns": [
            {"name": "SECRET_COLUMN", "type": "TEXT"}],
            "indexes": [], "foreign_keys": []}],
        "relationships": [],
    }


class DBVORASyntheticBridgeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ugreen-dbvora-synthetic-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / "README.md").write_text("disposable", encoding="utf-8")
        FakeMultipleLA.constructed = 0
        FakeMultipleLA.executed = 0
        self.called = []

    def reader(self, path):
        self.called.append(path)
        return synthetic_inventory(path)

    def chain(self, *, metadata=False, approval=None, reader=None):
        return run_local_observation_chain(
            "파일 누락 확인", self.root, ["README.md"],
            FakeMultipleLA, fake_assess,
            approve_local_metadata=metadata, approve_plan_sha256=approval,
            dbvora_reader=reader,
        )

    def test_no_metadata_consent_never_invokes_dbvora(self):
        row = self.chain(reader=self.reader)
        self.assertEqual(row["status"], "WAITING_LOCAL_METADATA_APPROVAL")
        self.assertEqual(self.called, [])
        self.assertFalse(row["dbvora_metadata_inspected"])

    def test_local_metadata_only_does_not_invoke_dbvora(self):
        row = self.chain(metadata=True, reader=self.reader)
        self.assertEqual(row["status"], "WAITING_EXACT_LOCAL_PLAN_APPROVAL")
        self.assertEqual(self.called, [])
        self.assertEqual(FakeMultipleLA.executed, 0)

    def test_after_exact_approval_only_disposable_sqlite_is_inspected(self):
        preview = self.chain(metadata=True, reader=self.reader)
        proved = self.chain(
            metadata=True, approval=preview["approve_plan_sha256"],
            reader=self.reader,
        )
        self.assertEqual(proved["status"], "PASS")
        self.assertEqual(proved["synthetic_write_rows"], 1)
        self.assertEqual(proved["dbvora"]["status"], "SYNTHETIC_SCHEMA_METADATA_ONLY")
        self.assertEqual(proved["dbvora"]["table_count"], 1)
        self.assertFalse(proved["dbvora"]["source_implementation_independently_verified"])
        self.assertEqual(len(self.called), 1)
        self.assertEqual(self.called[0].name, "business.sqlite")
        self.assertFalse(self.called[0].exists())
        returned = json.dumps(proved)
        for secret in ("SECRET_COLUMN", "SECRET_SYNTHETIC_IDENTIFIER",
                       "README.md", str(self.root)):
            self.assertNotIn(secret, returned)
        self.assertFalse(proved["actual_nas_verified"])
        self.assertEqual(proved["release_gate"], "HOLD")

    def test_mismatched_approval_never_invokes_dbvora(self):
        preview = self.chain(metadata=True, reader=self.reader)
        with self.assertRaisesRegex(ValueError, "APPROVAL_HASH_MISMATCH"):
            self.chain(metadata=True, approval="0" * 64, reader=self.reader)
        self.assertEqual(self.called, [])

    def test_no_opt_in_reader_preserves_existing_chain(self):
        preview = self.chain(metadata=True)
        proved = self.chain(metadata=True, approval=preview["approve_plan_sha256"])
        self.assertEqual(proved["status"], "PASS")
        self.assertFalse(proved["dbvora_metadata_inspected"])

    def test_contract_refuses_schema_and_provenance_forgery(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "business.sqlite"
            with sqlite3.connect(file) as db:
                db.execute("CREATE TABLE records (id INTEGER)")
            good = synthetic_inventory(file)
            self.assertEqual(summarize_synthetic_dbvora_inventory(good)["table_count"], 1)
            for patch in (
                {"engine": "postgres"}, {"contract_version": "unknown"},
                {"tables": [{"name": "customers", "columns": [],
                             "foreign_keys": [], "indexes": []}]},
                {"provenance": {"tables": "guessed", "size_bytes": "estimated"}},
                {"size_bytes": True},
            ):
                bad = {**good, **patch}
                with self.assertRaises(DBVORABridgeRefused):
                    summarize_synthetic_dbvora_inventory(bad)

    def test_injected_error_never_leaks_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "business.sqlite"
            path.touch()
            def broken_reader(_path):
                raise RuntimeError("PRIVATE_USER_PATH_OR_SQL_SECRET")
            with self.assertRaisesRegex(
                    DBVORABridgeRefused, "^DBVORA_SYNTHETIC_INSPECTION_FAILED$") as cm:
                inspect_disposable_la_ledger(path, broken_reader)
            self.assertNotIn("PRIVATE_USER_PATH", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
