"""G193 local registry-reference verification: fake Docker CLI only, no vendor code."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_checker_registry_evidence as probe

IMAGE = "sha256:" + "a" * 64
REPO = "docker.io/library/node@sha256:" + "b" * 64


class G193RegistryEvidenceTests(unittest.TestCase):
    def _fake(self, *, stdout: bytes, stderr: bytes = b"", rc: int = 0):
        with patch.object(probe.shutil, "which", return_value="/usr/bin/docker"):
            with patch.object(probe.gate, "_local_docker_socket_ready", return_value=True):
                with patch.object(probe.subprocess, "run", return_value=CompletedProcess(
                        [], rc, stdout, stderr)) as run:
                    receipt = probe.inspect_local_repo_digest(IMAGE, REPO)
        return receipt, run

    def test_strict_identity_before_docker_use(self):
        for image in (None, "", "node:22-alpine", "sha256:bad"):
            with self.subTest(image=image):
                with patch.object(probe.shutil, "which",
                                  side_effect=AssertionError("unexpected Docker")):
                    self.assertEqual(
                        probe.inspect_local_repo_digest(image, REPO)["status"],
                        "EXACT_LOCAL_IMAGE_ID_REQUIRED")

    def test_reject_nonofficial_or_malformed_repo_before_docker_use(self):
        for repo in (None, "", "docker.io/attacker/node@sha256:" + "b"*64,
                     "node@sha256:" + "b"*64, "docker.io/library/node:22-alpine",
                     "docker.io/library/node@sha256:" + "B"*64):
            with self.subTest(repo=repo):
                with patch.object(probe.shutil, "which",
                                  side_effect=AssertionError("unexpected Docker")):
                    self.assertEqual(
                        probe.inspect_local_repo_digest(IMAGE, repo)["status"],
                        "EXACT_OFFICIAL_NODE_REPO_DIGEST_REQUIRED")

    def test_missing_client_or_local_socket_never_executes(self):
        with patch.object(probe.shutil, "which", return_value=None):
            self.assertEqual(probe.inspect_local_repo_digest(IMAGE, REPO)["status"],
                             "LOCAL_DOCKER_CLIENT_MISSING")
        with patch.object(probe.shutil, "which", return_value="/usr/bin/docker"):
            with patch.object(probe.gate, "_local_docker_socket_ready", return_value=False):
                with patch.object(probe.subprocess, "run",
                                  side_effect=AssertionError("should not execute")):
                    self.assertEqual(probe.inspect_local_repo_digest(IMAGE, REPO)["status"],
                                     "LOCAL_UNIX_DOCKER_SOCKET_UNAVAILABLE")

    def test_matching_local_repo_ref_is_not_signature_or_release_proof(self):
        output = (IMAGE + "|linux|amd64|" + json.dumps([REPO]) + "\n").encode()
        receipt, run = self._fake(stdout=output)
        self.assertEqual(receipt["status"],
                         "LOCAL_NODE_REPO_REFERENCE_PRESENT_SIGNATURE_UNVERIFIED")
        self.assertEqual(receipt["platform"], "linux/amd64")
        for name in ("image_provenance_verified", "official_checker_executed",
                     "owner_archive_read", "docker_container_executed",
                     "docker_image_pulled", "nas_or_expert_executed"):
            self.assertFalse(receipt[name])
        self.assertEqual(receipt["release_gate"], "HOLD")
        self.assertEqual(run.call_count, 1)
        argv = run.call_args.args[0]
        self.assertEqual(argv[-5:],
                         ["image", "inspect", "--format",
                          "{{.Id}}|{{.Os}}|{{.Architecture}}|{{json .RepoDigests}}",
                          IMAGE])
        self.assertNotIn("run", argv)
        self.assertNotIn("pull", argv)
        self.assertEqual(run.call_args.kwargs["env"]["DOCKER_HOST"],
                         "unix:///var/run/docker.sock")
        self.assertNotIn("DOCKER_CONTEXT", run.call_args.kwargs["env"])

    def test_local_registry_digest_mismatch_fail_closed(self):
        different = "docker.io/library/node@sha256:" + "c"*64
        receipt, run = self._fake(stdout=(
            IMAGE + "|linux|amd64|" + json.dumps([different]) + "\n").encode())
        self.assertEqual(receipt["status"], "LOCAL_OFFICIAL_NODE_REPO_REFERENCE_NOT_MATCHED")
        self.assertEqual(run.call_count, 1)

    def test_wrong_image_or_platform_fail_closed(self):
        cases = [
            ("sha256:" + "d"*64 + "|linux|amd64|" + json.dumps([REPO]),
             "LOCAL_IMAGE_ID_MISMATCH"),
            (IMAGE + "|windows|amd64|" + json.dumps([REPO]),
             "LOCAL_IMAGE_PLATFORM_UNSUPPORTED"),
            (IMAGE + "|linux|386|" + json.dumps([REPO]),
             "LOCAL_IMAGE_PLATFORM_UNSUPPORTED"),
        ]
        for output, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(self._fake(stdout=output.encode())[0]["status"], expected)

    def test_invalid_repo_metadata_is_not_recognized(self):
        for blob in ('{"not":"array"}', '["foo", 2]', "invalid", "null"):
            with self.subTest(blob=blob):
                receipt, _ = self._fake(
                    stdout=(IMAGE + "|linux|amd64|" + blob + "\n").encode())
                self.assertIn(receipt["status"],
                              {"LOCAL_REPO_DIGEST_METADATA_INVALID",
                               "LOCAL_OFFICIAL_NODE_REPO_REFERENCE_NOT_MATCHED"})
                self.assertFalse(receipt["image_provenance_verified"])

    def test_docker_error_does_not_leak_private_stderr(self):
        receipt, _ = self._fake(stdout=b"", stderr=b"OWNER_PRIVATE_PATH", rc=1)
        self.assertEqual(receipt["status"], "LOCAL_IMAGE_METADATA_UNAVAILABLE")
        self.assertNotIn("PRIVATE", json.dumps(receipt))

    def test_cli_cannot_report_checker_pass_even_on_positive_metadata(self):
        with patch.object(probe, "inspect_local_repo_digest",
                          return_value=probe._receipt(
                              "LOCAL_NODE_REPO_REFERENCE_PRESENT_SIGNATURE_UNVERIFIED")):
            with redirect_stdout(StringIO()) as out:
                rc = probe.main(["--image-id", IMAGE, "--expected-repo-digest", REPO])
        self.assertEqual(rc, 2)
        self.assertFalse(json.loads(out.getvalue())["official_checker_executed"])


if __name__ == "__main__":
    unittest.main()
