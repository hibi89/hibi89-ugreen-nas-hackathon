"""Offline tests for local audit history view."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from flowpilot_audit_view import recent_runs, AuditReadRefused


class AuditViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "audit.sqlite"
        with sqlite3.connect(self.db) as conn:
            conn.execute("CREATE TABLE flowpilot_runs (id INTEGER PRIMARY KEY, timestamp TEXT, record_json TEXT)")
            conn.execute("INSERT INTO flowpilot_runs(timestamp,record_json) VALUES (?,?)",
                         ("2026-10-29T00:00:00Z", '{"status":"LOCAL_REPORT_CREATED_NOT_NAS"}'))

    def test_read_history(self):
        result = recent_runs(self.db)
        self.assertEqual(result["count"], 1)
        self.assertFalse(result["sovia_integrated"])
        self.assertEqual(result["runs"][0]["record"]["status"], "LOCAL_REPORT_CREATED_NOT_NAS")

    def test_invalid_limit(self):
        with self.assertRaises(AuditReadRefused):
            recent_runs(self.db, limit=0)

    def test_missing_db_does_not_create(self):
        missing = self.db.parent / "missing.sqlite"
        with self.assertRaises(AuditReadRefused):
            recent_runs(missing)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
