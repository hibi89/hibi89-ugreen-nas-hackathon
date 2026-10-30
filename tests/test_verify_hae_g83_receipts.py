"""G83 local HAE acceptance proof gates; synthetic fixture, no native archive in CI."""
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_hae_la_local_e2e import (
    AcceptanceRefused, FIXTURE, validate_pending_identity, verify_business_receipts,
)

RUN = "Gui" + "b" * 12


class G83AcceptanceEvidenceTests(unittest.TestCase):
    def test_new_g82_runtime_gate_fails_on_old_preview(self):
        self.assertIsNone(validate_pending_identity({"pending_run_id": None}, require_g82=False))
        with self.assertRaisesRegex(AcceptanceRefused, "G82 pending run ID absent"):
            validate_pending_identity({"pending_run_id": None}, require_g82=True)
        self.assertEqual(validate_pending_identity({"pending_run_id": RUN}, require_g82=True), RUN)

    def test_reject_malformed_preview_run_identity(self):
        for invalid in ("wrong", 42, True, "Gui" + "b" * 13):
            with self.subTest(value=invalid), self.assertRaises(AcceptanceRefused):
                validate_pending_identity({"pending_run_id": invalid}, require_g82=True)

    def test_independent_sqlite_receipts_values_and_digest(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "business.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE csv_records (run_id TEXT, row_number INT,"
                           " source_sha256 TEXT, payload_json TEXT)")
                for row_num, name in ((1, "SyntheticAlice"), (2, "SyntheticBob")):
                    db.execute("INSERT INTO csv_records VALUES (?,?,?,?)",
                               (RUN, row_num, sha256(FIXTURE).hexdigest(),
                                json.dumps({"id": str(row_num + 10), "name": name})))
            self.assertTrue(verify_business_receipts(path, RUN))
            self.assertFalse(verify_business_receipts(path, "Gui" + "c" * 12))
            with sqlite3.connect(path) as db:
                db.execute("UPDATE csv_records SET source_sha256=? WHERE row_number=2",
                           ("0" * 64,))
            self.assertFalse(verify_business_receipts(path, RUN))

    def test_absent_and_wrong_schema_never_report_verified(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "missing.sqlite"
            self.assertFalse(verify_business_receipts(path, RUN))
            self.assertFalse(path.exists(), "Read-only verifier must not create database")
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE not_csv_records (unused INT)")
            self.assertFalse(verify_business_receipts(path, RUN))


if __name__ == "__main__":
    unittest.main()
