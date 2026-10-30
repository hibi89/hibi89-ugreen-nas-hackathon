"""Real run from outside checkout without private repositories or NAS."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OneClickDemoEntrypointTests(unittest.TestCase):
    def test_real_os_demo_check_exits_pass_without_private_clone(self):
        script = ROOT / "tools" / "flowpilot_four_source_local_ui.py"
        with tempfile.TemporaryDirectory(prefix="ugreen-foreign-cwd-") as tmp:
            proc = subprocess.run(
                [sys.executable, str(script), "--demo-check"],
                cwd=tmp, capture_output=True, text=True, timeout=25,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        row = json.loads(proc.stdout)
        self.assertEqual(row["status"], "PASS_REAL_OS_LSTAT_SYNTHETIC_DEMO")
        self.assertEqual(row["scenario_count"], 5)
        self.assertTrue(row["all_test_fixtures_disposed"])
        self.assertFalse(row["private_hae_executed"])
        self.assertFalse(row["actual_nas_verified"])
        self.assertNotIn("README.md", proc.stdout)

    def test_template_keeps_windows_placeholders_and_js_newline_regex(self):
        from tools.flowpilot_four_source_local_ui import HTML
        self.assertIn(r"C:\Users", HTML)
        self.assertIn(r"value.split(/\r?\n/)", HTML)
        self.assertIn("ownerLocalOnly", HTML)
        self.assertIn("LOCAL FILE METADATA ONLY", HTML)

    def test_browser_utility_startup_has_no_required_private_root_flags(self):
        script = ROOT / "tools" / "flowpilot_four_source_local_ui.py"
        with tempfile.TemporaryDirectory(prefix="ugreen-demo-help-") as tmp:
            proc = subprocess.run(
                [sys.executable, str(script), "--help"],
                cwd=tmp, capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--open-browser", proc.stdout)
        self.assertIn("--demo-check", proc.stdout)
        self.assertNotIn("required: --hae-root", proc.stdout)

    def test_windows_double_click_cmd_starts_only_loopback_python_server(self):
        script = (ROOT / "tools" / "START_FLOWPILOT_DEMO.cmd").read_text()
        self.assertIn("%~dp0flowpilot_four_source_local_ui.py", script)
        self.assertIn("--open-browser", script)
        self.assertIn("py -3.11", script)
        self.assertNotIn("https://", script)
        self.assertNotIn("--approve-disposable-synthetic", script)


if __name__ == "__main__":
    unittest.main()
