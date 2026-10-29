"""Local E2E entrypoint integration tests. Run from tools/ on PYTHONPATH."""
import csv
import tempfile
import unittest
from pathlib import Path

from flowpilot_csv_e2e import run_session


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        with (self.root / "sales.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([["customer", "revenue"], ["alice", "1.25"], ["alice", "2.75"]])
        self.args = dict(goal="고객별 매출 보고서 만들어줘", root=self.root,
                         sources=["sales.csv"], output="summary.csv",
                         group="customer", amount="revenue")
        self.db = self.root / "audit.sqlite"

    def test_missing_slots(self):
        r = run_session("고객별 매출 보고서 만들어줘")
        self.assertEqual(r["status"], "WAITING_USER")
        self.assertFalse(r["executed"])

    def test_preview_does_not_write(self):
        r = run_session(**self.args)
        self.assertEqual(r["status"], "WAITING_EXECUTION_APPROVAL")
        self.assertEqual(r["la_compatibility"]["status"], "BLOCKED_MISSING_CAPABILITIES")
        self.assertFalse(r["la_compatibility"]["execution_allowed"])
        self.assertFalse((self.root / "summary.csv").exists())

    def test_decline_does_not_write(self):
        r = run_session(**self.args, approval="REJECT", audit_db=self.db)
        self.assertEqual(r["status"], "DECLINED")
        self.assertFalse((self.root / "summary.csv").exists())

    def test_approved_report_and_audit(self):
        r = run_session(**self.args, approval="APPROVE_EXECUTION", audit_db=self.db)
        self.assertTrue(r["executed"])
        self.assertEqual(r["audit"]["count"], 1)
        self.assertFalse(r["nas_verified"])
        self.assertFalse(r["la_compatibility"]["actual_la_engine_invoked"])
        with (self.root / "summary.csv").open(encoding="utf-8", newline="") as f:
            self.assertEqual(list(csv.reader(f))[1], ["alice", "4.00"])


if __name__ == "__main__":
    unittest.main()
