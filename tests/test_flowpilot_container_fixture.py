"""G118 fixed Docker fixture scripts: local Python execution and Docker mock boundaries."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_container_fixture import (
    _SCRIPTS, _trusted_receipt, plan_container_fixture, run_container_fixture
)
from flowpilot_isolation_contract import plan_sandbox

PINNED = "python@sha256:" + "b" * 64
GOAL = "고객별 매출 보고서 만들어줘"
FILE_GOAL = "필수 파일 확인해줘"


class G118ContainerFixtureTests(unittest.TestCase):
    def test_two_fixed_scripts_actually_run_in_local_python_interpreter(self):
        # Executes script source with the local Python interpreter, NOT Docker.
        for template, script in _SCRIPTS.items():
            with self.subTest(template=template):
                r = subprocess.run([sys.executable, "-I", "-B", "-c", script],
                                   capture_output=True, text=True, timeout=10)
                self.assertEqual(r.returncode, 0, r.stderr)
                receipt = json.loads(r.stdout)
                self.assertTrue(receipt["invalid_fixture_refused"])
                self.assertTrue(receipt["expected_output_verified"])
                self.assertTrue(receipt["source_preserved"])
                self.assertEqual(receipt["nonroot"],
                                 os.name == "posix" and os.getuid() != 0)
                # Windows local Python is not a Linux-container uid proof.
                self.assertEqual(_trusted_receipt(template, r.stdout),
                                 os.name == "posix" and os.getuid() != 0)

    def test_pinned_plan_only_is_nonexecuting_and_security_flags_preserved(self):
        p = plan_container_fixture(GOAL, PINNED)
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")
        self.assertEqual(p["template"], "csv_customer_revenue_v1")
        self.assertFalse(p["execution_attempted"])
        self.assertEqual(p["fixed_source_sha256"],
                         hashlib.sha256(_SCRIPTS[p["template"]].encode()).hexdigest())
        self.assertIn("--network=none", p["docker_flags"])
        self.assertIn("--host=unix:///var/run/docker.sock", p["docker_flags"])

    def test_no_approval_never_queries_docker_or_runs(self):
        with patch("flowpilot_container_fixture.shutil.which",
                   side_effect=AssertionError("Docker checked")), \
             patch("flowpilot_container_fixture.subprocess.run",
                   side_effect=AssertionError("process invoked")):
            p = run_container_fixture(GOAL, PINNED)
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")

    def test_unknown_nas_task_refused_before_docker(self):
        p = run_container_fixture("삭제하고 이메일로 보내줘", PINNED, approved=True)
        self.assertEqual(p["status"], "BLOCKED_UNSUPPORTED_GOAL")
        self.assertFalse(p["docker_launched"])

    def test_no_local_daemon_fails_closed(self):
        with patch("flowpilot_container_fixture.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_container_fixture._local_socket_ready", return_value=False), \
             patch("flowpilot_container_fixture.subprocess.run",
                   side_effect=AssertionError("must not run")):
            p = run_container_fixture(GOAL, PINNED, approved=True)
        self.assertEqual(p["status"], "LOCAL_DOCKER_NOT_AVAILABLE")

    def test_hardened_fixed_cli_with_simulated_receipt_only(self):
        output = json.dumps({"marker": "FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1",
                             "template": "csv_customer_revenue_v1",
                             "invalid_fixture_refused": True,
                             "expected_output_verified": True,
                             "source_preserved": True, "nonroot": True})
        fake = subprocess.CompletedProcess([], 0, output, "")
        with patch("flowpilot_container_fixture.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_container_fixture._local_socket_ready", return_value=True), \
             patch("flowpilot_container_fixture.subprocess.run", return_value=fake) as runner:
            p = run_container_fixture(GOAL, PINNED, approved=True)
        self.assertEqual(p["status"], "LOCAL_CONTAINER_FIXTURE_PASS_NOT_NAS")
        self.assertFalse(p["real_nas_verified"])
        self.assertFalse(p["Docker_isolation_independently_verified"])
        args = runner.call_args.args[0]
        self.assertTrue(runner.call_args.kwargs["shell"] is False)
        self.assertIn("--network=none", args)
        self.assertIn("--pull=never", args)
        self.assertIn("--read-only", args)
        self.assertIn("--host=unix:///var/run/docker.sock", args)
        self.assertEqual(args[-1], _SCRIPTS["csv_customer_revenue_v1"])

    def test_spoofed_or_failing_receipt_rejected(self):
        for bad in ("", "{}", '{"marker":"FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1"}',
                    '{"marker":"FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1","template":"csv_customer_revenue_v1","invalid_fixture_refused":true,"expected_output_verified":false,"source_preserved":true,"nonroot":true}'):
            with self.subTest(bad=bad):
                fake = subprocess.CompletedProcess([], 0, bad, "secret")
                with patch("flowpilot_container_fixture.shutil.which", return_value="/usr/bin/docker"), \
                     patch("flowpilot_container_fixture._local_socket_ready", return_value=True), \
                     patch("flowpilot_container_fixture.subprocess.run", return_value=fake):
                    p = run_container_fixture(GOAL, PINNED, approved=True)
                self.assertEqual(p["status"], "LOCAL_CONTAINER_FIXTURE_FAILED")
                self.assertNotIn("secret", json.dumps(p))

    def test_file_template_bounded_local_script(self):
        p = plan_container_fixture(FILE_GOAL, PINNED)
        self.assertEqual(p["template"], "required_file_metadata_v1")
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")

    def test_timeout_does_not_claim_success(self):
        with patch("flowpilot_container_fixture.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_container_fixture._local_socket_ready", return_value=True), \
             patch("flowpilot_container_fixture.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["docker"], 15)):
            p = run_container_fixture(GOAL, PINNED, approved=True)
        self.assertEqual(p["status"], "LOCAL_CONTAINER_FIXTURE_FAILED")

    def test_cli_plan_only_windows_safe(self):
        command = [sys.executable, str(ROOT/"tools"/"flowpilot_container_fixture.py"),
                   "--goal", FILE_GOAL, "--image", PINNED]
        r = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.isascii())
        self.assertEqual(json.loads(r.stdout)["status"], "WAITING_LOCAL_DOCKER_APPROVAL")


if __name__ == "__main__":
    unittest.main()
