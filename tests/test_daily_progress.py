"""Tests for daily milestone weights, blockers, and honest time reporting."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from projectready.progress_policy import validate_daily_progress

class DailyProgressTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "docs/roles/lead/DAILY_PROGRESS.json").read_text(encoding="utf-8"))

    def test_snapshot_is_consistent(self):
        self.assertEqual(100, validate_daily_progress(self.data)["completed_percent"])

    def test_daily_full_does_not_claim_sdk_compatible(self):
        self.assertNotEqual("PASS", self.data["g1_technical_gate"])
        self.assertFalse(self.data["overall_official_skill_sdk_compatible"])

    def test_historical_75_snapshot_preserved(self):
        old = json.loads((ROOT / "docs/roles/lead/history/20261024_G1_EARLY_75_PERCENT_SNAPSHOT.json").read_text(encoding="utf-8"))
        self.assertEqual(75, old["completed_percent"])
        self.assertEqual(25, old["remaining_percent"])

    def test_sum_must_equal_100(self):
        d=deepcopy(self.data)
        d["milestones"][0]["weight_percent"]=20
        with self.assertRaises(ValueError):
            validate_daily_progress(d)

    def test_blocked_item_cannot_be_counted_done(self):
        d=deepcopy(self.data)
        d["milestones"][0]["status"]="BLOCKED"
        # Finished total must now be 75, but JSON still says 100.
        with self.assertRaises(ValueError):
            validate_daily_progress(d)

    def test_done_needs_evidence(self):
        d=deepcopy(self.data)
        d["milestones"][0]["evidence"]=""
        with self.assertRaises(ValueError):
            validate_daily_progress(d)

    def test_unmeasured_time_is_not_invented(self):
        d=deepcopy(self.data)
        d["actual_time_measurement"]="MEASURED"
        with self.assertRaises(ValueError):
            validate_daily_progress(d)

    def test_blocked_external_eta_is_unknown(self):
        d=deepcopy(self.data)
        d["milestones"][0]["status"]="BLOCKED"
        d["completed_percent"]=75
        d["remaining_percent"]=25
        d["remaining_total_completion_eta_hours"]=1.0
        with self.assertRaises(ValueError):
            validate_daily_progress(d)

if __name__ == "__main__":
    unittest.main()
