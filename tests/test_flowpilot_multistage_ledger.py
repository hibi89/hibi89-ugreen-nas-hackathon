"""G144: real disposable OS multi-stage, replay-safe SQLite persistence.

Every filesystem is a TemporaryDirectory; no Uliya, vendor SDK, customer NAS
or external API is touched. Windows SQLite handles are always closed.
"""
from __future__ import annotations
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_multistage_ledger import run_recorded_local_workflow as run

class G144MultiStageLedgerTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.temp = Path(t.name)
        self.folder = self.temp / "owner-PRIVATE-AREA"
        self.folder.mkdir()
        (self.folder / "README.md").write_bytes(b"OWNER-CONTENT-NOT-TO-READ")
        (self.folder / "final.pdf").write_bytes(b"version-one")
        (self.folder / "final_v2.pdf").write_bytes(b"version-two")
        self.db = self.temp / "record.sqlite"
        self.run_id = "run_g144abcdef12"
        self.instructions = "파일 확인: README.md; 파일 확인: final.pdf"

    def record(self, *, mode="new", instructions=None, root=None,
               read=True, write=True, run_id=None):
        return run(self.db, run_id or self.run_id, mode=mode,
                   instructions=self.instructions if instructions is None else instructions,
                   root=self.folder if root is None else root,
                   approve_local_metadata=read, approve_local_db_write=write)

    def get(self):
        return run(self.db, self.run_id, mode="read")

    def test_real_two_step_local_metadata_persisted_and_read_back(self):
        before = (self.folder/"README.md").read_bytes()
        row = self.record()
        self.assertEqual(row["status"], "LOCAL_WORKFLOW_REVIEW_STORED")
        self.assertEqual((row["planned_steps"], row["executed_steps"]), (2, 2))
        self.assertEqual(row["audit_result"], "NEEDS_REVIEW")
        saved = self.get()
        self.assertEqual(saved["status"], "READ_ONLY_LOCAL_WORKFLOW_EVIDENCE")
        self.assertEqual([s["items"][0]["state"] for s in saved["steps"]],
                         ["PRESENT", "PRESENT"])
        self.assertFalse(saved["nas_verified"])
        self.assertEqual((self.folder/"README.md").read_bytes(), before)
        for sensitive in ("README.md", "final.pdf", str(self.folder),
                          "OWNER-CONTENT-NOT-TO-READ", "파일 확인"):
            self.assertNotIn(sensitive, self.db.read_bytes().decode("latin1"))
            self.assertNotIn(sensitive, json.dumps(row))
            self.assertNotIn(sensitive, json.dumps(saved))
        self.assertEqual(saved["release_gate"], "HOLD")

    def test_missing_first_step_blocks_later_and_is_durable(self):
        row = self.record(instructions="파일 확인: absent.txt; 파일 확인: README.md")
        self.assertEqual(row["status"], "LOCAL_WORKFLOW_BLOCKED_STORED")
        self.assertEqual(row["executed_steps"], 1)
        saved = self.get()
        self.assertEqual(saved["audit_result"], "BLOCKED")
        self.assertEqual(saved["steps"][0]["items"][0]["state"], "MISSING")
        self.assertEqual(saved["executed_steps"], 1)

    def test_version_conflict_stops_before_second_stage_and_persists(self):
        cmd = "버전 비교: final.pdf => final_v2.pdf; 파일 확인: README.md"
        row = self.record(instructions=cmd)
        self.assertEqual(row["status"], "LOCAL_WORKFLOW_REVIEW_STORED")
        self.assertEqual(row["executed_steps"], 1)
        self.assertEqual(self.get()["steps"][0]["items"][0]["state"], "VERSION_REVIEW")

    def test_missing_either_consent_performs_no_db_or_local_io(self):
        for read, write in ((False, True), (True, False), (False, False)):
            with self.subTest(read=read, write=write), \
                    patch("flowpilot_multistage_ledger.run_workflow",
                          side_effect=AssertionError("preflight touched")):
                row = self.record(read=read, write=write)
            self.assertEqual(row["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
            self.assertFalse(self.db.exists())

    def test_duplicate_run_same_scope_does_not_rescan(self):
        self.record()
        before = self.db.read_bytes()
        def guard(root, recipe, *, metadata_consent=False):
            if metadata_consent:
                raise AssertionError("REPLAYED_OWNER_READ")
            from flowpilot_local_workflow import run_workflow
            return run_workflow(root, recipe, metadata_consent=False)
        with patch("flowpilot_multistage_ledger.run_workflow", side_effect=guard):
            row = self.record(mode="append")
        self.assertEqual(row["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(row["database_modified"])
        self.assertEqual(self.db.read_bytes(), before)

    def test_same_id_alternate_scope_denied_without_rescan(self):
        self.record()
        row = self.record(mode="append",
                          instructions="파일 확인: final.pdf")
        self.assertEqual(row["status"], "RUN_ID_SCOPE_CONFLICT")
        self.assertFalse(row["database_modified"])

    def test_modified_sqlite_row_detected_on_read(self):
        self.record()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp144_multistage_runs SET state='BLOCKED'")
            db.commit()
        row = self.get()
        self.assertEqual(row["status"], "LOCAL_EVIDENCE_INVALID")
        self.assertEqual(row["evidence_integrity"], "LOCAL_CHAIN_INVALID")

    def test_unrecognized_owner_db_remains_untouched(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE original_keep (secret TEXT)")
            db.execute("INSERT INTO original_keep VALUES ('preserve')")
            db.commit()
        before = self.db.read_bytes()
        self.assertEqual(self.record(mode="append")["status"],
                         "LOCAL_WORKFLOW_LEDGER_REFUSED")
        self.assertEqual(self.db.read_bytes(), before)

    def test_existing_db_is_never_overwritten_by_new(self):
        self.db.write_bytes(b"PRIVATE-ORIGINAL-DB")
        before = self.db.read_bytes()
        self.assertEqual(self.record()["status"], "LOCAL_WORKFLOW_LEDGER_REFUSED")
        self.assertEqual(self.db.read_bytes(), before)

    def test_unknown_second_step_denied_before_db_creation(self):
        self.assertEqual(
            self.record(instructions="파일 확인: README.md; delete: final.pdf")["status"],
            "LOCAL_WORKFLOW_LEDGER_REFUSED")
        self.assertFalse(self.db.exists())

    def test_interrupted_run_remains_reserved_and_not_replayed(self):
        from flowpilot_local_workflow import run_workflow as original
        def interrupted(root, recipe, *, metadata_consent=False):
            if metadata_consent:
                raise KeyboardInterrupt("simulated interruption")
            return original(root, recipe, metadata_consent=False)
        with patch("flowpilot_multistage_ledger.run_workflow", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.record()
        state = self.get()
        self.assertEqual(state["status"], "PREVIOUS_RUN_INCOMPLETE_BLOCKED")
        self.assertEqual(self.record(mode="append")["status"],
                         "PREVIOUS_RUN_INCOMPLETE_BLOCKED")

    def test_read_requires_no_scope_or_consent(self):
        row = self.record(mode="read")
        self.assertEqual(row["status"], "READ_HAS_UNEXPECTED_OPTIONS")
        self.assertFalse(self.db.exists())

    def test_read_requires_existing_valid_file_and_no_mutation(self):
        self.record()
        before = self.db.read_bytes()
        self.assertEqual(self.get()["status"], "READ_ONLY_LOCAL_WORKFLOW_EVIDENCE")
        self.assertEqual(self.db.read_bytes(), before)

    def test_second_distinct_run_appends_without_data_loss(self):
        self.record()
        another = self.record(mode="append", run_id="run_g144secondabcd",
                              instructions="파일 확인: README.md")
        self.assertEqual(another["status"], "LOCAL_WORKFLOW_REVIEW_STORED")
        self.assertEqual(self.get()["executed_steps"], 2)
        read_second = run(self.db, "run_g144secondabcd", mode="read")
        self.assertEqual(read_second["executed_steps"], 1)

    def test_real_cli_process_new_read_replay(self):
        script = str(ROOT/"tools"/"flowpilot_multistage_ledger.py")
        common = [sys.executable, script, "--db", str(self.db),
                  "--run-id", self.run_id]
        commands = [
            common + ["--mode", "new", "--root", str(self.folder),
                      "--instructions", self.instructions,
                      "--approve-local-metadata", "--approve-local-db-write"],
            common + ["--mode", "read"],
            common + ["--mode", "append", "--root", str(self.folder),
                      "--instructions", self.instructions,
                      "--approve-local-metadata", "--approve-local-db-write"],
        ]
        codes = [0,0,2]
        statuses = ["LOCAL_WORKFLOW_REVIEW_STORED", "READ_ONLY_LOCAL_WORKFLOW_EVIDENCE",
                    "DUPLICATE_BLOCKED"]
        for command,code,status in zip(commands,codes,statuses):
            process = subprocess.run(command, capture_output=True, text=True, timeout=25)
            self.assertEqual(process.returncode, code, process.stderr)
            self.assertEqual(json.loads(process.stdout)["status"], status)
            self.assertNotIn(str(self.folder), process.stdout)
            self.assertNotIn("README.md", process.stdout)

if __name__ == "__main__":
    unittest.main()
