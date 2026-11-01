"""G191: immutable Docker image gate; all tests synthetic, no Docker/vendor/NAS."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from subprocess import CompletedProcess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_official_checker as gate

IMAGE = "sha256:" + ("b" * 64)


class G191DockerImageGate(unittest.TestCase):
    def setUp(self):
        self.missing = Path("/g191-synthetic-no-files/owner.zip")

    def test_consent_without_image_refuses_before_archive_read(self):
        with patch.object(gate, "_read_pinned", side_effect=AssertionError("private read")) as read:
            with self.assertRaisesRegex(gate.VerificationRefused, "image SHA256 ID"):
                gate.check(self.missing, self.missing, mode="docker",
                           candidate_profile="g188", official_risk_approved=True)
        read.assert_not_called()

    def test_tag_and_invalid_image_identity_refused_before_read(self):
        for image in ("node:22-alpine", "sha256:short", "sha256:"+"A"*64, 1, None):
            with self.subTest(image=image):
                with patch.object(gate, "_read_pinned", side_effect=AssertionError("private read")) as read:
                    with self.assertRaisesRegex(gate.VerificationRefused, "image SHA256 ID"):
                        gate.check(self.missing, self.missing, mode="docker",
                                   official_risk_approved=True, expected_docker_image_id=image)
                read.assert_not_called()

    def test_matching_image_id_does_not_bypass_missing_owner_source(self):
        with self.assertRaisesRegex(gate.VerificationRefused, "Missing, nonregular"):
            gate.check(self.missing, self.missing, mode="docker",
                       official_risk_approved=True, expected_docker_image_id=IMAGE)

    def test_image_mismatch_blocks_docker_run_before_mount(self):
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(gate.subprocess, "run", return_value=CompletedProcess(
                 [], 0, ("sha256:"+"c"*64+"\n").encode(), b"")) as run:
            with self.assertRaisesRegex(gate.VerificationRefused, "identity mismatch"):
                gate._execute(self.missing.parent, self.missing.parent, mode="docker",
                              docker_image_id=IMAGE)
        self.assertEqual(run.call_count, 1)

    def test_matching_image_uses_immutable_id_and_never_pulls(self):
        outputs = [CompletedProcess([], 0, (IMAGE+"\n").encode(), b""),
                   CompletedProcess([], 0, b"{}", b"")]
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(gate.subprocess, "run", side_effect=outputs) as run:
            result = gate._execute(self.missing.parent, self.missing.parent,
                                   mode="docker", docker_image_id=IMAGE)
        self.assertEqual(result, (0, "{}", ""))
        self.assertEqual(run.call_count, 2)
        inspect, execute = run.call_args_list
        self.assertEqual(inspect.args[0][-5:], ["image", "inspect", "--format", "{{.Id}}", IMAGE])
        self.assertEqual(execute.args[0][-3], IMAGE)
        self.assertIn("--pull=never", execute.args[0])
        self.assertIn("--network=none", execute.args[0])
        self.assertNotIn("node:22-alpine", execute.args[0])

    def test_cli_image_id_does_not_grant_vendor_execution_consent(self):
        args = ["--candidate-zip", str(self.missing), "--official-kit-zip", str(self.missing),
                "--candidate-profile", "g188", "--mode", "docker",
                "--expected-docker-image-id", IMAGE]
        with patch.object(gate, "check", side_effect=AssertionError("dispatched")) as check, \
             redirect_stdout(StringIO()) as output:
            rc = gate.main(args)
        self.assertEqual(rc, 2)
        check.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())["official_checker_executed"])

    def test_cli_explicit_consent_still_routes_only_to_mock(self):
        args = ["--candidate-zip", str(self.missing), "--official-kit-zip", str(self.missing),
                "--candidate-profile", "g188", "--mode", "docker",
                "--expected-docker-image-id", IMAGE, "--accept-official-code-execution-risk"]
        with patch.object(gate, "check", return_value={
                "release_gate": "HOLD", "official_checker_executed": False}) as call, \
             redirect_stdout(StringIO()) as output:
            rc = gate.main(args)
        self.assertEqual(rc, 2)
        self.assertEqual(call.call_args.kwargs["expected_docker_image_id"], IMAGE)
        self.assertIs(call.call_args.kwargs["official_risk_approved"], True)
        self.assertFalse(json.loads(output.getvalue())["official_checker_executed"])


if __name__ == "__main__":
    unittest.main()
