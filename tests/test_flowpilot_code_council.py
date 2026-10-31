"""G116 deterministic architect/security/builder/QA review, no Docker/NAS."""
import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_code_council import run_council, _review, _repair_missing_edge
from flowpilot_task_compiler import compile_goal


class G116CouncilTests(unittest.TestCase):
    def test_csv_roles_and_real_local_fixture_test(self):
        r = run_council("고객별 매출 보고서 만들어줘")
        self.assertEqual(r["status"], "OFFLINE_COUNCIL_REHEARSAL_PASS")
        self.assertEqual([s["role"] for s in r["trace"]],
                         ["Architect", "Security", "Builder", "QA"])
        self.assertEqual(r["test_evidence"]["observed_rows"][1], ["alice", "4.00"])
        self.assertFalse(r["container_sandbox_executed"])
        self.assertFalse(r["production_applied"])

    def test_missing_file_fixture_review(self):
        r = run_council("필수 파일 확인해줘")
        self.assertEqual(r["status"], "OFFLINE_COUNCIL_REHEARSAL_PASS")
        self.assertEqual(r["test_evidence"]["initial_states"], ["PRESENT", "MISSING"])
        self.assertEqual(r["test_evidence"]["repaired_states"], ["PRESENT", "PRESENT"])
        self.assertEqual(r["compiled_template"], "required_file_metadata_v1")

    def test_injected_edge_fault_is_diagnosed_fixed_and_retested(self):
        r = run_council("필수 파일 확인해줘", inject_test_fault=True)
        self.assertEqual(r["status"], "OFFLINE_COUNCIL_REHEARSAL_PASS")
        self.assertEqual(r["repair_count"], 1)
        self.assertEqual(r["trace"][0]["status"], "REJECTED")
        self.assertEqual(r["trace"][0]["reason"], "CANONICAL_PLAN_MISMATCH")
        self.assertEqual(r["trace"][2]["role"], "Repair")
        self.assertEqual(r["trace"][-1]["role"], "QA")
        self.assertFalse(r["multi_llm_agents_invoked"])

    def test_no_repairs_blocks_before_fixture(self):
        with patch("flowpilot_code_council.run_compiled", side_effect=AssertionError("MUST NOT RUN")):
            r = run_council("필수 파일 확인해줘", inject_test_fault=True, max_repairs=0)
        self.assertEqual(r["status"], "REVIEW_BLOCKED")
        self.assertFalse(r["fixture_executed"])

    def test_injected_fault_does_not_modify_original_compiler(self):
        original = compile_goal("필수 파일 확인해줘")
        run_council("필수 파일 확인해줘", inject_test_fault=True)
        self.assertEqual(compile_goal("필수 파일 확인해줘"), original)

    def test_cannot_self_heal_arbitrary_unsafe_operation(self):
        goal = "필수 파일 확인해줘"
        p = compile_goal(goal)
        evil = deepcopy(p)
        evil["steps"][0]["operation"] = "shell_exec"
        self.assertFalse(_review(goal, evil)[0])
        self.assertIsNone(_repair_missing_edge(goal, evil))
        evil2 = deepcopy(p)
        evil2["steps"][0]["runtime"] = "host_shell"
        self.assertFalse(_review(goal, evil2)[0])
        self.assertIsNone(_repair_missing_edge(goal, evil2))
        evil3 = deepcopy(p)
        evil3["steps"][0]["access"] = "DELETE"
        self.assertFalse(_review(goal, evil3)[0])

    def test_unknown_or_mixed_goal_fails_without_test_run(self):
        with patch("flowpilot_code_council.run_compiled", side_effect=AssertionError("MUST NOT RUN")):
            for goal in ("delete NAS files", "필수 파일 확인해줘 그리고 전송해줘",
                         "매일 파일들 동기화해줘"):
                with self.subTest(goal=goal):
                    r = run_council(goal)
                    self.assertEqual(r["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")
                    self.assertFalse(r["fixture_executed"])

    def test_repair_options_are_typed(self):
        for invalid in (True, -1, 2, "1"):
            with self.subTest(v=invalid), self.assertRaises(ValueError):
                run_council("필수 파일 확인해줘", max_repairs=invalid)
        with self.assertRaises(ValueError):
            run_council("필수 파일 확인해줘", inject_test_fault=1)

    def test_forged_qa_evidence_blocks(self):
        fake = {"status": "SYNTHETIC_LOCAL_REHEARSAL_PASS",
                "test_results": [{"status": "PASS"}],
                "actual_nas_verified": True, "owner_files_opened": False,
                "uliya_expert_invoked": False}
        with patch("flowpilot_code_council.run_compiled", return_value=fake):
            r = run_council("필수 파일 확인해줘")
        self.assertEqual(r["status"], "QA_BLOCKED")
        self.assertFalse(r["production_applied"])

    def test_cli_korean_output_is_ascii_safe(self):
        p = subprocess.run([sys.executable, str(ROOT/"tools"/"flowpilot_code_council.py"),
                            "--goal", "필수 파일 확인해줘", "--inject-test-fault"],
                           capture_output=True, text=True, timeout=25)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.isascii())
        result = json.loads(p.stdout)
        self.assertEqual(result["repair_count"], 1)
        self.assertFalse(result["docker_isolation_verified"])

    def test_cli_unsafe_goal_exit_one(self):
        p = subprocess.run([sys.executable, str(ROOT/"tools"/"flowpilot_code_council.py"),
                            "--goal", "NAS 파일 삭제해줘"],
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stdout)["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")


if __name__ == "__main__":
    unittest.main()
