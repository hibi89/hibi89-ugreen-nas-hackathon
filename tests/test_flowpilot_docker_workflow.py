"""G146 scoped Docker workflow: local fixture E2E + mocked real-host boundary."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import flowpilot_docker_workflow as g146

GOAL = "고객별 매출 보고서 만들어줘"
IMAGE = "docker.io/library/python@sha256:" + "a" * 64


class G146RealSandboxTests(unittest.TestCase):
    def test_fixed_code_full_csv_and_sqlite_fixture_runs_as_actual_python_subprocess(self):
        proc = subprocess.run([sys.executable, "-I", "-B", "-c", g146._WORKFLOW_SCRIPT],
                              capture_output=True, text=True, timeout=12)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(proc.stderr.strip())
        data = json.loads(proc.stdout)
        self.assertEqual(data, g146._EXPECTED)
        self.assertTrue(data["source_unchanged"])
        self.assertEqual(data["repair_count"], 1)

    def test_builds_known_isolation_args_and_forbids_unknown_template(self):
        p = g146.plan_workflow(GOAL, IMAGE)
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")
        argv = p["argv"]
        for arg in ("--host=unix:///var/run/docker.sock", "--network=none",
                    "--read-only", "--cap-drop=ALL", "--pull=never",
                    "--security-opt=no-new-privileges", "--user=65534:65534",
                    "--tmpfs=/tmp:rw,noexec,nosuid,size=16m"):
            self.assertIn(arg, argv)
        for arg in ("--privileged", "-v", "--mount", "--network=host"):
            self.assertNotIn(arg, argv)
        self.assertEqual(argv[-1], g146._WORKFLOW_SCRIPT)
        self.assertEqual(g146.plan_workflow("필수 파일 확인해줘", IMAGE)["status"],
                         "UNSUPPORTED_WORKFLOW_TEMPLATE")

    def test_no_user_approval_no_docker_or_socket_checks(self):
        with patch("flowpilot_docker_workflow.shutil.which",
                   side_effect=AssertionError("docker consulted")):
            data = g146.run_workflow(GOAL, IMAGE)
        self.assertEqual(data["status"], "WAITING_LOCAL_DOCKER_APPROVAL")
        self.assertNotIn("argv", data)
        self.assertFalse(data["docker_launched"])

    def test_invalid_image_and_unsafe_goal_refused(self):
        for goal, image in ((GOAL, "python:3.11-alpine"), ("delete NAS", IMAGE),
                            (GOAL, IMAGE+" --privileged"), (GOAL, "")):
            with self.subTest(goal=goal, image=image):
                self.assertEqual(g146.run_workflow(goal, image, approved=True)["status"],
                                 "INVALID_OR_UNSUPPORTED_PLAN")

    def test_no_docker_installed_denies_without_execution(self):
        with patch("flowpilot_docker_workflow.shutil.which", return_value=None), \
             patch("flowpilot_docker_workflow.subprocess.run",
                   side_effect=AssertionError("spawned")):
            row = g146.run_workflow(GOAL, IMAGE, approved=True)
        self.assertEqual(row["status"], "LOCAL_DOCKER_NOT_AVAILABLE")

    def test_real_runner_receipt_exact_mock_boundary(self):
        success = subprocess.CompletedProcess([], 0,
                 stdout=json.dumps(g146._EXPECTED, sort_keys=True), stderr="")
        with patch("flowpilot_docker_workflow.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_docker_workflow._local_socket_ready", return_value=True), \
             patch("flowpilot_docker_workflow.subprocess.run", return_value=success) as invoke:
            row = g146.run_workflow(GOAL, IMAGE, approved=True)
        self.assertEqual(row["status"], "LOCAL_DOCKER_SYNTHETIC_REPAIR_WORKFLOW_PASS")
        self.assertTrue(row["bounded_synthetic_edge_repair_verified"])
        self.assertFalse(row["nas_verified"])
        self.assertFalse(row["arbitrary_llm_code_repair_verified"])
        call = invoke.call_args
        self.assertEqual(call.kwargs["env"]["DOCKER_HOST"], "unix:///var/run/docker.sock")
        self.assertFalse(call.kwargs["shell"])
        self.assertIn("--pull=never", call.args[0])
        self.assertLessEqual(call.kwargs["timeout"], 25)

    def test_nominal_json_with_stderr_rejected_and_redacted(self):
        success = subprocess.CompletedProcess([], 0,
                 stdout=json.dumps(g146._EXPECTED), stderr="private customer filename")
        with patch("flowpilot_docker_workflow.shutil.which", return_value="docker"), \
             patch("flowpilot_docker_workflow._local_socket_ready", return_value=True), \
             patch("flowpilot_docker_workflow.subprocess.run", return_value=success):
            row = g146.run_workflow(GOAL, IMAGE, approved=True)
        self.assertEqual(row["status"], "LOCAL_DOCKER_WORKFLOW_FAILED")
        self.assertNotIn("private", json.dumps(row))

    def test_forged_receipts_rejected(self):
        baseline = dict(g146._EXPECTED)
        forged = [
            {**baseline, "repair_count": 0},
            {**baseline, "sqlite_rows": 1},
            {**baseline, "source_unchanged": False},
            {**baseline, "nas_verified": True},
            {**baseline, "output_sha256": "0"*64},
            {**baseline, "raw_user_data_used": "false"},
        ]
        for item in forged:
            with self.subTest(item=item):
                cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(item), stderr="")
                with patch("flowpilot_docker_workflow.shutil.which", return_value="docker"), \
                     patch("flowpilot_docker_workflow._local_socket_ready", return_value=True), \
                     patch("flowpilot_docker_workflow.subprocess.run", return_value=cp):
                    row = g146.run_workflow(GOAL, IMAGE, approved=True)
                self.assertEqual(row["status"], "LOCAL_DOCKER_WORKFLOW_FAILED")

    def test_duplicate_json_receipt_refused(self):
        raw = json.dumps(g146._EXPECTED)
        raw = raw[:-1] + ',"marker":"FLOWPILOT_SYNTHETIC_CONTAINER_WORKFLOW_V1"}'
        cp = subprocess.CompletedProcess([], 0, stdout=raw, stderr="")
        with patch("flowpilot_docker_workflow.shutil.which", return_value="docker"), \
             patch("flowpilot_docker_workflow._local_socket_ready", return_value=True), \
             patch("flowpilot_docker_workflow.subprocess.run", return_value=cp):
            row = g146.run_workflow(GOAL, IMAGE, approved=True)
        self.assertEqual(row["status"], "LOCAL_DOCKER_WORKFLOW_FAILED")

    def test_real_failure_exit_cannot_pass(self):
        cp = subprocess.CompletedProcess([], 9, stdout=json.dumps(g146._EXPECTED),
                                        stderr="")
        with patch("flowpilot_docker_workflow.shutil.which", return_value="docker"), \
             patch("flowpilot_docker_workflow._local_socket_ready", return_value=True), \
             patch("flowpilot_docker_workflow.subprocess.run", return_value=cp):
            row = g146.run_workflow(GOAL, IMAGE, approved=True)
        self.assertEqual(row["status"], "LOCAL_DOCKER_WORKFLOW_FAILED")


if __name__ == "__main__":
    unittest.main()
