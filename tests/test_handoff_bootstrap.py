"""Checks that one-line UGREEN GitHub resumption works without conversation state."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHRASE = "[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]"
STATE_PATH = ROOT/"docs/roles/lead/LIVE_STATE.json"
class UgreenBootstrapContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    def test_exact_one_line_phrase(self):
        self.assertEqual(PHRASE,self.s["canonical_user_prompt"])
    def test_entry_documents_route_to_canonical_source(self):
        for name in ("START_HERE.md","CHAT_BOOTSTRAP.md","AGENTS.md","README.md"):
            with self.subTest(name=name):
                text=(ROOT/name).read_text(encoding="utf-8")
                self.assertIn(PHRASE,text)
                self.assertIn("LIVE_HANDOFF.md",text)
                self.assertIn("lead/ugreen",text)
    def test_required_handoff_exists_and_has_status(self):
        p=ROOT/"docs/roles/lead/LIVE_HANDOFF.md"
        body=p.read_text(encoding="utf-8")
        self.assertIn(PHRASE,body)
        self.assertIn("91/91",body)
        self.assertIn("BLOCKED",body)
        self.assertIn("SESSION_CLOSEOUT.md",body)
    def test_live_state_structural_contract(self):
        s=self.s
        self.assertEqual("hibi89/hibi89-ugreen-nas-hackathon",s["repository"])
        self.assertEqual("lead/ugreen",s["authoritative_branch"])
        self.assertTrue(s["next_chat_must_refetch_live_head"])
        self.assertTrue(s["new_commit_sha_must_be_verified_after_write"])
        self.assertGreaterEqual(s["offline_synthetic_tests_passed"],91)
    def test_status_not_falsified_as_real_nas(self):
        self.assertEqual("NOT_RUN",self.s["nas_runtime"])
        self.assertEqual("NOT_CHECKED",self.s["pii_safety"])
        self.assertNotEqual("PASS",self.s["official_sdk_cli_schema"])
        self.assertNotEqual("SUBMITTED",self.s["devpost_final_submission"])
    def test_daily_progress_has_distinct_completed_day(self):
        day=self.s["current_calendar_day"]
        self.assertEqual(100,day["delivered_completion_percent"])
        self.assertEqual(0,day["remaining_percent"])
        self.assertTrue(day["sdk_gate_distinct"])
    def test_next_work_budget_and_blockers(self):
        n=self.s["next_work"]
        self.assertTrue(n["id"])
        self.assertGreaterEqual(n["planned_hours"],0)
        self.assertGreaterEqual(n["separate_reserve_hours"],0)
        if n["status"].startswith("BLOCKED"):
            self.assertIsNone(n["actual_completion_eta_hours"])
    def test_end_session_sync_contract(self):
        close=(ROOT/"docs/roles/lead/SESSION_CLOSEOUT.md").read_text(encoding="utf-8")
        for name in self.s["closeout_must_update"]:
            self.assertTrue((ROOT/name).exists(),name)
            self.assertIn(name.split("/")[-1],close)
    def test_advanced_files_exist(self):
        for item in self.s["advance_done_offline"]:
            self.assertTrue((ROOT/item["source"]).exists(),item["source"])
            self.assertEqual("SYNTHETIC_ONLY",item["status"])
    def test_handoff_uses_valid_sha_snapshot(self):
        sha=self.s["last_source_verified_head_at_handoff"]
        self.assertRegex(sha,r"^[0-9a-f]{40}$")
        self.assertTrue(self.s["next_chat_must_refetch_live_head"])

if __name__ == "__main__":
    unittest.main()
