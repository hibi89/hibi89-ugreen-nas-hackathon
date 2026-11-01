"""G167 executable safety/preflight regression (temporary SQLite + HTTP only)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from flowpilot_g167_local_preflight import run_preflight


class G167PreflightTests(unittest.TestCase):
    def test_actual_ephemeral_loopback_http_and_sqlite_acceptance(self):
        result = run_preflight()
        self.assertEqual(result["status"], "LOCAL_SYNTHETIC_ACCEPTANCE_PASS_NOT_NAS")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["real_browser_verified"])
        self.assertFalse(result["real_nas_verified"])
        self.assertFalse(result["trial_started"])
        expected = {
            "AUTH_DENIED", "ORIGIN_DENIED", "HEALTH", "ASSET_dashboard",
            "ASSET_dashboard.css", "ASSET_dashboard.js", "CREATE", "PLAN",
            "COUNCIL", "NAS_APPROVAL_DENIED", "SYNTHETIC_APPROVED",
            "SYNTHETIC_RUN", "IDEMPOTENT_RUN", "AUDIT", "EVIDENCE",
            "CSV_SHA", "METADATA_PREVIEW", "METADATA_WRONG_ACK_DENIED",
            "METADATA_APPROVED_ONCE", "METADATA_REPLAY_DENIED",
            "SQLITE_RESTART_READBACK",
        }
        self.assertTrue(expected.issubset(set(result["verified_cases"])))
        self.assertEqual(result["checks"], len(result["verified_cases"]))
        self.assertNotIn("secret", json.dumps(result).lower())

    def test_windows_launcher_source_guards_entire_checkout(self):
        text = (ROOT / "tools" / "start_g166_local.ps1").read_text(encoding="utf-8")
        self.assertIn("outside the GitHub checkout", text)
        self.assertIn("OrdinalIgnoreCase", text)
        self.assertIn("DriveType]::Network", text)
        self.assertIn("DB parent directory must exist", text)
        self.assertIn("Remove-Item Env:FLOWPILOT_LOCAL_API_TOKEN", text)

    @unittest.skipUnless(os.name == "nt", "PowerShell 5.1 live refusal only on Windows")
    def test_windows_launcher_cannot_initialize_db_inside_checkout(self):
        shell = shutil.which("powershell.exe")
        if not shell:
            self.skipTest("Windows PowerShell unavailable")
        # Must refuse BEFORE generating/printing auth token or invoking Python.
        not_a_real_db = ROOT / "tools" / "g167-denied-checkout.sqlite"
        self.assertFalse(not_a_real_db.exists())
        command = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(ROOT / "tools" / "start_g166_local.ps1"),
                   "-Db", str(not_a_real_db), "-InitNewDb"]
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=15, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the GitHub checkout", result.stdout + result.stderr)
        self.assertFalse(not_a_real_db.exists())
        self.assertNotIn("Local-only API token", result.stdout)


if __name__ == "__main__":
    unittest.main()
