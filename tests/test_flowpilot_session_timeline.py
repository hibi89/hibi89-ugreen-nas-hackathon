"""G122 single offline timeline, synthetic QA idempotency, safe HTML export."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from flowpilot_session_timeline import run_session_timeline,render_offline_dashboard,write_new_offline_html

GOAL = "필수 파일 확인해줘"
ROOT_SECRET = "/volume1/projects/SENSITIVE_OWNER_CLIENT"
FILES = "README.md,release/SENSITIVE_OWNER_FILE.pdf"
OK = [ROOT_SECRET, FILES, "APPROVE_METADATA", "ACK_UNKNOWN_PROCESSING"]

class G122TimelineTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir=Path(tmp.name)
        self.db=sqlite3.connect(self.dir/"ledger.sqlite")
        self.addCleanup(self.db.close)

    def run_timeline(self, replies=OK, *, run_id="run_g122safe001", goal=GOAL,
                     qa=True, fault=True, loader=None):
        answers=iter(replies)
        outputs=[]
        result=run_session_timeline(
            goal, run_id, self.db, ask=lambda _ : next(answers),
            emit=outputs.append, kit_loader=loader,
            approved_synthetic_qa=qa, inject_test_fault=fault,
        )
        body=json.dumps(result)+"\n"+"\n".join(outputs)
        self.assertNotIn("SENSITIVE_OWNER_CLIENT",body)
        self.assertNotIn("SENSITIVE_OWNER_FILE",body)
        return result

    def test_real_local_qa_one_repair_timeline_and_verified_chain(self):
        row=self.run_timeline()
        self.assertEqual(row["status"],"LOCAL_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        self.assertEqual(row["evidence_integrity"],"LOCAL_CHAIN_INTACT")
        self.assertEqual(row["repair_count"],1)
        self.assertEqual(len(row["steps"]),6)
        self.assertEqual([x["status"] for x in row["steps"]],
                         ["PASS","PASS","WAITING","PASS","PASS","WAITING"])
        self.assertTrue(any(x["role"]=="Repair" for x in row["council_roles"]))
        self.assertFalse(row["nas_verified"])
        self.assertEqual(row["release_gate"],"HOLD")

    def test_duplicate_run_blocked_before_qa_function(self):
        self.run_timeline(run_id="run_g122dup0001")
        with patch("flowpilot_repair_ledger.run_council",
                   side_effect=AssertionError("re-executed unexpectedly")):
            repeat=self.run_timeline(run_id="run_g122dup0001")
        self.assertEqual(repeat["status"],"DUPLICATE_BLOCKED")
        self.assertFalse(repeat["local_synthetic_qa_executed_again"])

    def test_same_id_other_goal_blocks_but_never_executes(self):
        self.run_timeline(run_id="run_g122conflict1")
        with patch("flowpilot_repair_ledger.run_council",
                   side_effect=AssertionError("should not run")):
            row=self.run_timeline(
                run_id="run_g122conflict1",goal="check required files")
        self.assertEqual(row["status"],"RUN_ID_GOAL_CONFLICT")

    def test_no_consent_means_no_database_write_or_fixture(self):
        with patch("flowpilot_repair_ledger.run_council",
                   side_effect=AssertionError("must not execute")):
            row=self.run_timeline(
                replies=[ROOT_SECRET,FILES,"DECLINE"],run_id="run_g122decline1")
        self.assertEqual(row["status"],"NO_SYNTHETIC_EXECUTION")
        self.assertEqual(row["guided_status"],"DECLINED_NO_ACTION")
        found=self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fp119_runs'").fetchone()
        self.assertIsNone(found)

    def test_synthetic_qa_is_separate_explicit_optin(self):
        row=self.run_timeline(qa=False)
        self.assertEqual(row["status"],"NO_SYNTHETIC_EXECUTION")
        self.assertEqual(row["steps"][3]["status"],"NOT_RUN")
        self.assertEqual(row["steps"][4]["status"],"NOT_RUN")

    def test_unimplemented_csv_and_delete_never_prompt_or_touch_db(self):
        for goal in ("고객별 매출 보고서 만들어줘","모든 NAS 파일 삭제해줘"):
            row=run_session_timeline(
                goal,"run_g122blocked9",self.db,
                ask=lambda _: self.fail("Unexpected prompt"),approved_synthetic_qa=True)
            self.assertEqual(row["status"],"NO_SYNTHETIC_EXECUTION")
            self.assertFalse(row["local_synthetic_qa_attempted"])

    def test_blocked_repair_records_only_blocked_qa(self):
        from flowpilot_repair_ledger import run_once
        # Pre-reserved blocked run is replay-protected even if UI reruns.
        pre=run_once(GOAL,"run_g122blocked1",self.db,
                     inject_test_fault=True,max_repairs=0)
        self.assertEqual(pre["status"],"SYNTHETIC_LEDGER_BLOCKED")
        row=self.run_timeline(run_id="run_g122blocked1")
        self.assertEqual(row["status"],"DUPLICATE_BLOCKED")

    def test_corrupt_chain_is_not_counted_as_verified_pass(self):
        self.run_timeline(run_id="run_g122tamper12")
        self.db.execute("UPDATE fp119_events SET detail='{}' WHERE run_id=? AND seq=2",
                        ("run_g122tamper12",))
        self.db.commit()
        row=self.run_timeline(run_id="run_g122tamper12")
        self.assertEqual(row["status"],"DUPLICATE_BLOCKED")
        self.assertFalse(row["local_synthetic_qa_executed_again"])

    def test_html_static_no_inline_scripts_or_private_data(self):
        row=self.run_timeline()
        markup=render_offline_dashboard(row)
        self.assertIn("default-src 'none'",markup)
        self.assertNotIn("<script",markup)
        self.assertNotIn("SENSITIVE_OWNER",markup)
        self.assertIn("RELEASE HOLD",markup)
        p=self.dir/"offline.html"
        write_new_offline_html(p,row)
        self.assertTrue(p.is_file())
        self.assertEqual(p.read_text(encoding="utf-8"),markup)
        with self.assertRaises(FileExistsError):
            write_new_offline_html(p,row)

    def test_dashboard_rejects_modified_timeline_or_unsafe_markup(self):
        row=self.run_timeline()
        row["steps"][0]["description"]="<script>alert(1)</script>"
        with self.assertRaises(ValueError):
            render_offline_dashboard(row)
        row["steps"][0]["description"]="Review a single known natural-language file-inspection intent."
        row["run_id"]="<img src=x onerror=alert(1)>"
        self.assertNotIn("<img",render_offline_dashboard(row))
        self.assertIn("&lt;img",render_offline_dashboard(row))

    def test_refuses_untrusted_run_id_before_asking(self):
        with self.assertRaises(ValueError):
            run_session_timeline(GOAL,"../../secret",self.db,
                                 ask=lambda _: self.fail("Should not ask"))

    def test_cli_offline_ascii_json_does_not_persist_user_data(self):
        p=subprocess.run(
            [sys.executable,str(ROOT/"tools"/"flowpilot_session_timeline.py"),
             "--goal",GOAL,"--run-id","run_g122cli12345","--synthetic-qa"],
            input="\n".join(OK)+"\n",capture_output=True,text=True,timeout=20,
        )
        self.assertEqual(p.returncode,0,p.stderr)
        obj=json.loads(p.stdout)
        self.assertEqual(obj["status"],"LOCAL_SYNTHETIC_QA_PASS_NATIVE_HOLD")
        self.assertEqual(obj["evidence_integrity"],"LOCAL_CHAIN_INTACT")
        self.assertTrue(p.stdout.isascii())
        self.assertNotIn("SENSITIVE_OWNER",p.stdout)

if __name__=="__main__":
    unittest.main()
