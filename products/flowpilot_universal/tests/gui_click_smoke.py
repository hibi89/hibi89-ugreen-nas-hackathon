"""Real Tk smoke using synthetic files. Run via xvfb-run on Ubuntu CI."""
from contextlib import closing
import json
import sqlite3
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from flowpilot_universal.gui import App
from flowpilot_universal.session import HISTORY_FILE


class DesktopGUIAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "업무 납품 파일"
        self.output = self.base / "보고 기록"
        self.source.mkdir()
        self.output.mkdir()
        self.manifest = self.base / "검수조건.json"
        (self.source / "납품원본.txt").write_bytes(b"immutable-delivery")
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "expected_files": [{"path": "납품원본.txt"}]
        }, ensure_ascii=False), encoding="utf-8")
        self.window = tk.Tk()
        self.window.withdraw()
        self.addCleanup(self.window.destroy)
        self.app = App(self.window)
        self.app.root.set(str(self.source))
        self.app.manifest.set(str(self.manifest))
        self.app.output.set(str(self.output))

    def test_real_tk_consent_scan_history_backup(self):
        with patch("flowpilot_universal.gui.messagebox.showerror") as show_error:
            self.app.start()
            show_error.assert_called_once()
            self.assertEqual(list(self.output.iterdir()), [])
        self.app.consent.set(True)
        self.app.start()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            self.window.update()
            if self.app.worker and not self.app.worker.is_alive() and self.app.events.empty():
                self.window.update()
                break
            time.sleep(0.03)
        self.assertTrue(self.app.status.get().startswith("READY"), self.app.status.get())
        self.assertGreaterEqual(self.app.history.size(), 1)
        self.assertTrue((self.output / HISTORY_FILE).is_file())
        self.assertEqual((self.source / "납품원본.txt").read_bytes(), b"immutable-delivery")
        with closing(sqlite3.connect(self.output / HISTORY_FILE)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM scans").fetchone()[0], 1)
        with patch("flowpilot_universal.gui.messagebox.showinfo") as show_info:
            self.app.backup()
            show_info.assert_called_once()
        self.assertEqual(len(list(self.output.glob("flowpilot-history-backup-*.sqlite3"))), 1)
        # Recheck must create a distinct report; no stale hashes or overwritten files.
        first_reports = set(self.output.glob("flowpilot-*.json"))
        self.app.start()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            self.window.update()
            if self.app.worker and not self.app.worker.is_alive() and self.app.events.empty():
                self.window.update()
                break
            time.sleep(0.03)
        self.assertEqual(len(list(self.output.glob("flowpilot-*.json"))), len(first_reports) + 1)
        self.assertGreaterEqual(self.app.history.size(), 2)


if __name__ == "__main__":
    unittest.main()
