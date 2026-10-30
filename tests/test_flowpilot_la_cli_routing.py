"""G73: one explicit CLI front door for local reports vs synthetic LA v0.

All LA execution assertions here inject a fake backend; the independent native
LA runtime acceptance lives in test_flowpilot_la_installed_runtime.py and is
SKIPPED unless the real private package is available.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from flowpilot_csv_e2e import LA_SYNTHETIC_GOALS, main, run_session
from flowpilot_csv_report import ReportRefused
from flowpilot_la_synthetic_import import APPROVAL


class G73BackendRoutingTests(unittest.TestCase):
    def test_synthetic_goal_preview_must_be_read_only(self):
        for goal in LA_SYNTHETIC_GOALS:
            with self.subTest(goal=goal):
                with patch("flowpilot_la_synthetic_import.run_demo", return_value={
                    "status": "WAITING_EXECUTION_APPROVAL",
                    "la_execution_verified": False,
                }) as backend:
                    result = run_session(goal, backend="la-synthetic-import")
                backend.assert_called_once_with(approval=None)
                self.assertEqual(result["status"], "WAITING_EXECUTION_APPROVAL")
                self.assertFalse(result["executed"])
                self.assertFalse(result["nas_verified"])
                self.assertFalse(result["actual_la_full_graph_integrated"])

    def test_unsupported_goal_fails_before_la_import(self):
        for goal in ("delete all NAS files", "고객별 매출 보고서 만들어줘",
                     "../private", "shell exec", "", {}, None):
            with self.subTest(goal=goal):
                with patch("flowpilot_la_synthetic_import.run_demo",
                           side_effect=AssertionError("should not run")):
                    with self.assertRaises(ReportRefused):
                        run_session(goal, backend="la-synthetic-import")

    def test_la_mode_refuses_any_owner_path_or_fields(self):
        args = {
            "root": Path("/tmp"), "sources": ["sales.csv"],
            "output": "out.csv", "group": "customer", "amount": "revenue",
            "audit_db": Path("audit.sqlite"),
        }
        for field, value in args.items():
            with self.subTest(field=field):
                with patch("flowpilot_la_synthetic_import.run_demo",
                           side_effect=AssertionError("should not run")):
                    with self.assertRaises(ReportRefused):
                        run_session("import synthetic sales csv to local sqlite",
                                    backend="la-synthetic-import", **{field: value})

    def test_valid_approval_is_forwarded_without_modification(self):
        fake = {
            "status": "SYNTHETIC_LA_SQLITE_VERIFIED",
            "la_execution_verified": True,
            "persisted_rows": 2,
            "uliya_or_nas_called": False,
        }
        with patch("flowpilot_la_synthetic_import.run_demo", return_value=fake) as backend:
            result = run_session("합성 매출 CSV를 SQLite로 가져와줘",
                                 backend="la-synthetic-import", approval=APPROVAL)
        backend.assert_called_once_with(approval=APPROVAL)
        self.assertTrue(result["executed"])
        self.assertFalse(result["actual_la_full_graph_integrated"])
        self.assertEqual(result["persisted_rows"], 2)

    def test_blocked_installed_backend_returns_nonzero_cli(self):
        goal = "import synthetic sales csv to local sqlite"
        with patch("flowpilot_la_synthetic_import.run_demo", return_value={
            "status": "BLOCKED_RUNTIME_UNAVAILABLE", "la_execution_verified": False,
        }):
            output = StringIO()
            with redirect_stdout(output):
                code = main(["--goal", goal, "--backend", "la-synthetic-import",
                             "--approval", APPROVAL])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_RUNTIME_UNAVAILABLE")

    def test_approved_native_return_requires_actual_verified_flag(self):
        goal = "import synthetic sales csv to local sqlite"
        with patch("flowpilot_la_synthetic_import.run_demo", return_value={
            "status": "BLOCKED_RECEIPT_MISMATCH", "la_execution_verified": False,
        }):
            result = run_session(goal, backend="la-synthetic-import", approval=APPROVAL)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_MISMATCH")
        self.assertFalse(result["executed"])

    def test_unknown_backend_refused_without_import(self):
        with self.assertRaises(ReportRefused):
            run_session("import synthetic sales csv to local sqlite", backend="auto")

    def test_cli_real_preview_and_rejection_are_side_effect_free(self):
        goal = "import synthetic sales csv to local sqlite"
        root = Path(__file__).resolve().parents[1]
        for args, expected in (([], "WAITING_EXECUTION_APPROVAL"),
                               (["--approval", "REJECT"], "DECLINED")):
            with self.subTest(expected=expected):
                proc = subprocess.run(
                    [sys.executable, str(TOOLS / "flowpilot_csv_e2e.py"),
                     "--goal", goal, "--backend", "la-synthetic-import", *args],
                    cwd=root, capture_output=True, text=True, timeout=12)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                result = json.loads(proc.stdout)
                self.assertEqual(result["status"], expected)
                self.assertFalse(result["executed"])
                self.assertFalse(result["nas_verified"])

    def test_local_csv_default_remains_unchanged(self):
        result = run_session("고객별 매출 보고서 만들어줘")
        self.assertEqual(result["status"], "WAITING_USER")
        self.assertFalse(result["executed"])


if __name__ == "__main__":
    unittest.main()
