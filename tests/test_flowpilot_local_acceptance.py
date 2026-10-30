"""Run all four public FlowPilot capabilities against disposable OS fixtures."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.flowpilot_local_acceptance import run_acceptance


class FourStageLocalAcceptance(unittest.TestCase):
    def test_four_actual_local_workflows_and_sqlite_receipt(self):
        result = run_acceptance()
        self.assertEqual(result["status"], "PASS_FOUR_LOCAL_CAPABILITY_CHECKS")
        self.assertEqual(result["passed"], 4)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(result["checks"]), 4)
        self.assertTrue(all(row["status"] == "PASS_SYNTHETIC"
                            for row in result["checks"]))
        self.assertFalse(result["user_files_read"])
        self.assertFalse(result["actual_nas_verified"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_acceptance_reports_no_private_data_or_owner_paths(self):
        result = json.dumps(run_acceptance(), ensure_ascii=False)
        for private in ("README.md", "month-a.csv", "month-b.csv",
                        "acceptance temporary test only", "/tmp/flowpilot"):
            self.assertNotIn(private, result)
        self.assertIn("actual_private_hae_la_executed", result)

    def test_cli_runs_from_unrelated_directory_without_private_repos(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "flowpilot_local_acceptance.py"
        with tempfile.TemporaryDirectory(prefix="ugreen-acceptance-cwd-") as tmp:
            run = subprocess.run(
                [sys.executable, str(script)], cwd=tmp,
                capture_output=True, text=True, timeout=45,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(run.stdout)
        self.assertEqual(data["passed"], 4)
        self.assertFalse(data["actual_nas_verified"])


if __name__ == "__main__":
    unittest.main()
