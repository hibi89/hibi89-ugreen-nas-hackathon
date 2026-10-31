"""G119 SQLite synthetic evidence chain and exact run ID idempotency."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_repair_ledger import run_once, verify_record

GOAL = "필수 파일 확인해줘"


class G119LedgerTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = sqlite3.connect(Path(folder.name) / "evidence.sqlite")
        self.addCleanup(self.db.close)

    def test_real_local_fixture_and_verifiable_repair_trace(self):
        r = run_once(GOAL, "run_G119repair01", self.db, inject_test_fault=True)
        self.assertEqual(r["status"], "SYNTHETIC_LEDGER_PASS")
        self.assertEqual(r["repair_count"], 1)
        self.assertTrue(r["synthetic_fixture_executed"])
        self.assertEqual(verify_record(self.db, "run_G119repair01")["status"], "LOCAL_CHAIN_INTACT")
        self.assertFalse(r["actual_docker_executed"])
        self.assertFalse(r["nas_verified"])

    def test_duplicate_id_blocks_before_engine(self):
        run_once(GOAL, "run_replay123456", self.db)
        with patch("flowpilot_repair_ledger.run_council", side_effect=AssertionError("replayed")):
            r = run_once(GOAL, "run_replay123456", self.db)
        self.assertEqual(r["status"], "DUPLICATE_BLOCKED")
        self.assertFalse(r["executed"])

    def test_id_cannot_be_reused_for_a_different_goal(self):
        run_once(GOAL, "run_collision1234", self.db)
        r = run_once("고객별 매출 보고서 만들어줘", "run_collision1234", self.db)
        self.assertEqual(r["status"], "RUN_ID_GOAL_CONFLICT")
        self.assertFalse(r["executed"])

    def test_repair_refused_still_records_terminal_block(self):
        row = run_once(GOAL, "run_norepair12345", self.db,
                       inject_test_fault=True, max_repairs=0)
        self.assertEqual(row["status"], "SYNTHETIC_LEDGER_BLOCKED")
        self.assertEqual(verify_record(self.db, "run_norepair12345")["status"],
                         "LOCAL_CHAIN_INTACT")

    def test_naive_event_tampering_is_detected(self):
        run_once(GOAL, "run_tamper123456", self.db)
        self.db.execute("UPDATE fp119_events SET detail=? WHERE run_id=? AND seq=2",
                        ('{"role":"QA","status":"PASS"}', "run_tamper123456"))
        self.db.commit()
        self.assertEqual(verify_record(self.db, "run_tamper123456")["status"],
                         "LOCAL_CHAIN_INVALID")

    def test_no_raw_goal_in_evidence_database(self):
        run_once("고객별 매출 보고서 만들어줘", "run_private123456", self.db)
        payload = self.db.execute("SELECT detail FROM fp119_events").fetchall()
        self.assertNotIn("고객별 매출 보고서", repr(payload))
        self.assertNotIn("create customer revenue summary", repr(payload))
        # Public fixed template IDs may contain the word customer; raw goals must not.

    def test_rejects_bad_run_ids_and_wrong_types(self):
        for key in ("../private", "run_short", "", "raw customer", "run_x"*30, None):
            with self.subTest(key=key), self.assertRaises(ValueError):
                run_once(GOAL, key, self.db)

    def test_unsupported_goal_never_creates_evidence(self):
        out = run_once("NAS 파일 지워줘", "run_unsupported123", self.db)
        self.assertEqual(out["status"], "UNSUPPORTED_GOAL")
        self.assertFalse(out["executed"])

    def test_failure_logs_are_sanitized(self):
        with patch("flowpilot_repair_ledger.run_council",
                   side_effect=RuntimeError("customer_secret_should_never_log")):
            r = run_once(GOAL, "run_failure123456", self.db)
        self.assertEqual(r["status"], "SYNTHETIC_LEDGER_BLOCKED")
        self.assertNotIn("customer_secret_should_never_log",
                         str(self.db.execute("SELECT * FROM fp119_events").fetchall()))

    def test_cli_korean_goal_windows_safe_json(self):
        cmd = [sys.executable, str(ROOT/"tools"/"flowpilot_repair_ledger.py"),
               "--goal", GOAL, "--run-id", "run_cli119123456",
               "--inject-test-fault"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.isascii())
        value = json.loads(p.stdout)
        self.assertEqual(value["status"], "SYNTHETIC_LEDGER_PASS")
        self.assertEqual(value["integrity"], "LOCAL_CHAIN_INTACT")


if __name__ == "__main__":
    unittest.main()
