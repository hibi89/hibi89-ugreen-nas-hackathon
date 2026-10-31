"""G135 real local disposable metadata snapshot delta, SQLite read-only tests.

Developer local test uses temporary filesystem. No NAS, Expert, owner data.
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
from flowpilot_local_audit_delta import compare_local_audits
from flowpilot_local_audit_ledger import run_local_audit_ledger, _digest, _scope_digest
from flowpilot_persistent_qa import _connect

GOAL = "check required files"
PREV = "run_g135baseline01"
CURR = "run_g135current002"


class DeltaTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.base = Path(td.name)
        self.root = self.base / "PRIVATE_OWNER_LOCAL_FOLDER"
        self.root.mkdir()
        (self.root / "release").mkdir()
        self.db = self.base / "evidence.sqlite"
        self.required = ["README.md", "release/final.pdf"]
        (self.root / "README.md").write_text("PRIVATE_OWNER_CONTENT", encoding="utf-8")

    def capture(self, run_id, *, mode, required=None, goal=GOAL, candidates=None):
        return run_local_audit_ledger(
            self.db, run_id, mode=mode, root=self.root,
            required=self.required if required is None else required,
            candidates=candidates, goal=goal,
            approve_local_metadata=True, approve_local_db_write=True,
        )

    def delta(self, *, previous_id=PREV, current_id=CURR,
              required=None, root=None, goal=GOAL, candidates=None):
        return compare_local_audits(
            self.db, previous_id, current_id,
            root=self.root if root is None else root,
            required=self.required if required is None else required,
            candidates=candidates, goal=goal,
        )

    def two(self):
        self.assertEqual(self.capture(PREV, mode="new")["audit_result"], "BLOCKED")
        (self.root / "release" / "final.pdf").write_bytes(b"%PDF-test-only")
        self.assertEqual(self.capture(CURR, mode="append")["audit_result"], "NEEDS_REVIEW")

    def test_genuine_local_missing_becomes_present(self):
        self.two()
        report = self.delta()
        self.assertEqual(report["status"], "SNAPSHOT_DELTA_REVIEW_REQUIRED")
        self.assertEqual(report["change_count"], 1)
        self.assertEqual(report["resolved_missing_to_present_count"], 1)
        self.assertEqual(report["new_missing_count"], 0)
        self.assertEqual(report["changes"], [{
            "index": 2, "before": "MISSING", "after": "PRESENT",
            "reference_count_before": 0, "reference_count_after": 1,
        }])
        self.assertTrue(report["scope_match_verified_locally"])
        self.assertFalse(report["nas_verified"])
        self.assertFalse(report["owner_folder_inspected_again"])
        self.assertFalse(report["database_modified"])
        self.assertEqual(report["release_gate"], "HOLD")
        for confidential in ("PRIVATE_OWNER_LOCAL_FOLDER", "README.md", "release/final.pdf", "PRIVATE_OWNER_CONTENT"):
            self.assertNotIn(confidential, json.dumps(report))

    def test_new_missing_is_explicitly_counted(self):
        (self.root / "release" / "final.pdf").write_bytes(b"fixture")
        self.capture(PREV, mode="new")
        (self.root / "release" / "final.pdf").unlink()
        self.capture(CURR, mode="append")
        report = self.delta()
        self.assertEqual(report["new_missing_count"], 1)
        self.assertEqual(report["resolved_missing_to_present_count"], 0)
        self.assertEqual(report["changes"][0]["after"], "MISSING")

    def test_identical_snapshots_still_require_human_review(self):
        self.capture(PREV, mode="new")
        self.capture(CURR, mode="append")
        result = self.delta()
        self.assertEqual(result["status"], "SNAPSHOTS_EQUAL_REVIEW_REQUIRED")
        self.assertEqual(result["change_count"], 0)
        self.assertFalse(result["comparison_is_live_nas_state"])

    def test_unrelated_scope_rejected_even_when_state_counts_look_same(self):
        self.capture(PREV, mode="new")
        self.capture(CURR, mode="append", required=["release/final.pdf", "README.md"])
        self.assertEqual(self.delta()["status"], "SNAPSHOT_SCOPE_MISMATCH")

    def test_different_required_scope_argument_cannot_launder_comparison(self):
        self.two()
        self.assertEqual(self.delta(required=["README.md", "release/other.pdf"])["status"],
                         "SNAPSHOT_SCOPE_MISMATCH")
        self.assertEqual(self.delta(root=self.base / "different_root")["status"],
                         "SNAPSHOT_SCOPE_MISMATCH")

    def test_tampered_snapshots_blocked(self):
        self.two()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp134_metadata_runs SET summary_json='[]' WHERE run_id=?", (CURR,))
            db.commit()
        self.assertEqual(self.delta()["status"], "EVIDENCE_INTEGRITY_INVALID")

    def test_previous_incomplete_run_blocks_comparison(self):
        self.capture(PREV, mode="new")
        salt = "a" * 32
        scope_sha = _scope_digest(salt, root=self.root, goal=GOAL,
                                  required=self.required, candidates={})
        digest = _digest(CURR, salt, scope_sha, "IN_PROGRESS", [])
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("INSERT INTO fp134_metadata_runs VALUES(?,?,?,?,?,?)",
                       (CURR, salt, scope_sha, "IN_PROGRESS", "[]", digest))
            db.commit()
        self.assertEqual(self.delta()["status"], "INCOMPLETE_SNAPSHOT_BLOCKED")

    def test_failed_snapshot_cannot_be_compared_as_valid_missing(self):
        self.capture(PREV, mode="new")
        missing_dir = self.base / "not-real"
        result = run_local_audit_ledger(
            self.db, CURR, mode="append", root=missing_dir,
            required=self.required, goal=GOAL,
            approve_local_metadata=True, approve_local_db_write=True,
        )
        self.assertEqual(result["audit_result"], "LOCAL_AUDIT_FAILED")
        self.assertEqual(self.delta()["status"], "FAILED_OR_UNVERIFIED_SNAPSHOT_BLOCKED")

    def test_absent_run_refused(self):
        self.capture(PREV, mode="new")
        self.assertEqual(self.delta()["status"], "SNAPSHOT_NOT_FOUND")

    def test_existing_synthetic_only_database_no_metadata_records(self):
        with closing(_connect(self.db, mode="new")) as _:
            pass
        self.assertEqual(self.delta()["status"], "NO_METADATA_RECORDS")

    def test_nonexistent_db_and_path_error_redacted(self):
        report = self.delta()
        self.assertEqual(report["status"], "LOCAL_SNAPSHOT_COMPARISON_REFUSED")
        self.assertNotIn(str(self.db), json.dumps(report))

    def test_same_ids_or_bad_ids_block_before_io(self):
        with patch("flowpilot_local_audit_delta._connect", side_effect=AssertionError("DB_READ")):
            self.assertEqual(self.delta(current_id=PREV)["status"], "INVALID_COMPARISON_RUN_IDS")
            self.assertEqual(self.delta(previous_id="bad/secret")["status"], "INVALID_COMPARISON_RUN_IDS")

    def test_reject_restricted_scope_without_touching_db(self):
        with patch("flowpilot_local_audit_delta._connect", side_effect=AssertionError("DB_READ")):
            report = self.delta(required=[".env"])
        self.assertEqual(report["status"], "LOCAL_SNAPSHOT_COMPARISON_REFUSED")

    def test_no_reinspection_of_owner_folder_and_db_identical_bytes(self):
        self.two()
        before = self.db.read_bytes()
        from flowpilot_local_audit_delta import inspect_owner_folder as original
        def inspect(*args, **kwargs):
            self.assertIs(kwargs.get("metadata_consent"), False)
            return original(*args, **kwargs)
        with patch("flowpilot_local_audit_delta.inspect_owner_folder", side_effect=inspect):
            self.assertEqual(self.delta()["resolved_missing_to_present_count"], 1)
        self.assertEqual(before, self.db.read_bytes())

    def test_version_conflict_introduced_requires_review(self):
        (self.root / "release" / "final.pdf").write_bytes(b"fixture")
        candidate = {"release/final.pdf": ["release/final_v2.pdf"]}
        self.capture(PREV, mode="new", candidates=candidate, goal="compare versions")
        (self.root / "release" / "final_v2.pdf").write_bytes(b"version2")
        self.capture(CURR, mode="append", candidates=candidate, goal="compare versions")
        report = self.delta(candidates=candidate, goal="compare versions")
        self.assertEqual(report["new_uncertainty_count"], 1)
        self.assertEqual(report["changes"][0]["after"], "VERSION_REVIEW")

    def test_cross_process_cli_json_does_not_expose_owner_scope(self):
        self.two()
        cmd = [sys.executable, str(ROOT / "tools" / "flowpilot_local_audit_delta.py"),
               "--db", str(self.db), "--previous-id", PREV, "--current-id", CURR,
               "--root", str(self.root), "--required", "README.md",
               "--required", "release/final.pdf"]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["resolved_missing_to_present_count"], 1)
        self.assertNotIn(str(self.root), result.stdout + result.stderr)
        self.assertNotIn("README.md", result.stdout + result.stderr)
        self.assertNotIn("release/final.pdf", result.stdout + result.stderr)
        self.assertFalse(parsed["nas_verified"])

    def test_unknown_owner_sqlite_never_modified(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE PRIVATE(value TEXT)")
            db.execute("INSERT INTO PRIVATE VALUES ('owner-keep')")
            db.commit()
        before = self.db.read_bytes()
        self.assertEqual(self.delta()["status"], "LOCAL_SNAPSHOT_COMPARISON_REFUSED")
        self.assertEqual(before, self.db.read_bytes())


if __name__ == "__main__":
    unittest.main()