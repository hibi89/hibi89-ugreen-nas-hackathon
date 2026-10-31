"""G114 synthetic full vertical build/test/guide checks (no NAS)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_builder_rehearsal import rehearse


class WorkflowBuilderRehearsalTests(unittest.TestCase):
    def test_korean_goal_executes_and_tests_synthetic_csv(self):
        value = rehearse("고객별 매출 보고서 만들어줘")
        self.assertEqual(value["status"], "SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertEqual(value["test_evidence"]["sqlite_audit_rows"], 1)
        self.assertEqual(value["test_evidence"]["observed_rows"][1], ["alice", "4.00"])
        self.assertEqual(len(value["verified_steps"]), 6)
        self.assertFalse(value["actual_nas_verified"])
        self.assertFalse(value["owner_files_opened"])

    def test_english_goal_also_works(self):
        value = rehearse("create customer revenue summary")
        self.assertTrue(value["test_evidence"]["invalid_input_refused"])
        self.assertTrue(value["test_evidence"]["duplicate_output_refused"])
        self.assertEqual([n["type"] for n in value["workflow_graph"]["nodes"]],
                         ["csv_read", "decimal_group_sum", "csv_write_new", "sqlite_audit"])

    def test_stepwise_manual_runbook_keeps_real_nas_unverified(self):
        guide = rehearse("고객별 매출 보고서 만들어줘")["operator_runbook_markdown"]
        for part in ("Python 3.11", "--approval APPROVE_EXECUTION", "audit.sqlite",
                     "NOT validated", "separate owner consent"):
            self.assertIn(part, guide)

    def test_unsafe_and_unsupported_tasks_do_not_run(self):
        for request in ("delete everything", "모든 파일 지워줘",
                        "매일 들어오는 CSV를 자동으로 예약 처리해줘", "", " ",
                        "고객별 매출 보고서 만들어줘\nrm -rf /"):
            with self.subTest(request=request):
                value = rehearse(request)
                self.assertEqual(value["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")
                self.assertFalse(value["executed"])

    def test_cli_prints_runbook_and_trust_flags(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "flowpilot_builder_rehearsal.py"),
                               "--goal", "create customer revenue summary"],
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertTrue(value["operator_runbook_markdown"].startswith("# FlowPilot"))
        self.assertFalse(value["uliya_expert_invoked"])
        self.assertEqual(value["release_gate"], "HOLD")

    def test_cli_refuses_unimplemented_daily_scheduling(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "flowpilot_builder_rehearsal.py"),
                               "--goal", "매일 CSV 예약 작업 만들어줘"],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")


if __name__ == "__main__":
    unittest.main()
