"""Focused offline tests for FlowPilot CSV report prototype."""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from flowpilot_csv_report import preview, execute, ReportRefused


class CsvReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for filename, rows in (("a.csv", [("alice", "1.25"), ("bob", "2")]),
                               ("b.csv", [("alice", "3.75")])):
            with (self.root / filename).open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["customer", "revenue"])
                w.writerows(rows)
        self.kw = dict(group="customer", amount="revenue")
        self.db = self.root / "audit.sqlite"

    def test_preview_never_creates_report(self):
        p = preview(self.root, ["a.csv", "b.csv"], "summary.csv", **self.kw)
        self.assertEqual(p["status"], "WAITING_EXECUTION_APPROVAL")
        self.assertFalse((self.root / "summary.csv").exists())

    def test_rejection_no_output(self):
        p = preview(self.root, ["a.csv"], "summary.csv", **self.kw)
        with self.assertRaises(ReportRefused):
            execute(self.root, p, approval="NO", audit_db=self.db)
        self.assertFalse((self.root / "summary.csv").exists())

    def test_decimal_report_and_trace(self):
        p = preview(self.root, ["a.csv", "b.csv"], "summary.csv", **self.kw)
        result = execute(self.root, p, approval="APPROVE_EXECUTION", audit_db=self.db)
        self.assertEqual(result["rows"], 3)
        with (self.root / "summary.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows, [["customer", "total_revenue"], ["alice", "5.00"], ["bob", "2"]])
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM flowpilot_runs").fetchone()[0], 1)

    def test_no_traversal_or_overwrite(self):
        with self.assertRaises(ReportRefused):
            preview(self.root, ["../outside.csv"], "summary.csv", **self.kw)
        with self.assertRaises(ReportRefused):
            preview(self.root, ["a.csv"], "a.csv", **self.kw)

    def test_plan_tampering_refused(self):
        p = preview(self.root, ["a.csv"], "summary.csv", **self.kw)
        p["operations"] = ["delete_files"]
        with self.assertRaises(ReportRefused):
            execute(self.root, p, approval="APPROVE_EXECUTION", audit_db=self.db)


if __name__ == "__main__":
    unittest.main()
