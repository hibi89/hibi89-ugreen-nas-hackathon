"""G192 isolated Docker metadata preflight tests: all fake subprocess data."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_checker_docker_preflight as probe

IMAGE = "sha256:" + ("b" * 64)


class G192LocalDockerPreflightTests(unittest.TestCase):
    def test_missing_and_mutable_image_rejected_without_docker_query(self):
        for val in (None, "", "node:22-alpine", "sha256:" + "a" * 63):
            with self.subTest(val=val), \
                 patch.object(probe.shutil, "which", side_effect=AssertionError("Docker touched")):
                report = probe.preflight(val)
                self.assertEqual(report["status"], "EXACT_IMAGE_ID_REQUIRED")
                self.assertEqual(report["release_gate"], "HOLD")

    def test_missing_client_reports_no_vendor_execution(self):
        with patch.object(probe.shutil, "which", return_value=None), \
             patch.object(probe.subprocess, "run", side_effect=AssertionError("executed")):
            out = probe.preflight(IMAGE)
        self.assertEqual(out["status"], "LOCAL_DOCKER_CLIENT_MISSING")
        self.assertFalse(out["official_checker_executed"])

    def test_missing_local_socket_refuses_remote_fallback(self):
        with patch.object(probe.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(probe.gate, "_local_docker_socket_ready", return_value=False), \
             patch.object(probe.subprocess, "run", side_effect=AssertionError("remote attempted")):
            out = probe.preflight(IMAGE)
        self.assertEqual(out["status"], "LOCAL_UNIX_DOCKER_SOCKET_UNAVAILABLE")
        self.assertFalse(out["private_candidate_or_kit_read"])

    def _inspect(self, proc):
        with patch.object(probe.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(probe.gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(probe.subprocess, "run", return_value=proc) as run:
            result = probe.preflight(IMAGE)
        return result, run

    def test_correct_local_metadata_never_claims_image_origin_or_checker(self):
        data = CompletedProcess([], 0, (IMAGE+"|linux|amd64\n").encode(), b"")
        receipt, run = self._inspect(data)
        self.assertEqual(receipt["status"], "LOCAL_IMAGE_INSPECTED_PROVENANCE_UNVERIFIED")
        self.assertEqual(receipt["local_image_id"], IMAGE)
        self.assertEqual(receipt["platform"], "linux/amd64")
        self.assertTrue(receipt["docker_image_inspected"])
        for k in ("image_provenance_verified", "official_checker_executed",
                  "docker_container_executed", "external_image_pull", "private_candidate_or_kit_read"):
            self.assertIs(receipt[k], False)
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[-5:], ["image", "inspect", "--format",
                                   "{{.Id}}|{{.Os}}|{{.Architecture}}", IMAGE])
        self.assertNotIn("run", cmd)
        self.assertNotIn("pull", cmd)
        self.assertIn("--host=unix:///var/run/docker.sock", cmd)
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["DOCKER_HOST"], "unix:///var/run/docker.sock")
        self.assertEqual(env["HOME"], env["DOCKER_CONFIG"])
        self.assertNotIn("DOCKER_CONTEXT", env)
        self.assertNotIn("DOCKER_TLS_VERIFY", env)

    def test_mismatched_id_and_invalid_platform_fail_closed(self):
        cases = [
            (("sha256:"+"c"*64)+"|linux|amd64\n", "LOCAL_IMAGE_ID_MISMATCH"),
            (IMAGE+"|windows|amd64\n", "LOCAL_IMAGE_PLATFORM_UNSUPPORTED"),
            (IMAGE+"|linux|386\n", "LOCAL_IMAGE_PLATFORM_UNSUPPORTED"),
            ("not-a-recognized-format", "LOCAL_IMAGE_ID_MISMATCH"),
        ]
        for raw, expected in cases:
            with self.subTest(expected=expected):
                receipt, _ = self._inspect(CompletedProcess([], 0, raw.encode(), b""))
                self.assertEqual(receipt["status"], expected)
                self.assertEqual(receipt["release_gate"], "HOLD")

    def test_failed_docker_cli_never_leaks_stderr(self):
        marker = b"OWNER_PRIVATE_SECRET_PATH"
        receipt, _ = self._inspect(CompletedProcess([], 1, b"", marker))
        self.assertEqual(receipt["status"], "LOCAL_IMAGE_NOT_VERIFIED")
        self.assertNotIn("SECRET", json.dumps(receipt))
        self.assertNotIn("PATH", json.dumps(receipt))

    def test_timeout_is_nonretriable_safe_report(self):
        with patch.object(probe.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(probe.gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(probe.subprocess, "run",
                          side_effect=TimeoutExpired(["docker"], 20)):
            receipt = probe.preflight(IMAGE)
        self.assertEqual(receipt["status"], "LOCAL_DOCKER_INSPECTION_FAILED")

    def test_cli_never_returns_checker_pass_exit_code(self):
        with patch.object(probe, "preflight", return_value=probe._report(
                "LOCAL_IMAGE_INSPECTED_PROVENANCE_UNVERIFIED", inspected=True)), \
             redirect_stdout(StringIO()) as buf:
            rc = probe.main(["--image-id", IMAGE])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(buf.getvalue())["release_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
