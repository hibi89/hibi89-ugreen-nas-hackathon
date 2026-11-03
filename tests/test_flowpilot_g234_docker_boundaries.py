"""G234: fail-closed local Docker client boundary for actual synthetic smoke."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g233_real_docker_smoke as g233


def response(stage: str) -> str:
    status, present, missing = g233.EXPECTED[stage]
    return json.dumps({
        "schema": g233.SMOKE_SCHEMA, "status": status,
        "present_count": present, "missing_count": missing,
        "nas_verified": False, "owner_files_accessed": False,
        "auto_repair_performed": False,
    })


class G234DockerSecurityTests(unittest.TestCase):
    def test_explicit_approval_is_required_without_docker_probe(self):
        with patch.object(g233, "test_synthetic_docker",
                          side_effect=AssertionError("should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as captured:
            rc = g233.main([])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(captured.getvalue())["status"],
                         "EXPLICIT_LOCAL_DOCKER_APPROVAL_REQUIRED")

    def test_remote_only_context_refused_before_subprocess(self):
        with patch.object(g233, "_local_docker_socket_ready", return_value=False), \
             patch.object(g233.subprocess, "run",
                          side_effect=AssertionError("remote daemon contacted")):
            with self.assertRaisesRegex(g233.SmokeRefused,
                                        "LOCAL_DOCKER_SOCKET_NOT_VERIFIED"):
                g233.checked_run(["docker", "info"])

    def test_docker_client_is_forced_to_local_socket_and_no_owner_credentials(self):
        success = subprocess.CompletedProcess([], 0, "Docker OK\n", "")
        with patch.object(g233, "_local_docker_socket_ready", return_value=True), \
             patch.object(g233.subprocess, "run", return_value=success) as invoke, \
             patch.dict(os.environ, {
                 "DOCKER_HOST": "tcp://remote.invalid:2375",
                 "DOCKER_CONTEXT": "remote-personal",
                 "DOCKER_CONFIG": "/home/owner/.docker",
             }):
            self.assertEqual(g233.checked_run(
                ["docker", "info", "--format", "{{.ServerVersion}}"]),
                "Docker OK")
        args = invoke.call_args.args[0]
        env = invoke.call_args.kwargs["env"]
        self.assertEqual(args[:2], ["docker",
                         "--host=unix:///var/run/docker.sock"])
        self.assertEqual(env["DOCKER_HOST"], "unix:///var/run/docker.sock")
        self.assertNotIn("DOCKER_CONTEXT", env)
        self.assertNotEqual(env["DOCKER_CONFIG"], "/home/owner/.docker")
        self.assertFalse(invoke.call_args.kwargs["shell"])

    def test_compiler_invocation_is_not_replaced_with_docker(self):
        success = subprocess.CompletedProcess([], 0, "", "")
        with patch.object(g233.subprocess, "run", return_value=success) as invoke:
            g233.checked_run(["cc", "-v"])
        self.assertEqual(invoke.call_args.args[0], ["cc", "-v"])

    def test_fixed_receipts_pass_but_fake_nas_and_duplicate_keys_fail(self):
        for stage in ("before", "after"):
            g233.verify_fixture_output(response(stage), stage)
        forged = json.loads(response("before"))
        forged["nas_verified"] = True
        with self.assertRaisesRegex(g233.SmokeRefused, "INVALID_OR_OVERSTATED"):
            g233.verify_fixture_output(json.dumps(forged), "before")
        duplicate = response("after")[:-1] + ',"nas_verified":false}'
        with self.assertRaisesRegex(g233.SmokeRefused, "DUPLICATE_CONTAINER"):
            g233.verify_fixture_output(duplicate, "after")

    def test_untrusted_oversized_or_wrong_stage_receipt_fails(self):
        with self.assertRaises(g233.SmokeRefused):
            g233.verify_fixture_output(" " * 1025, "before")
        with self.assertRaises(g233.SmokeRefused):
            g233.verify_fixture_output(response("after"), "before")

    def test_failed_docker_command_does_not_echo_sensitive_stderr(self):
        failed = subprocess.CompletedProcess([], 1, "", "SECRET_OWNER_TOKEN")
        with patch.object(g233, "_local_docker_socket_ready", return_value=True), \
             patch.object(g233.subprocess, "run", return_value=failed):
            with self.assertRaises(g233.SmokeRefused) as caught:
                g233.checked_run(["docker", "info"])
        self.assertNotIn("SECRET_OWNER_TOKEN", str(caught.exception))

    def test_arbitrary_process_rejected(self):
        with patch.object(g233.subprocess, "run",
                          side_effect=AssertionError("executed")):
            with self.assertRaisesRegex(g233.SmokeRefused,
                                        "UNSUPPORTED_LOCAL_PROCESS"):
                g233.checked_run(["sh", "-c", "anything"])


if __name__ == "__main__":
    unittest.main()
