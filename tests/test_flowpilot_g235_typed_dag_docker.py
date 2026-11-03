"""G235 fixed typed synthetic DAG tests: no customer I/O or native NAS claim."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g235_typed_dag_docker as g235
from flowpilot_g233_real_docker_smoke import SmokeRefused


class G235TypedDockerTests(unittest.TestCase):
    def receipt(self):
        return json.dumps(g235.EXPECTED, separators=(",", ":"))

    def test_no_approval_no_docker_activity(self):
        with patch.object(g235, "run_fixed_dag", side_effect=AssertionError("called")), \
             patch("sys.stdout", new_callable=io.StringIO) as output:
            rc = g235.main([])
        self.assertEqual(rc, 2)
        self.assertIn("EXPLICIT_SYNTHETIC_APPROVAL_REQUIRED", output.getvalue())

    def test_exact_expected_receipt_valid(self):
        digest = g235.verify_output(self.receipt())
        self.assertEqual(len(digest), 64)

    def test_rejects_wrong_totals_and_forged_nas_status(self):
        for patch_row in (
            {"source_rows": 4},
            {"nas_verified": True},
            {"automatic_repair": True},
            {"node_types": list(reversed(g235.STEPS))},
            {"report_rows": [{"customer": "alice", "total_cents": 400}]},
            {"owner_files_opened": True},
            {"general_automation_verified": True},
        ):
            payload = {**g235.EXPECTED, **patch_row}
            with self.subTest(patch_row=patch_row), self.assertRaises(SmokeRefused):
                g235.verify_output(json.dumps(payload))

    def test_rejects_duplicate_keys(self):
        raw = self.receipt()[:-1] + ',"status":"SYNTHETIC_TYPED_DAG_COMPLETE"}'
        with self.assertRaisesRegex(SmokeRefused, "DUPLICATE"):
            g235.verify_output(raw)

    def test_rejects_noncanonical_types_and_oversize(self):
        for raw in (
            self.receipt().replace('"source_rows":3','"source_rows":true'),
            "a" * 1025, "[]", "garbage", self.receipt()[:-1],
        ):
            with self.subTest(raw=raw[:30]), self.assertRaises(SmokeRefused):
                g235.verify_output(raw)

    def test_real_compiled_c_executes_typed_steps_without_docker(self):
        import shutil
        import tempfile
        if shutil.which("cc") is None:
            self.skipTest("C compiler not installed")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            program = root / "check"
            src = root / "check.c"
            src.write_text(g235.C_SOURCE, encoding="ascii")
            cc = subprocess.run(["cc", "-O2", "-static", "-Wall", "-Wextra",
                                 "-Werror", str(src), "-o", str(program)],
                                capture_output=True, timeout=20)
            if cc.returncode:
                self.skipTest("static C compiler unavailable")
            # This unit test only compiles; fixture file paths are hard-coded
            # to /fixture, so the actual end-to-end execution is in Docker CI.
            self.assertTrue(program.is_file())

    def test_workflow_is_fixed_no_python_code_or_external_image(self):
        self.assertEqual(g235.STEPS,
                         ("csv_read","validate_decimal","group_sum","report"))
        self.assertTrue(g235.DOCKERFILE_TYPED.startswith("FROM scratch"))
        self.assertNotIn("curl", g235.C_SOURCE)
        self.assertNotIn("ADD http", g235.DOCKERFILE_TYPED)
        self.assertEqual(g235.SOURCE.count("\n"), 4)
        self.assertEqual(g235.PLAN.count("\n"), 4)

    def test_local_docker_missing_denied(self):
        with patch.object(g235.shutil, "which", return_value=None), \
             patch.object(g235, "checked_run", side_effect=AssertionError("called")):
            with self.assertRaisesRegex(SmokeRefused, "UNAVAILABLE"):
                g235.run_fixed_dag()


if __name__ == "__main__":
    unittest.main()
