"""Real pinned PUBLIC SOVIA + synthetic LA and DBVORA in one local E2E.

This test is executed only after CI checks out the exact public SOVIA SHA.
HAE LA and DBVORA are injected fakes, never private source imports.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from sovia_la_plan_preflight import assess
from integrations.dbvora_bridge import DBVORABridgeRefused
from integrations.local_metadata_la_chain import run_local_observation_chain
from test_bounded_goal_runtime import FakeMultipleLA


GOAL = "파일 누락 확인 그리고 인계 확인"


def fake_dbvora_p0(path: Path) -> dict:
    # Only a disposable LA-generated database may be inspected.
    if path.name != "business.sqlite":
        raise AssertionError("Unexpected DBVORA target")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
        names = [x[0] for x in conn.execute(
            "SELECT name FROM sqlite_schema WHERE type='table'")]
        rows = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        columns = conn.execute("PRAGMA table_info(records)").fetchall()
    if rows != 2 or "records" not in names:
        raise AssertionError("Synthetic LA row contract mismatch")
    return {
        "contract_version": "p0-01.v1",
        "db_id": "PRIVATE_SYNTHETIC_DB_ID",
        "engine": "sqlite",
        "size_bytes": path.stat().st_size,
        "size_scope": "main_database_file_only_excludes_wal_and_shm",
        "provenance": {
            "tables": "measured_sqlite_catalog",
            "size_bytes": "measured_local_filesystem",
        },
        "tables": [{
            "name": "records",
            "columns": [{"name": col[1]} for col in columns],
            "indexes": [],
            "foreign_keys": [],
        }],
        "relationships": [],
    }


class PublicSoviaToDBVORALocalE2E(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="ugreen-sovia-dbvora-ci-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "README.md").write_text("synthetic only", encoding="utf-8")
        FakeMultipleLA.constructed = 0
        FakeMultipleLA.executed = 0
        self.inspections = []

    def reader(self, path):
        self.inspections.append(path)
        return fake_dbvora_p0(path)

    def flow(self, *, consent=False, approval=None, reader=None, required=None):
        return run_local_observation_chain(
            GOAL, self.root, ["README.md"] if required is None else required,
            FakeMultipleLA, assess,
            approve_local_metadata=consent,
            approve_plan_sha256=approval,
            dbvora_reader=reader,
        )

    def test_real_public_sovia_two_intent_approved_disposable_e2e(self):
        unapproved = self.flow(reader=self.reader)
        self.assertEqual(unapproved["status"], "WAITING_LOCAL_METADATA_APPROVAL")
        self.assertFalse(unapproved["local_inspection_performed"])
        self.assertEqual(self.inspections, [])
        self.assertEqual(FakeMultipleLA.executed, 0)

        pending = self.flow(consent=True, reader=self.reader)
        self.assertEqual(pending["status"], "WAITING_EXACT_LOCAL_PLAN_APPROVAL")
        self.assertEqual(pending["intent_count"], 2)
        self.assertEqual(pending["sovia_finding_count"], 2)
        self.assertEqual(self.inspections, [])
        self.assertEqual(FakeMultipleLA.executed, 0)

        passed = self.flow(
            consent=True, approval=pending["approve_plan_sha256"],
            reader=self.reader,
        )
        self.assertEqual(passed["status"], "PASS")
        self.assertTrue(passed["la_execution_verified"])
        self.assertEqual(passed["synthetic_write_rows"], 2)
        self.assertEqual(passed["approval_receipts"], 1)
        self.assertEqual(passed["replay_duplicate_writes"], 0)
        self.assertTrue(passed["dbvora_metadata_inspected"])
        self.assertEqual(passed["dbvora"]["table_count"], 1)
        self.assertEqual(passed["dbvora"]["column_count"], 3)
        self.assertEqual(FakeMultipleLA.executed, 2)
        self.assertEqual(len(self.inspections), 1)
        self.assertFalse(self.inspections[0].exists())
        self.assertFalse(passed["actual_nas_verified"])
        self.assertFalse(passed["registered_uliya_expert_invoked"])
        self.assertEqual(passed["release_gate"], "HOLD")
        rendered = json.dumps(passed, ensure_ascii=False)
        for secret in ("README.md", str(self.root), GOAL,
                       "PRIVATE_SYNTHETIC_DB_ID"):
            self.assertNotIn(secret, rendered)

    def test_missing_required_item_blocks_la_and_dbvora(self):
        blocked = self.flow(
            consent=True, reader=self.reader, required=["missing-file.txt"]
        )
        self.assertEqual(blocked["status"], "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED")
        self.assertEqual(FakeMultipleLA.executed, 0)
        self.assertEqual(self.inspections, [])

    def test_wrong_plan_hash_never_calls_la_or_dbvora(self):
        self.flow(consent=True, reader=self.reader)
        with self.assertRaisesRegex(ValueError, "LOCAL_PLAN_APPROVAL_HASH_MISMATCH"):
            self.flow(consent=True, approval="0" * 64, reader=self.reader)
        self.assertEqual(FakeMultipleLA.executed, 0)
        self.assertEqual(self.inspections, [])

    def test_corrupt_dbvora_provenance_refused_not_pass(self):
        pending = self.flow(consent=True)
        def forged_reader(path):
            result = fake_dbvora_p0(path)
            result["provenance"]["tables"] = "guessed"
            return result
        with self.assertRaisesRegex(
                DBVORABridgeRefused, "DBVORA_PROVENANCE_UNVERIFIED"):
            self.flow(
                consent=True, approval=pending["approve_plan_sha256"],
                reader=forged_reader,
            )


if __name__ == "__main__":
    unittest.main()
