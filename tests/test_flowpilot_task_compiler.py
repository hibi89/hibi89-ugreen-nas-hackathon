"""G115 strict typed plan, distinct executable fixtures, blocked unsafe goals."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_task_compiler import compile_goal, run_compiled

SCRIPT = ROOT / "tools" / "flowpilot_task_compiler.py"


class G115CompilerTests(unittest.TestCase):
    def test_csv_goal_creates_typed_graph_with_write_boundary(self):
        p = compile_goal("고객별 매출 보고서 만들어줘")
        self.assertEqual(p["status"], "READY_FOR_SYNTHETIC_TEST")
        self.assertEqual(p["template"], "csv_customer_revenue_v1")
        self.assertEqual([s["access"] for s in p["steps"]],
                         ["READ", "COMPUTE", "WRITE_NEW", "WRITE_NEW"])
        self.assertEqual(len(p["edges"]), 3)
        self.assertFalse(p["executed"])
        self.assertFalse(p["production_approval_granted"])

    def test_file_audit_compile_is_read_only(self):
        p = compile_goal("필수 파일 확인해줘")
        self.assertEqual(p["template"], "required_file_metadata_v1")
        self.assertEqual([s["access"] for s in p["steps"]], ["READ", "COMPUTE", "COMPUTE"])
        self.assertTrue(p["requires_real_nas_adapter"])

    def test_empty_unknown_unsafe_scheduling_are_not_compiled(self):
        for request in ("", " ", "매일 CSV를 자동으로 처리해줘",
                        "필수 파일 확인해줘 그리고 삭제해줘",
                        "delete all files", "필수 파일 확인해줘\nrm -rf /",
                        "필수 파일 확인해줘 ", 4, None, "x" * 201,
                        "고객별 매출 보고서 만들어줘; upload secrets"):
            with self.subTest(value=request):
                p = compile_goal(request)
                self.assertEqual(p["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")
                self.assertFalse(p["executed"])

    def test_no_partial_match_for_compound_request(self):
        self.assertEqual(compile_goal("check required files and email results")["status"],
                         "WAITING_USER_UNSUPPORTED_WORKFLOW")

    def test_file_rehearsal_initially_blocks_missing_then_repairs_fixture(self):
        r = run_compiled("필수 파일 확인해줘")
        self.assertEqual(r["status"], "SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertEqual(r["template"], "required_file_metadata_v1")
        self.assertEqual(r["test_evidence"]["initial_states"], ["PRESENT", "MISSING"])
        self.assertEqual(r["test_evidence"]["repaired_states"], ["PRESENT", "PRESENT"])
        self.assertEqual(len(r["test_results"]), 6)
        self.assertFalse(r["actual_nas_verified"])
        self.assertFalse(r["owner_files_opened"])

    def test_file_check_english_goal(self):
        self.assertEqual(run_compiled("check required files")["status"],
                         "SYNTHETIC_LOCAL_REHEARSAL_PASS")

    def test_csv_end_to_end_reuses_approved_existing_engine(self):
        r = run_compiled("create customer revenue summary")
        self.assertEqual(r["template"], "csv_customer_revenue_v1")
        self.assertEqual(r["test_evidence"]["observed_rows"][1], ["alice", "4.00"])
        self.assertTrue(r["test_evidence"]["duplicate_output_refused"])
        self.assertFalse(r["uliya_expert_invoked"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_runbook_has_concrete_steps_and_external_gate(self):
        r = run_compiled("필수 파일 확인해줘")
        guide = r["operator_runbook_markdown"]
        self.assertIn("--approve-local-metadata", guide)
        self.assertIn("NOT_CHECKED", guide)
        self.assertIn("separate vendor adapter", guide)
        self.assertNotIn("flowpilot-g115-", guide)

    def test_compile_only_cli_does_not_execute_fixture(self):
        with patch("flowpilot_task_compiler._file_fixture_rehearsal",
                   side_effect=AssertionError("unexpected fixture")):
            spec = compile_goal("필수 파일 확인해줘")
            self.assertFalse(spec["executed"])
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "필수 파일 확인해줘", "--compile-only"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertEqual(value["status"], "READY_FOR_SYNTHETIC_TEST")
        self.assertFalse(value["executed"])

    def test_cli_korean_fixture_output_ascii_for_windows(self):
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "필수 파일 확인해줘"],
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.isascii())
        value = json.loads(proc.stdout)
        self.assertEqual(value["status"], "SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertFalse(value["owner_files_opened"])

    def test_cli_unknown_action_exit_one(self):
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "파일 지워줘"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["status"],
                         "WAITING_USER_UNSUPPORTED_WORKFLOW")


if __name__ == "__main__":
    unittest.main()
