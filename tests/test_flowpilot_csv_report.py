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

    def test_audit_database_failure_rolls_back_newly_created_csv(self):
        from unittest.mock import patch
        p = preview(self.root, ["a.csv", "b.csv"], "summary.csv", **self.kw)
        with patch("flowpilot_csv_report.sqlite3.connect",
                   side_effect=sqlite3.OperationalError("audit unavailable")):
            with self.assertRaisesRegex(ReportRefused, "LOCAL_CSV_OUTPUT_OR_AUDIT_FAILED"):
                execute(self.root, p, approval="APPROVE_EXECUTION", audit_db=self.db)
        self.assertFalse((self.root / "summary.csv").exists())
        self.assertEqual((self.root / "a.csv").read_text().splitlines()[0],
                         "customer,revenue")

    def test_audit_failure_does_not_delete_a_competing_replacement(self):
        from unittest.mock import patch
        import os
        out = self.root / "summary.csv"
        foreign = self.root / "other-owner.csv"
        foreign.write_bytes(b"OWNED-BY-ANOTHER-PROCESS")
        real_connect = sqlite3.connect
        def replace_and_fail(*args, **kwargs):
            os.replace(foreign, out)
            raise sqlite3.OperationalError("injected audit error")
        p = preview(self.root, ["a.csv", "b.csv"], "summary.csv", **self.kw)
        with patch("flowpilot_csv_report.sqlite3.connect", side_effect=replace_and_fail):
            with self.assertRaises(ReportRefused):
                execute(self.root, p, approval="APPROVE_EXECUTION", audit_db=self.db)
        self.assertEqual(out.read_bytes(), b"OWNED-BY-ANOTHER-PROCESS")

    def test_report_csv_writer_failure_rolls_back_partial_output(self):
        from unittest.mock import patch
        p = preview(self.root, ["a.csv", "b.csv"], "summary.csv", **self.kw)
        class BrokenWriter:
            def writerow(self, row):
                raise OSError("injected writing error")
        with patch("flowpilot_csv_report.csv.writer", return_value=BrokenWriter()):
            with self.assertRaises(ReportRefused):
                execute(self.root, p, approval="APPROVE_EXECUTION", audit_db=self.db)
        self.assertFalse((self.root / "summary.csv").exists())

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
