"""G133 opt-in durable SQLite replay and redacted readback; synthetic-only."""
from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_persistent_qa import run_persistent

GOAL = "필수 파일 확인해줘"


class PersistentQATests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "session.sqlite"

    def run_qa(self, mode="new", *, goal=GOAL, run_id="run_g133stable01", approve=True,
               inject=False):
        return run_persistent(goal, run_id, self.path, mode=mode,
                              approve_local_write=approve, inject_test_fault=inject)

    def test_consent_denial_creates_no_file(self):
        result = self.run_qa(approve=False)
        self.assertEqual(result["status"], "WAITING_EXPLICIT_LOCAL_DB_APPROVAL")
        self.assertFalse(self.path.exists())

    def test_durable_readback_and_duplicate_across_connections(self):
        first = self.run_qa()
        self.assertEqual(first["status"], "PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        self.assertEqual(first["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertTrue(self.path.is_file())
        self.assertFalse(first["nas_verified"])
        before = self.path.stat().st_size
        with patch("flowpilot_repair_ledger.run_council", side_effect=AssertionError("replayed")):
            duplicate = self.run_qa("append")
        self.assertEqual(duplicate["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(duplicate["database_modified"])
        self.assertEqual(self.path.stat().st_size, before)
        read = self.run_qa("read", approve=False, goal=None)
        self.assertEqual(read["status"], "READ_ONLY_LOCAL_EVIDENCE")
        self.assertEqual(read["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertFalse(read["database_modified"])

    def test_same_id_other_goal_is_collision(self):
        self.run_qa()
        with patch("flowpilot_repair_ledger.run_council", side_effect=AssertionError("replayed")):
            result = self.run_qa("append", goal="check required files")
        self.assertEqual(result["status"], "RUN_ID_GOAL_CONFLICT")
        self.assertFalse(result["synthetic_fixture_executed"])

    def test_local_ledger_tampering_is_not_accepted(self):
        self.run_qa()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE fp119_events SET detail='{}' WHERE run_id=? AND seq=2",
                       ("run_g133stable01",))
            db.commit()
        result = self.run_qa("read", approve=False, goal=None)
        self.assertEqual(result["status"], "LOCAL_EVIDENCE_INVALID")
        with patch("flowpilot_repair_ledger.run_council", side_effect=AssertionError("replayed")):
            duplicate = self.run_qa("append")
        self.assertEqual(duplicate["status"], "PRIOR_LOCAL_EVIDENCE_INVALID")

    def test_new_mode_will_never_overwrite_existing_file(self):
        self.path.write_bytes(b"owner-private-original-do-not-replace")
        before = self.path.read_bytes()
        result = self.run_qa()
        self.assertEqual(result["status"], "LOCAL_DB_REFUSED")
        self.assertEqual(self.path.read_bytes(), before)

    def test_cannot_append_unrecognized_existing_sqlite(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE owner_data (message TEXT)")
            db.execute("INSERT INTO owner_data VALUES('must remain')")
            db.commit()
        result = self.run_qa("append")
        self.assertEqual(result["status"], "LOCAL_DB_REFUSED")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT message FROM owner_data").fetchone()[0],
                             "must remain")
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='fp119_runs'").fetchone())

    def test_unknown_run_no_mutation(self):
        self.run_qa()
        before = self.path.read_bytes()
        result = self.run_qa("read", run_id="run_g133missing22", approve=False, goal=None)
        self.assertEqual(result["status"], "NO_RUN_RECORD")
        self.assertEqual(before, self.path.read_bytes())

    def test_unsupported_goal_never_ran_fixture(self):
        value = self.run_qa(goal="delete my NAS files")
        self.assertEqual(value["status"], "NOT_VERIFIED_OR_UNSUPPORTED")
        self.assertFalse(value["database_modified"])
        self.assertFalse(value["synthetic_fixture_executed"])
        self.assertTrue(self.path.exists())  # Only explicit new DB creation.

    def test_new_creation_accepts_fault_and_records_local_chain(self):
        value = self.run_qa(inject=True)
        self.assertEqual(value["status"], "PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        self.assertEqual(value["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertFalse(value["actual_docker_executed"])

    def test_invalid_run_id_rejected_pre_io(self):
        result = self.run_qa(run_id="../../customer")
        self.assertEqual(result["status"], "INVALID_RUN_ID")
        self.assertFalse(self.path.exists())

    def test_relative_or_wrong_extension_rejected_pre_io(self):
        for target in (Path("relative.sqlite"), Path(self.path.parent / "bad.txt")):
            with self.subTest(target=target):
                result = run_persistent(GOAL, "run_g133stable01", target,
                                        mode="new", approve_local_write=True)
                self.assertEqual(result["status"], "LOCAL_DB_REFUSED")
                self.assertFalse(target.exists())

    def test_symlinked_db_rejected_without_impact(self):
        linked = self.path.with_name("alias.sqlite")
        self.path.write_bytes(b"private-owner-bytes")
        try:
            linked.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable in this Windows runner")
        self.assertEqual(run_persistent(GOAL, "run_g133stable01", linked,
                                        mode="append", approve_local_write=True)["status"],
                         "LOCAL_DB_REFUSED")
        self.assertEqual(self.path.read_bytes(), b"private-owner-bytes")

    def test_cli_persistent_replay_across_processes(self):
        base = [sys.executable, str(ROOT / "tools" / "flowpilot_persistent_qa.py"),
                "--db", str(self.path), "--run-id", "run_g133proc002"]
        created = subprocess.run(base + ["--mode", "new", "--goal", GOAL,
                                         "--approve-local-write"],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(json.loads(created.stdout)["status"],
                         "PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        reused = subprocess.run(base + ["--mode", "append", "--goal", GOAL,
                                        "--approve-local-write"],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(reused.returncode, 2)
        self.assertEqual(json.loads(reused.stdout)["status"], "DUPLICATE_BLOCKED")
        read = subprocess.run(base + ["--mode", "read"],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(read.returncode, 0)
        self.assertEqual(json.loads(read.stdout)["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertNotIn(str(self.path), read.stdout)
        self.assertNotIn(GOAL, read.stdout)

    def test_declined_cli_has_no_side_effect(self):
        args = [sys.executable, str(ROOT / "tools" / "flowpilot_persistent_qa.py"),
                "--db", str(self.path), "--run-id", "run_g133declined1",
                "--mode", "new", "--goal", GOAL]
        process = subprocess.run(args, capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(json.loads(process.stdout)["status"],
                         "WAITING_EXPLICIT_LOCAL_DB_APPROVAL")
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
