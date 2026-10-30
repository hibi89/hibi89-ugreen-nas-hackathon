"""Real owner-selected CSV file content (local temp fixtures only)."""
from __future__ import annotations

import csv
from io import StringIO
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.flowpilot_owner_csv import OwnerCSV, OwnerCSVRefused, CONSENT


class LocalOwnerCSVTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="ugreen-local-owner-csv-tests-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name, amount in (("january.csv", "3.50"), ("february.csv", "4.25")):
            (self.root / name).write_text(
                "customer,revenue\nalice," + amount + "\n", encoding="utf-8"
            )
        self.owner = OwnerCSV()
        self.addCleanup(self.owner.close)

    def scope(self):
        return {
            "root": str(self.root), "sources": ["january.csv", "february.csv"],
            "output": "new-report.csv", "group": "customer", "amount": "revenue",
            "local_metadata_ack": True,
        }

    def test_real_owner_csv_plan_execute_sqlite_and_digest_download(self):
        row = self.owner.preview(self.scope())
        self.assertFalse(row["source_contents_read"])
        self.assertFalse((self.root / "new-report.csv").exists())
        result = self.owner.execute(row["approval_token"], CONSENT)
        self.assertTrue(result["audit_recorded"])
        self.assertEqual(result["rows_read"], 2)
        self.assertEqual(result["groups_written"], 1)
        self.assertFalse(result["actual_nas_verified"])
        report = self.owner.download()
        self.assertEqual(hashlib.sha256(report).hexdigest(),
                         result["report_sha256"])
        table = list(csv.DictReader(StringIO(report.decode("utf-8"))))
        self.assertEqual(table, [{"customer": "alice", "total_revenue": "7.75"}])
        self.assertNotIn(str(self.root), str(result))
        self.assertNotIn("alice", str(result))

    def test_approval_cannot_be_replayed(self):
        p = self.owner.preview(self.scope())
        with self.assertRaises(OwnerCSVRefused):
            self.owner.execute(p["approval_token"], "DECLINED")
        self.owner.execute(p["approval_token"], CONSENT)
        with self.assertRaisesRegex(OwnerCSVRefused, "NO_PENDING_CSV_APPROVAL"):
            self.owner.execute(p["approval_token"], CONSENT)

    def test_source_changed_after_preview_refuses_before_output(self):
        p = self.owner.preview(self.scope())
        (self.root / "january.csv").write_text("customer,revenue\nalice,999.00\n")
        with self.assertRaisesRegex(OwnerCSVRefused, "SOURCE_CHANGED_AFTER_PREVIEW"):
            self.owner.execute(p["approval_token"], CONSENT)
        self.assertFalse((self.root / "new-report.csv").exists())

    def test_output_exists_cannot_overwrite(self):
        p = self.owner.preview(self.scope())
        (self.root / "new-report.csv").write_text("preexisting")
        with self.assertRaisesRegex(OwnerCSVRefused, "OUTPUT_WOULD_OVERWRITE"):
            self.owner.execute(p["approval_token"], CONSENT)
        self.assertEqual((self.root / "new-report.csv").read_text(), "preexisting")

    def test_cancel_requires_repreview_without_writes(self):
        p = self.owner.preview(self.scope())
        self.assertEqual(self.owner.cancel()["status"], "LOCAL_CSV_PLAN_CANCELLED")
        with self.assertRaises(OwnerCSVRefused):
            self.owner.execute(p["approval_token"], CONSENT)
        self.assertFalse((self.root / "new-report.csv").exists())
        self.assertEqual(self.owner.preview(self.scope())["source_count"], 2)

    def test_modified_output_refuses_download(self):
        p = self.owner.preview(self.scope())
        self.owner.execute(p["approval_token"], CONSENT)
        (self.root / "new-report.csv").write_bytes(b"malicious replacement")
        with self.assertRaisesRegex(OwnerCSVRefused, "CSV_OUTPUT_MODIFIED"):
            self.owner.download()

    def test_root_must_be_explicitly_acknowledged_and_basename_only(self):
        invalid = [
            {**self.scope(), "local_metadata_ack": False},
            {**self.scope(), "sources": ["../private.csv"]},
            {**self.scope(), "output": "../report.csv"},
            {**self.scope(), "output": "january.csv"},
            {**self.scope(), "sources": ["january.csv", "january.csv"]},
        ]
        for req in invalid:
            with self.subTest(request=list(req)), self.assertRaises(OwnerCSVRefused):
                self.owner.preview(req)

    def test_unapproved_download_refused(self):
        self.owner.preview(self.scope())
        with self.assertRaisesRegex(OwnerCSVRefused, "NO_APPROVED_CSV_OUTPUT"):
            self.owner.download()


if __name__ == "__main__":
    unittest.main()
