"""Offline tests for UGREEN canonical work schedule and synchronization."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_master_progress import MASTER,SOURCE,integrity_errors
from check_handoff_sync import closeout_errors,REQUIRED

class MasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=MASTER.read_text(encoding="utf8");cls.p=SOURCE.read_text(encoding="utf8")
    def test_full_plan_matches_original(self):
        self.assertEqual([],integrity_errors(self.m,self.p))
    def test_missing_day_rejected(self):
        bad="\n".join(line for line in self.m.splitlines() if not line.startswith("| 2026-11-16 |"))
        self.assertTrue(integrity_errors(bad,self.p))
    def test_rewritten_hours_rejected(self):
        self.assertTrue(integrity_errors(self.m.replace("| 1.5 | 1.5 |","| 99 | 1.5 |",1),self.p))
    def test_false_final_done_rejected(self):
        self.assertTrue(integrity_errors(self.m.replace("| D24 | **NOT_STARTED** |","| D24 | **DONE** |"),self.p))
    def test_missing_master_on_source_push_rejected(self):
        self.assertTrue(closeout_errors({"src/projectready/presence.py"}))
    def test_missing_master_on_document_only_push_rejected(self):
        self.assertTrue(closeout_errors({"docs/roles/lead/LIVE_HANDOFF.md"}))
    def test_master_and_handoff_sync_accepted(self):
        self.assertEqual([],closeout_errors(set(REQUIRED)|{"src/projectready/presence.py"}))
    def test_master_only_push_accepted(self):
        self.assertEqual([],closeout_errors({"MASTER_PROGRESS.md"}))

if __name__=="__main__":unittest.main()
