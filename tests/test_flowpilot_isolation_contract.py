"""G117 fail-closed optional local Docker smoke preflight."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_isolation_contract import plan_sandbox, run_local_smoke

GOOD = "docker.io/library/python@sha256:" + "a" * 64
GOAL = "고객별 매출 보고서 만들어줘"


class G117SandboxContractTests(unittest.TestCase):
    def test_compiles_pinned_no_network_no_privilege_command(self):
        p = plan_sandbox(GOAL, GOOD)
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")
        argv = p["argv"]
        for flag in ("--rm", "--pull=never", "--network=none", "--read-only",
                     "--cap-drop=ALL", "--security-opt=no-new-privileges",
                     "--memory=128m", "--pids-limit=32", "--cpus=0.5",
                     "--user=65534:65534"):
            self.assertIn(flag, argv)
        self.assertNotIn("-v", argv)
        self.assertNotIn("--privileged", argv)
        self.assertNotIn("--env", argv)
        self.assertIn("--host=unix:///var/run/docker.sock", argv)
        self.assertEqual(argv[-5:-4], [GOOD])
        self.assertFalse(p["docker_launched"])

    def test_no_approval_even_when_docker_exists_never_invokes(self):
        with patch("flowpilot_isolation_contract.shutil.which", side_effect=AssertionError("docker checked")), \
             patch("flowpilot_isolation_contract.subprocess.run", side_effect=AssertionError("docker invoked")):
            p = run_local_smoke(GOAL, GOOD)
        self.assertEqual(p["status"], "WAITING_LOCAL_DOCKER_APPROVAL")

    def test_refuses_mutable_unpinned_or_untrusted_image_refs(self):
        for image in ("python:3.11", "python@sha256:123", "evil.io/x@sha256:" + "b"*64,
                      "docker.io/library/python@sha256:" + "a"*63 + "Z",
                      "python@sha256:" + "a"*64 + " --privileged", "", None):
            with self.subTest(image=image):
                self.assertEqual(plan_sandbox(GOAL, image)["status"], "BLOCKED_UNPINNED_IMAGE")

    def test_refuses_unimplemented_nas_and_scheduling_request(self):
        self.assertEqual(plan_sandbox("NAS 전부 삭제해줘", GOOD)["status"],
                         "BLOCKED_UNSUPPORTED_GOAL")

    def test_approval_without_installed_docker_fails_closed(self):
        with patch("flowpilot_isolation_contract.shutil.which", return_value=None), \
             patch("flowpilot_isolation_contract.subprocess.run", side_effect=AssertionError("executed")):
            p = run_local_smoke(GOAL, GOOD, approved=True)
        self.assertEqual(p["status"], "LOCAL_DOCKER_NOT_AVAILABLE")
        self.assertFalse(p["docker_launched"])

    def test_fake_shell_free_invocation_and_exact_smoke_receipt(self):
        response = subprocess.CompletedProcess([], 0,
            stdout=json.dumps({"marker": "FLOWPILOT_DISPOSABLE_CONTAINER_SMOKE_V1",
                               "nonroot": True, "python": True}), stderr="")
        with patch("flowpilot_isolation_contract.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_isolation_contract._local_socket_ready", return_value=True), \
             patch("flowpilot_isolation_contract.subprocess.run", return_value=response) as run:
            p = run_local_smoke(GOAL, GOOD, approved=True)
        self.assertEqual(p["status"], "LOCAL_DOCKER_SMOKE_PASS_NOT_NAS")
        argv = run.call_args.args[0]
        self.assertEqual(argv[0], "/usr/bin/docker")
        self.assertTrue(run.call_args.kwargs["shell"] is False)
        self.assertEqual(run.call_args.kwargs["env"]["DOCKER_HOST"],
                         "unix:///var/run/docker.sock")
        self.assertNotIn("DOCKER_CONTEXT", run.call_args.kwargs["env"])
        self.assertTrue(run.call_args.kwargs["timeout"] <= 15)
        self.assertFalse(p["actual_workflow_executed_in_docker"])
        self.assertFalse(p["docker_host_isolation_independently_verified"])

    def test_forged_or_bad_exit_never_returns_success(self):
        for out, rc in [('{"marker":"FLOWPILOT_DISPOSABLE_CONTAINER_SMOKE_V1","nonroot":false,"python":true}', 0),
                        ("", 0), ("unauthorized", 1), ("{}", 0)]:
            with self.subTest(out=out):
                response = subprocess.CompletedProcess([], rc, stdout=out, stderr="private")
                with patch("flowpilot_isolation_contract.shutil.which", return_value="/usr/bin/docker"), \
                     patch("flowpilot_isolation_contract._local_socket_ready", return_value=True), \
                     patch("flowpilot_isolation_contract.subprocess.run", return_value=response):
                    p = run_local_smoke(GOAL, GOOD, approved=True)
                self.assertEqual(p["status"], "LOCAL_DOCKER_SMOKE_FAILED")
                self.assertNotIn("private", json.dumps(p))

    def test_subprocess_timeout_fails_closed(self):
        with patch("flowpilot_isolation_contract.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_isolation_contract._local_socket_ready", return_value=True), \
             patch("flowpilot_isolation_contract.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["docker"], 15)):
            p = run_local_smoke(GOAL, GOOD, approved=True)
        self.assertEqual(p["status"], "LOCAL_DOCKER_SMOKE_FAILED")

    def test_docker_binary_without_local_socket_never_executes(self):
        with patch("flowpilot_isolation_contract.shutil.which", return_value="/usr/bin/docker"), \
             patch("flowpilot_isolation_contract._local_socket_ready", return_value=False), \
             patch("flowpilot_isolation_contract.subprocess.run",
                   side_effect=AssertionError("must not execute")):
            r = run_local_smoke(GOAL, GOOD, approved=True)
        self.assertEqual(r["status"], "LOCAL_DOCKER_NOT_AVAILABLE")

    def test_cli_plan_only_is_ascii_json_and_never_runs(self):
        cmd = [sys.executable, str(ROOT/"tools"/"flowpilot_isolation_contract.py"),
               "--goal", GOAL, "--image", GOOD]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.isascii())
        self.assertEqual(json.loads(r.stdout)["status"], "WAITING_LOCAL_DOCKER_APPROVAL")


if __name__ == "__main__":
    unittest.main()
