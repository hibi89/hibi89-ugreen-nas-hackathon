"""G134 real disposable local-file metadata + persistent SQLite E2E.

No NAS, Uliya, Docker, customer files or private assets; local fixtures only.
"""
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
from flowpilot_local_audit_ledger import run_local_audit_ledger
from flowpilot_persistent_qa import run_persistent


class LocalAuditLedgerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.parent = Path(tmp.name)
        self.folder = self.parent / "owner-SECRET-FOLDER"
        self.folder.mkdir()
        (self.folder / "README.md").write_bytes(b"owner-file-SECRET-CONTENT-never-open")
        (self.folder / "release").mkdir()
        self.db = self.parent / "audit.sqlite"
        self.run_id = "run_g134actual001"

    def audit(self, mode="new", *, required=None, metadata=True, write=True,
              goal="check required files", root=None, run_id=None, candidates=None):
        return run_local_audit_ledger(
            self.db, run_id or self.run_id, mode=mode,
            root=self.folder if root is None else root,
            required=["README.md"] if required is None else required,
            candidates=candidates, goal=goal,
            approve_local_metadata=metadata, approve_local_db_write=write)

    def test_local_actual_os_metadata_is_persisted_without_reading_contents(self):
        original = (self.folder / "README.md").read_bytes()
        result = self.audit()
        self.assertEqual(result["status"], "LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED")
        self.assertEqual(result["audit_result"], "NEEDS_REVIEW")
        self.assertEqual(result["item_count"], 1)
        self.assertEqual(result["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["owner_file_contents_opened"])
        self.assertEqual((self.folder / "README.md").read_bytes(), original)
        stored = self.db.read_bytes()
        for private in (str(self.folder).encode(), b"README.md", b"SECRET-CONTENT",
                        b"check required files", b"owner-SECRET-FOLDER"):
            self.assertNotIn(private, stored)
        self.assertNotIn("owner-SECRET", json.dumps(result))

    def test_missing_required_file_is_blocked_and_durable(self):
        row = self.audit(required=["README.md", "release/final.pdf"])
        self.assertEqual(row["status"], "LOCAL_METADATA_BLOCKED_EVIDENCE_STORED")
        self.assertEqual(row["audit_result"], "BLOCKED")
        read = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual([x["state"] for x in read["items"]], ["PRESENT", "MISSING"])
        self.assertEqual(read["evidence_integrity"], "LOCAL_CHAIN_INTACT")
        self.assertFalse(read["nas_verified"])

    def test_version_candidate_remains_needs_review(self):
        (self.folder / "release" / "v1.pdf").write_bytes(b"v1")
        (self.folder / "release" / "v2.pdf").write_bytes(b"v2")
        row = self.audit(required=["release/v1.pdf"], goal="compare versions",
                         candidates={"release/v1.pdf": ["release/v2.pdf"]})
        self.assertEqual(row["audit_result"], "NEEDS_REVIEW")
        read = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual(read["items"][0]["state"], "VERSION_REVIEW")

    def test_denied_metadata_does_not_read_or_write(self):
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder",
                   side_effect=AssertionError("SHOULD_NOT_INSPECT")):
            row = self.audit(metadata=False)
        self.assertEqual(row["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        self.assertFalse(self.db.exists())

    def test_denied_db_write_does_not_read_owner_metadata(self):
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder",
                   side_effect=AssertionError("SHOULD_NOT_INSPECT")):
            row = self.audit(write=False)
        self.assertEqual(row["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        self.assertFalse(self.db.exists())

    def test_replay_blocks_before_local_metadata_io(self):
        self.assertEqual(self.audit()["audit_result"], "NEEDS_REVIEW")
        original = self.db.read_bytes()
        from flowpilot_local_audit_ledger import inspect_owner_folder as real_reader
        def check(*a, **kw):
            if kw.get("metadata_consent") is True:
                raise AssertionError("REPLAYED_METADATA_READ")
            return real_reader(*a, **kw)
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder", side_effect=check):
            repeat = self.audit(mode="append")
        self.assertEqual(repeat["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(repeat["local_folder_inspected_again"])
        self.assertFalse(repeat["database_modified"])
        self.assertEqual(original, self.db.read_bytes())

    def test_run_id_same_scope_conflict_is_not_replayed(self):
        self.audit()
        row = self.audit(mode="append", required=["README.md", "release/final.pdf"])
        self.assertEqual(row["status"], "RUN_ID_SCOPE_CONFLICT")
        self.assertFalse(row["database_modified"])

    def test_second_run_with_distinct_id_in_same_database(self):
        first = self.audit()
        second = self.audit(mode="append", run_id="run_g134second02",
                            required=["release/missing.pdf"])
        self.assertEqual(first["audit_result"], "NEEDS_REVIEW")
        self.assertEqual(second["audit_result"], "BLOCKED")
        self.assertEqual(run_local_audit_ledger(self.db, self.run_id, mode="read")["audit_result"],
                         "NEEDS_REVIEW")
        self.assertEqual(run_local_audit_ledger(self.db, "run_g134second02", mode="read")["audit_result"],
                         "BLOCKED")

    def test_read_only_file_bytes_unchanged(self):
        self.audit()
        before = self.db.read_bytes()
        read = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual(read["status"], "READ_ONLY_LOCAL_METADATA_EVIDENCE")
        self.assertFalse(read["database_modified"])
        self.assertEqual(before, self.db.read_bytes())

    def test_tampered_row_detected_and_not_reexecuted(self):
        self.audit()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp134_metadata_runs SET state='BLOCKED' WHERE run_id=?",
                       (self.run_id,))
            db.commit()
        result = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual(result["status"], "LOCAL_EVIDENCE_INVALID")
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder") as io:
            io.return_value = {"status": "WAITING_APPROVAL"}
            another = self.audit(mode="append")
        self.assertEqual(another["status"], "PRIOR_LOCAL_EVIDENCE_INVALID")
        self.assertFalse(another["database_modified"])

    def test_unrecognized_db_is_not_changed(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE owner_data (secret TEXT)")
            db.execute("INSERT INTO owner_data VALUES('retain')")
            db.commit()
        original = self.db.read_bytes()
        row = self.audit(mode="append")
        self.assertEqual(row["status"], "LOCAL_AUDIT_LEDGER_REFUSED")
        self.assertEqual(self.db.read_bytes(), original)

    def test_create_never_overwrites_existing_original(self):
        self.db.write_bytes(b"owner-sensitive-original-database")
        original = self.db.read_bytes()
        row = self.audit()
        self.assertEqual(row["status"], "LOCAL_AUDIT_LEDGER_REFUSED")
        self.assertEqual(self.db.read_bytes(), original)

    def test_unapproved_goal_does_not_create_db(self):
        row = self.audit(goal="delete all NAS data")
        self.assertEqual(row["status"], "BLOCKED_UNSUPPORTED_SCOPE_OR_GOAL")
        self.assertFalse(self.db.exists())

    def test_traversal_and_restricted_file_are_refused_before_db_creation(self):
        for name in ("../bad", ".env", "secret.key"):
            with self.subTest(name=name):
                row = self.audit(required=[name])
                self.assertEqual(row["status"], "LOCAL_AUDIT_LEDGER_REFUSED")
                self.assertFalse(self.db.exists())

    def test_missing_root_after_consent_yields_fail_closed_record(self):
        row = self.audit(root=self.parent / "missing-root")
        self.assertEqual(row["status"], "LOCAL_METADATA_CHECK_FAILED_EVIDENCE_STORED")
        stored = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual(stored["audit_result"], "LOCAL_AUDIT_FAILED")
        self.assertFalse(stored["local_observation_complete"])

    def test_interrupted_run_stays_reserved_with_no_retry(self):
        from flowpilot_local_audit_ledger import inspect_owner_folder as real_reader
        def crash(*a, **kw):
            if kw.get("metadata_consent"):
                raise KeyboardInterrupt("simulated crash, must not resume")
            return real_reader(*a, **kw)
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder", side_effect=crash):
            with self.assertRaises(KeyboardInterrupt):
                self.audit()
        row = run_local_audit_ledger(self.db, self.run_id, mode="read")
        self.assertEqual(row["status"], "PREVIOUS_RUN_INCOMPLETE_BLOCKED")
        repeat = self.audit(mode="append")
        self.assertEqual(repeat["status"], "PREVIOUS_RUN_INCOMPLETE_BLOCKED")

    def test_inherited_g133_db_retains_original_synthetic_records(self):
        synthetic = run_persistent("필수 파일 확인해줘", "run_g133old001", self.db,
                                   mode="new", approve_local_write=True)
        self.assertEqual(synthetic["status"], "PERSISTED_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        audit = self.audit(mode="append")
        self.assertEqual(audit["status"], "LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED")
        old = run_persistent(None, "run_g133old001", self.db, mode="read")
        self.assertEqual(old["evidence_integrity"], "LOCAL_CHAIN_INTACT")

    def test_rejects_malformed_reader_receipt(self):
        from flowpilot_local_audit_ledger import inspect_owner_folder as real_reader
        def fake(*a, **kw):
            if kw.get("metadata_consent"):
                return {"status": "NEEDS_REVIEW", "items": [{"index": 1, "state": "PRESENT",
                                 "local_reference_count": 1, "path": "PRIVATE"}],
                        "item_count": 1, "inspected_local_metadata": True,
                        "file_contents_opened": False, "nas_verified": False,
                        "registered_uliya_agent_invoked": False}
            return real_reader(*a, **kw)
        with patch("flowpilot_local_audit_ledger.inspect_owner_folder", side_effect=fake):
            row = self.audit()
        self.assertEqual(row["status"], "LOCAL_METADATA_CHECK_FAILED_EVIDENCE_STORED")
        self.assertNotIn("PRIVATE", self.db.read_bytes().decode("latin1"))

    def test_read_mode_disallows_scope_and_approval(self):
        row = self.audit(mode="read")
        self.assertEqual(row["status"], "READ_MODE_HAS_UNEXPECTED_SCOPE_OR_CONSENT")
        self.assertFalse(self.db.exists())

    def test_command_line_new_read_replay_across_processes(self):
        common = [sys.executable, str(ROOT / "tools" / "flowpilot_local_audit_ledger.py"),
                  "--db", str(self.db), "--run-id", self.run_id]
        run = subprocess.run(common + ["--mode", "new", "--root", str(self.folder),
                                     "--required", "README.md", "--approve-local-metadata",
                                     "--approve-local-db-write"],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        first = json.loads(run.stdout)
        self.assertEqual(first["status"], "LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED")
        self.assertNotIn(str(self.folder), run.stdout)
        read = subprocess.run(common + ["--mode", "read"],
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertEqual(json.loads(read.stdout)["items"][0]["state"], "PRESENT")
        replay = subprocess.run(common + ["--mode", "append", "--root", str(self.folder),
                                        "--required", "README.md", "--approve-local-metadata",
                                        "--approve-local-db-write"],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(replay.returncode, 2)
        self.assertEqual(json.loads(replay.stdout)["status"], "DUPLICATE_BLOCKED")

    def test_cli_no_consent_never_creates_db(self):
        cmd = [sys.executable, str(ROOT / "tools" / "flowpilot_local_audit_ledger.py"),
               "--db", str(self.db), "--mode", "new", "--run-id", self.run_id,
               "--root", str(self.folder), "--required", "README.md"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        self.assertFalse(self.db.exists())


if __name__ == "__main__":
    unittest.main()
