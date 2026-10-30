"""Actual CSV aggregation, SHA-verified receipt and SQLite audit tests."""
from __future__ import annotations
import csv
import hashlib
from io import StringIO
import unittest
from tools.flowpilot_synthetic_csv_panel import CSVPanel, CSVPanelRefused


class RealGeneratedCSVTests(unittest.TestCase):
    def setUp(self):
        self.c = CSVPanel()
        self.addCleanup(self.c.close)

    def test_real_csv_rows_audit_receipt_and_report_digest(self):
        preview = self.c.configure({"output": "summary.csv"})
        self.assertEqual(preview["status"], "WAITING_EXECUTION_APPROVAL")
        self.assertFalse(preview["csv_created"])
        with self.assertRaises(ValueError):
            self.c.report()
        result = self.c.action("approve")
        self.assertEqual(result["status"], "LOCAL_REPORT_CREATED_NOT_NAS")
        self.assertTrue(result["audit_recorded"])
        self.assertFalse(result["nas_verified"])
        content = self.c.report()
        self.assertEqual(hashlib.sha256(content).hexdigest(),
                         result["report_sha256"])
        rows = list(csv.DictReader(StringIO(content.decode("utf-8"))))
        self.assertEqual(list(rows[0]), ["customer", "total_revenue"])
        self.assertEqual(
            {(r["customer"], r["total_revenue"]) for r in rows},
            {("alice", "5.00"), ("bob", "6.00")},
        )
        with self.assertRaises(ValueError):
            self.c.action("approve")

    def test_reject_keeps_output_uncreated(self):
        self.c.configure({"output": "summary.csv"})
        decline = self.c.action("reject")
        self.assertEqual(decline["status"], "DECLINED")
        self.assertFalse(decline["csv_created"])
        with self.assertRaises(ValueError):
            self.c.report()
        self.assertTrue(
            self.c.configure({"output": "monthly-summary.csv"})[
                "workflow_preview_ready"]
        )

    def test_no_implicit_write_approval(self):
        with self.assertRaises(ValueError):
            self.c.action("approve")

    def test_only_fixed_generated_names_allowed(self):
        for value in ("../customer.csv", "C:\\private.csv", "", "foo.csv"):
            with self.subTest(value=value), self.assertRaises(CSVPanelRefused):
                self.c.configure({"output": value})

    def test_no_owner_paths_in_report(self):
        value = self.c.configure({"output": "summary.csv"})
        self.assertNotIn(str(self.c._engine.root), str(value))
        self.assertTrue(value["generated_only"])

    def test_closed_demo_refuses_operations(self):
        self.c.close()
        with self.assertRaises(CSVPanelRefused):
            self.c.configure({"output": "summary.csv"})


if __name__ == "__main__":
    unittest.main()
