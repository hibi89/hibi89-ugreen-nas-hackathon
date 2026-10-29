"""Bounded goal-to-CSV report integration tests (local only)."""
import csv
import tempfile
import unittest
from pathlib import Path
from flowpilot_csv_goal_bridge import plan_request, run_approved_request
from flowpilot_csv_report import ReportRefused


class GoalBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        with (self.root / "sales.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([["customer", "revenue"], ["A", "1.50"], ["A", "2.25"]])
        self.kw = dict(root=self.root, sources=["sales.csv"], output="summary.csv",
                       group="customer", amount="revenue")

    def test_missing_slots_does_not_access_files(self):
        r = plan_request("고객별 매출 보고서 만들어줘")
        self.assertEqual(r["status"], "WAITING_USER")
        self.assertEqual(len(r["missing_inputs"]), 5)

    def test_unsupported_goal_refused(self):
        with self.assertRaises(ReportRefused):
            plan_request("delete all files", **self.kw)

    def test_rejection_preserves_sources(self):
        r = plan_request("고객별 매출 보고서 만들어줘", **self.kw)
        declined = run_approved_request(r, root=self.root, approval="REJECT",
                                        audit_db=self.root / "audit.db")
        self.assertEqual(declined["status"], "DECLINED")
        self.assertFalse((self.root / "summary.csv").exists())

    def test_approved_end_to_end(self):
        r = plan_request("고객별 매출 보고서 만들어줘", **self.kw)
        done = run_approved_request(r, root=self.root, approval="APPROVE_EXECUTION",
                                    audit_db=self.root / "audit.db")
        self.assertTrue(done["executed"])
        with (self.root / "summary.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[1], ["A", "3.75"])


if __name__ == "__main__":
    unittest.main()
