"""G137 real disposable local OS metadata -> SQLite -> delta -> inert HTML E2E.

No private user files, NAS mount, network, Uliya expert or Docker runtime.
"""
from __future__ import annotations

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
from flowpilot_local_review_cli import review_local, render_review_html, write_new_report_html

INSTRUCTIONS = "파일 확인: README.md,release/final.pdf"
PREV = "run_g137initial01"
CURR = "run_g137repeat002"


class G137ReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.root = self.home / "PRIVATE_ROOT_OWNER_12345"
        self.root.mkdir()
        (self.root / "release").mkdir()
        (self.root / "README.md").write_bytes(b"PRIVATE_OWNER_CONTENT_DO_NOT_OPEN")
        self.db = self.home / "audit.sqlite"
        self.html = self.home / "report.html"

    def review(self, action, *, instructions=INSTRUCTIONS, root=None, **kwargs):
        return review_local(action=action, instructions=instructions,
                            root=self.root if root is None else root, **kwargs)

    def capture(self, run_id, mode, **kwargs):
        return self.review("capture", db=self.db, run_id=run_id, mode=mode,
                           approve_local_metadata=True, approve_local_db_write=True,
                           **kwargs)

    def two(self):
        first = self.capture(PREV, "new")
        self.assertEqual(first["audit_result"], "BLOCKED")
        (self.root / "release" / "final.pdf").write_bytes(b"%PDF synthetic-not-real")
        second = self.capture(CURR, "append")
        self.assertEqual(second["audit_result"], "NEEDS_REVIEW")

    def comparison(self, **kwargs):
        return self.review("compare", db=self.db, previous_id=PREV,
                           current_id=CURR, **kwargs)

    def test_full_local_pipeline_recovery_and_html(self):
        original = (self.root / "README.md").read_bytes()
        preview = self.review("preview")
        self.assertEqual(preview["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        self.assertFalse(preview["local_folder_inspected"])
        self.assertFalse(self.db.exists())
        self.two()
        before = self.db.read_bytes()
        result = self.comparison()
        self.assertEqual(result["status"], "SNAPSHOT_DELTA_REVIEW_REQUIRED")
        self.assertEqual(result["resolved_missing_to_present_count"], 1)
        self.assertEqual(result["new_missing_count"], 0)
        self.assertTrue(result["local_only"])
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["owner_folder_inspected_again"])
        write_new_report_html(self.html, result)
        markup = self.html.read_text(encoding="utf-8")
        self.assertIn("RELEASE HOLD", markup)
        self.assertIn("MISSING", markup)
        self.assertIn("PRESENT", markup)
        self.assertIn("default-src 'none'", markup)
        self.assertNotIn("<script", markup)
        for secret in (str(self.root), "README.md", "release/final.pdf", "PRIVATE_OWNER_CONTENT"):
            self.assertNotIn(secret, json.dumps(result))
            self.assertNotIn(secret, markup)
            self.assertNotIn(secret, self.db.read_bytes().decode("latin1"))
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(original, (self.root / "README.md").read_bytes())

    def test_capture_without_consent_never_opens_db_or_owner_folder(self):
        with patch("flowpilot_local_review_cli.run_local_audit_ledger", side_effect=AssertionError("EXECUTED")):
            result = self.review("capture", db=self.db, run_id=PREV, mode="new")
        self.assertEqual(result["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        self.assertFalse(self.db.exists())

    def test_preview_no_root_io(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("SCANNED")):
            result = self.review("preview")
        self.assertFalse(result["local_folder_inspected"])

    def test_unrecognized_second_stage_blocks_before_any_db(self):
        result = self.review("capture", instructions="파일 확인: README.md; 삭제: README.md",
                             db=self.db, run_id=PREV, mode="new",
                             approve_local_metadata=True, approve_local_db_write=True)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REFUSED")
        self.assertFalse(self.db.exists())

    def test_known_second_stage_still_refused_single_stage_contract(self):
        result = self.review("capture", instructions="파일 확인: README.md; 파일 확인: release/final.pdf",
                             db=self.db, run_id=PREV, mode="new",
                             approve_local_metadata=True, approve_local_db_write=True)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REFUSED")
        self.assertFalse(self.db.exists())

    def test_scope_traversal_refused_without_io(self):
        result = self.review("capture", instructions="파일 확인: ../private.txt", db=self.db,
                             run_id=PREV, mode="new", approve_local_metadata=True,
                             approve_local_db_write=True)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REFUSED")
        self.assertFalse(self.db.exists())

    def test_replay_same_id_cannot_reinspect_owner(self):
        self.capture(PREV, "new")
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("RE-SCANNED")):
            result = self.capture(PREV, "append")
        self.assertEqual(result["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(result["database_modified"])

    def test_true_replay_returns_duplicate_blocked(self):
        self.capture(PREV, "new")
        result = self.capture(PREV, "append")
        self.assertEqual(result["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(result["database_modified"])

    def test_inverted_comparison_refused(self):
        self.two()
        result = self.review("compare", db=self.db, previous_id=CURR, current_id=PREV)
        self.assertEqual(result["status"], "REVERSED_OR_UNVERIFIABLE_SNAPSHOT_ORDER")
        self.assertFalse(result["database_modified"])

    def test_comparison_requires_same_scope(self):
        self.two()
        result = self.comparison(instructions="파일 확인: README.md")
        self.assertEqual(result["status"], "SNAPSHOT_SCOPE_MISMATCH")

    def test_untrusted_database_refused_no_mutation(self):
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE private_table(value TEXT)")
            db.execute("INSERT INTO private_table VALUES('OWNER_KEEP')")
        before = self.db.read_bytes()
        result = self.comparison()
        self.assertEqual(result["status"], "LOCAL_SNAPSHOT_COMPARISON_REFUSED")
        self.assertEqual(before, self.db.read_bytes())

    def test_original_html_must_not_be_overwritten(self):
        self.two()
        result = self.comparison()
        self.html.write_text("OWNED ORIGINAL", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_new_report_html(self.html, result)
        self.assertEqual(self.html.read_text(encoding="utf-8"), "OWNED ORIGINAL")

    def test_invalid_untrusted_html_refused(self):
        self.two()
        result = self.comparison()
        result["changes"][0]["state"] = "<script>secret</script>"
        with self.assertRaises(ValueError):
            render_review_html(result)
        self.assertFalse(self.html.exists())

    def test_cannot_export_html_on_invalid_or_missing_history(self):
        result = self.comparison()
        with self.assertRaises(ValueError):
            write_new_report_html(self.html, result)
        self.assertFalse(self.html.exists())

    def test_cli_e2e_across_processes(self):
        base = [sys.executable, str(ROOT / "tools/flowpilot_local_review_cli.py"),
                "--instructions", INSTRUCTIONS, "--root", str(self.root)]
        def command(*args):
            return subprocess.run(base + list(args), capture_output=True, text=True, timeout=30)
        pre = command("--action", "preview")
        self.assertEqual(pre.returncode, 0, pre.stderr)
        self.assertEqual(json.loads(pre.stdout)["status"], "WAITING_TWO_SEPARATE_LOCAL_APPROVALS")
        first = command("--action", "capture", "--db", str(self.db),
                        "--mode", "new", "--run-id", PREV,
                        "--approve-local-metadata", "--approve-local-db-write")
        self.assertEqual(json.loads(first.stdout)["audit_result"], "BLOCKED")
        (self.root / "release/final.pdf").write_bytes(b"G137 synthetic")
        second = command("--action", "capture", "--db", str(self.db),
                         "--mode", "append", "--run-id", CURR,
                         "--approve-local-metadata", "--approve-local-db-write")
        self.assertEqual(second.returncode, 0, second.stderr)
        comparison = command("--action", "compare", "--db", str(self.db),
                             "--previous-id", PREV, "--current-id", CURR,
                             "--html-out", str(self.html))
        self.assertEqual(comparison.returncode, 0, comparison.stderr)
        output = json.loads(comparison.stdout)
        self.assertTrue(output["local_html_created"])
        self.assertEqual(output["resolved_missing_to_present_count"], 1)
        self.assertTrue(self.html.exists())
        self.assertNotIn("PRIVATE_ROOT_OWNER", comparison.stdout + comparison.stderr)
        self.assertNotIn("README.md", comparison.stdout + comparison.stderr)
        self.assertNotIn(str(self.db), comparison.stdout + comparison.stderr)

    def test_invalid_html_path_rejected_without_leaking_owner(self):
        self.two()
        result = self.comparison()
        with self.assertRaises(ValueError):
            write_new_report_html(Path("relative.html"), result)
        with self.assertRaises(ValueError):
            write_new_report_html(self.home / "blocked.txt", result)
        self.assertFalse(self.html.exists())


if __name__ == "__main__":
    unittest.main()