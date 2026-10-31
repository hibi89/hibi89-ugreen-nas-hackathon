"""G100 tests: pure synthetic vendor fixtures; NEVER execute real vendor code."""
from contextlib import redirect_stdout
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_official_checker as gate


def zip_bytes(files):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buffer.getvalue()


class G100OfficialKitBoundary(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.source = b"---\nname: flowpilot-3\ndescription: synthetic\n---\n"
        self.candidate = zip_bytes({gate.MEMBER: self.source})
        self.kit = zip_bytes({
            "uliya-skill-kit/SKILL.md": b"official synthetic",
            "uliya-skill-kit/scripts/check-skill.mjs": b"// synthetic only",
            "uliya-skill-kit/data/capability-catalog.json": b"{}",
        })
        self.path = base / "candidate.zip"
        self.vendor = base / "kit.zip"
        self.path.write_bytes(self.candidate)
        self.vendor.write_bytes(self.kit)
        for key, raw in (("CANDIDATE_SHA", self.source),
                         ("CANDIDATE_ZIP_SHA", self.candidate),
                         ("VENDOR_ZIP_SHA", self.kit)):
            mock = patch.object(gate, key, sha256(raw).hexdigest())
            mock.start()
            self.addCleanup(mock.stop)

    def test_pins_only_inspection_cannot_claim_official_execution(self):
        with patch.object(gate, "_execute", side_effect=AssertionError("No execution")):
            result = gate.check(self.path, self.vendor, mode="inspect")
        self.assertEqual(result["status"], "EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN")
        self.assertFalse(result["official_checker_executed"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_candidate_mutation_rejected_before_execution(self):
        self.path.write_bytes(self.candidate + b"tampered")
        with self.assertRaisesRegex(gate.VerificationRefused, "SHA256"):
            gate.check(self.path, self.vendor, mode="inspect")

    def test_vendor_mutation_rejected_before_execution(self):
        self.vendor.write_bytes(self.kit + b"tampered")
        with self.assertRaisesRegex(gate.VerificationRefused, "SHA256"):
            gate.check(self.path, self.vendor, mode="inspect")

    def test_malformed_member_refused(self):
        altered = zip_bytes({"flowpilot-3/not-skill.txt": self.source})
        self.path.write_bytes(altered)
        with patch.object(gate, "CANDIDATE_ZIP_SHA", sha256(altered).hexdigest()):
            with self.assertRaisesRegex(gate.VerificationRefused, "exact Markdown"):
                gate.check(self.path, self.vendor, mode="inspect")

    def test_traversal_refused(self):
        altered = zip_bytes({"../outside": self.source})
        self.path.write_bytes(altered)
        with patch.object(gate, "CANDIDATE_ZIP_SHA", sha256(altered).hexdigest()):
            with self.assertRaisesRegex(gate.VerificationRefused, "Unsafe ZIP"):
                gate.check(self.path, self.vendor, mode="inspect")

    def test_native_requires_explicit_opt_in(self):
        with patch.object(gate, "_execute", side_effect=AssertionError("No execution")):
            with self.assertRaisesRegex(gate.VerificationRefused, "explicit"):
                gate.check(self.path, self.vendor, mode="native")

    def test_zero_warnings_does_not_release(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": []})
        with patch.object(gate, "_execute", return_value=(0, payload, "")):
            result = gate.check(self.path, self.vendor, mode="native",
                                native_risk_approved=True)
        self.assertEqual(result["result"], "OFFICIAL_STATIC_PASS_REVIEW_ONLY")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["owner_release_approved"])

    def test_nonzero_warning_maintains_hold(self):
        payload = json.dumps({"status": "static-pass-needs-target-validation", "summary": {
            "errors": 0, "warnings": 1, "info": 0}, "diagnostics": [
                {"code": "DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE"}]})
        with patch.object(gate, "_execute", return_value=(0, payload, "")):
            result = gate.check(self.path, self.vendor, mode="native",
                                native_risk_approved=True)
        self.assertEqual(result["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertEqual(result["checker_summary"]["warnings"], 1)

    def test_duplicate_checker_json_key_fails_closed(self):
        forged = '{"status":"static-pass","status":"static-pass","summary":{"errors":0,"warnings":0,"info":0}}'
        result = gate._sanitized_checker_result(0, forged, "", mode="native")
        self.assertEqual(result["result"], "UNVERIFIED_NON_JSON_CHECKER_OUTPUT")

    def test_inconsistent_error_diagnostic_cannot_pass(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": [
                {"code": "INCONSISTENT_FATAL", "severity": "error"}]})
        result = gate._sanitized_checker_result(0, payload, "", mode="docker")
        self.assertEqual(result["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertFalse(result["diagnostics_consistent_with_zero_summary"])
        self.assertIn("INCONSISTENT_FATAL", result["diagnostic_codes"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_missing_diagnostics_cannot_pass(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}})
        result = gate._sanitized_checker_result(0, payload, "", mode="docker")
        self.assertEqual(result["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertFalse(result["diagnostics_consistent_with_zero_summary"])

    def test_malformed_diagnostics_cannot_pass(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": "NOT_A_LIST"})
        result = gate._sanitized_checker_result(0, payload, "", mode="docker")
        self.assertEqual(result["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertFalse(result["diagnostics_consistent_with_zero_summary"])

    def test_g103_exact_profile_with_synthetic_inputs_maintains_hold(self):
        with patch.object(gate, "G103_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G103_CANDIDATE_ZIP_SHA", sha256(self.candidate).hexdigest()):
            result = gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g103")
        self.assertEqual(result["candidate_profile"], "g103")
        self.assertEqual(result["source_sha256"], sha256(self.source).hexdigest())
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["official_checker_executed"])

    def test_g103_profile_without_matching_exact_bytes_is_refused(self):
        with self.assertRaisesRegex(gate.VerificationRefused, "SHA256"):
            gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g103")

    def test_unknown_profile_fails_before_any_kit_read(self):
        with self.assertRaisesRegex(gate.VerificationRefused, "Unsupported exact"):
            gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g104")

    def test_g103_cli_inspect_never_claims_official_checker(self):
        with patch.object(gate, "G103_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G103_CANDIDATE_ZIP_SHA", sha256(self.candidate).hexdigest()):
            with patch.object(sys, "argv", [
                 "check", "--candidate-zip", str(self.path), "--official-kit-zip", str(self.vendor),
                 "--candidate-profile", "g103"]), redirect_stdout(StringIO()) as out:
                code = gate.main()
        self.assertEqual(code, 2)
        result = json.loads(out.getvalue())
        self.assertEqual(result["candidate_profile"], "g103")
        self.assertFalse(result["official_checker_executed"])

    def test_inspect_command_never_claims_success(self):
        with patch.object(sys, "argv", ["check", "--candidate-zip", str(self.path),
                    "--official-kit-zip", str(self.vendor)]), redirect_stdout(StringIO()) as out:
            code = gate.main()
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())["official_checker_executed"])


    def test_g139_exact_multifile_profile_synthetic_inspect_only(self):
        files = {
            gate.MEMBER: self.source,
            gate.G139_MEMBERS[1]: b"# synthetic capability reference\n",
            gate.G139_MEMBERS[2]: b"# synthetic safety reference\n",
        }
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G139_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(gate, "_execute", side_effect=AssertionError("No execution")):
            result = gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g139")
        self.assertEqual(result["candidate_profile"], "g139")
        self.assertEqual(result["candidate_member_count"], 3)
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["official_checker_executed"])

    def test_g139_missing_reference_fails_before_checker(self):
        incomplete = zip_bytes({gate.MEMBER: self.source,
                                gate.G139_MEMBERS[1]: b"# synthetic\n"})
        self.path.write_bytes(incomplete)
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G139_CANDIDATE_ZIP_SHA", sha256(incomplete).hexdigest()), \
             patch.object(gate, "_execute", side_effect=AssertionError("No execution")):
            with self.assertRaisesRegex(gate.VerificationRefused, "exact approved"):
                gate.check(self.path, self.vendor, mode="docker", candidate_profile="g139")

    def test_g139_ref_only_tamper_rejected_by_pinned_zip(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# changed", gate.G139_MEMBERS[2]: b"# expected"}
        self.path.write_bytes(zip_bytes(files))
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()):
            with self.assertRaisesRegex(gate.VerificationRefused, "SHA256"):
                gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g139")

    def test_g139_exact_three_files_passed_to_checker_without_vendor_execution(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# synthetic capability reference",
                 gate.G139_MEMBERS[2]: b"# synthetic safety reference"}
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        payload = json.dumps({"status": "static-pass", "summary":
                              {"errors": 0, "warnings": 0, "info": 0},
                              "diagnostics": []})
        def fake_checker(vendor, candidate, mode):
            self.assertTrue((candidate / "SKILL.md").exists())
            for name in gate.G139_MEMBERS[1:]:
                expected_path = candidate.parent / name
                self.assertEqual(expected_path.read_bytes(), files[name])
            return (0, payload, "")
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G139_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(gate, "_execute", side_effect=fake_checker):
            result = gate.check(self.path, self.vendor, mode="native",
                                native_risk_approved=True, candidate_profile="g139")
        self.assertEqual(result["result"], "OFFICIAL_STATIC_PASS_REVIEW_ONLY")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertEqual(result["candidate_member_count"], 3)

    def test_g139_reference_mutation_during_checker_fails_closed(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# synthetic capability reference",
                 gate.G139_MEMBERS[2]: b"# synthetic safety reference"}
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        def mutator(vendor, candidate, mode):
            (candidate / "references" / "SAFETY_AND_SCENARIOS.md").write_bytes(b"changed")
            return (0, "{}", "")
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G139_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(gate, "_execute", side_effect=mutator):
            with self.assertRaisesRegex(gate.VerificationRefused, "changed during Checker"):
                gate.check(self.path, self.vendor, mode="native",
                           native_risk_approved=True, candidate_profile="g139")

    def test_g139_stored_exact_pins_are_full_sha256(self):
        self.assertRegex(gate.G139_CANDIDATE_SHA, r"\A[0-9a-f]{64}\Z")
        self.assertRegex(gate.G139_CANDIDATE_ZIP_SHA, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(len(gate.G139_MEMBERS), 3)

    def test_g139_inspect_cli_never_implies_execution(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# synthetic",
                 gate.G139_MEMBERS[2]: b"# synthetic"}
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        with patch.object(gate, "G139_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G139_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(sys, "argv", ["check", "--candidate-zip", str(self.path),
                  "--official-kit-zip", str(self.vendor), "--candidate-profile", "g139"]), \
             redirect_stdout(StringIO()) as output:
            code = gate.main()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["candidate_member_count"], 3)
        self.assertIn('"official_checker_executed": false', output.getvalue().lower())


    def test_stderr_warning_cannot_be_promoted_to_clean_official_pass(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": []})
        report = gate._sanitized_checker_result(
            0, payload, "Error: extra diagnostic printed by vendor", mode="docker")
        self.assertEqual(report["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertTrue(report["checker_stderr_present"])
        self.assertEqual(report["release_gate"], "HOLD")
        self.assertFalse(report["owner_release_approved"])
        self.assertNotIn("extra diagnostic", json.dumps(report))

    def test_nonzero_exit_with_zero_summary_still_fails(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": []})
        report = gate._sanitized_checker_result(2, payload, "", mode="docker")
        self.assertEqual(report["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertEqual(report["checker_exit_code"], 2)

    def test_boolean_summary_zero_is_not_int_zero(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": False, "warnings": 0, "info": 0}, "diagnostics": []})
        report = gate._sanitized_checker_result(0, payload, "", mode="docker")
        self.assertEqual(report["result"], "OFFICIAL_WARN_OR_FAIL_HOLD")
        self.assertEqual(report["checker_summary"], "UNVERIFIED_SUMMARY")

    def test_blank_stderr_retains_empty_diagnostic_semantics(self):
        payload = json.dumps({"status": "static-pass", "summary": {
            "errors": 0, "warnings": 0, "info": 0}, "diagnostics": []})
        report = gate._sanitized_checker_result(0, payload, " \t\n", mode="docker")
        self.assertEqual(report["result"], "OFFICIAL_STATIC_PASS_REVIEW_ONLY")
        self.assertFalse(report["checker_stderr_present"])
        self.assertEqual(report["release_gate"], "HOLD")



    def test_g147_review_variant_pins_full_sha256_and_reuses_exact_three_member_contract(self):
        self.assertRegex(gate.G147_CANDIDATE_SHA, r"\A[0-9a-f]{64}\Z")
        self.assertRegex(gate.G147_CANDIDATE_ZIP_SHA, r"\A[0-9a-f]{64}\Z")
        self.assertNotEqual(gate.G147_CANDIDATE_SHA, gate.G139_CANDIDATE_SHA)
        self.assertNotEqual(gate.G147_CANDIDATE_ZIP_SHA, gate.G139_CANDIDATE_ZIP_SHA)
        self.assertEqual(len(gate.G139_MEMBERS), 3)

    def test_g147_synthetic_exact_three_markdown_inspect_no_executable_and_hold(self):
        files = {
            gate.MEMBER: self.source,
            gate.G139_MEMBERS[1]: b"# synthetic review-only capability\n",
            gate.G139_MEMBERS[2]: b"# synthetic review-only safety\n",
        }
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        with patch.object(gate, "G147_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G147_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(gate, "_execute", side_effect=AssertionError("vendor executed")):
            receipt = gate.check(self.path, self.vendor, mode="inspect", candidate_profile="g147")
        self.assertEqual(receipt["candidate_profile"], "g147")
        self.assertEqual(receipt["candidate_member_count"], 3)
        self.assertEqual(receipt["release_gate"], "HOLD")
        self.assertFalse(receipt["official_checker_executed"])

    def test_g147_modified_reference_rejected_before_vendor_execution(self):
        files = {
            gate.MEMBER: self.source,
            gate.G139_MEMBERS[1]: b"# synthetic allowed reference\n",
            gate.G139_MEMBERS[2]: b"# synthetic baseline safety\n",
        }
        good = zip_bytes(files)
        self.path.write_bytes(good)
        files[gate.G139_MEMBERS[2]] = b"# unauthorized replacement\n"
        self.path.write_bytes(zip_bytes(files))
        with patch.object(gate, "G147_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G147_CANDIDATE_ZIP_SHA", sha256(good).hexdigest()), \
             patch.object(gate, "_execute", side_effect=AssertionError("vendor executed")):
            with self.assertRaisesRegex(gate.VerificationRefused, "SHA256"):
                gate.check(self.path, self.vendor, mode="docker", candidate_profile="g147")

    def test_g147_multifile_reference_contents_supplied_to_mock_only(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# synthetic capability\n",
                 gate.G139_MEMBERS[2]: b"# synthetic safety\n"}
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        def inspect_fake(_vendor, candidate, *, mode):
            self.assertEqual(mode, "native")
            self.assertEqual((candidate / "SKILL.md").read_bytes(), files[gate.MEMBER])
            for name in gate.G139_MEMBERS[1:]:
                self.assertEqual((candidate.parent / name).read_bytes(), files[name])
            return (0, json.dumps({"status": "static-pass",
                     "summary": {"errors": 0, "warnings": 0, "info": 0},
                     "diagnostics": []}), "")
        with patch.object(gate, "G147_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G147_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(gate, "_execute", side_effect=inspect_fake):
            result = gate.check(self.path, self.vendor, mode="native",
                                native_risk_approved=True, candidate_profile="g147")
        self.assertEqual(result["candidate_profile"], "g147")
        self.assertEqual(result["result"], "OFFICIAL_STATIC_PASS_REVIEW_ONLY")
        self.assertEqual(result["release_gate"], "HOLD")

    def test_g147_cli_inspect_must_exit_hold_without_official_success_claim(self):
        files = {gate.MEMBER: self.source,
                 gate.G139_MEMBERS[1]: b"# synthetic capability\n",
                 gate.G139_MEMBERS[2]: b"# synthetic safety\n"}
        raw = zip_bytes(files)
        self.path.write_bytes(raw)
        with patch.object(gate, "G147_CANDIDATE_SHA", sha256(self.source).hexdigest()), \
             patch.object(gate, "G147_CANDIDATE_ZIP_SHA", sha256(raw).hexdigest()), \
             patch.object(sys, "argv", [
                 "gate", "--candidate-zip", str(self.path), "--official-kit-zip",
                 str(self.vendor), "--candidate-profile", "g147"]), \
             redirect_stdout(StringIO()) as output:
            rc = gate.main()
        self.assertEqual(rc, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["candidate_profile"], "g147")
        self.assertEqual(report["release_gate"], "HOLD")
        self.assertFalse(report["official_checker_executed"])



    def test_g149_docker_refuses_remote_context_when_local_socket_unavailable(self):
        # Explicit approval of docker mode does NOT approve shipping G147 to a
        # caller-configured remote daemon, even if the Docker binary is present.
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=False), \
             patch.object(gate.subprocess, "run",
                          side_effect=AssertionError("Private mounts must not be sent")):
            with self.assertRaisesRegex(gate.VerificationRefused, "local Unix Docker"):
                gate._execute(self.path.parent, self.path.parent, mode="docker")

    def test_g149_docker_uses_pinned_local_endpoint_without_inherited_credentials(self):
        from subprocess import CompletedProcess
        import os
        outputs = [
            CompletedProcess([], 0, stdout=b"image-present", stderr=b""),
            CompletedProcess([], 0, stdout=b'{"status":"static-pass"}', stderr=b""),
        ]
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=True), \
             patch.dict(os.environ, {
                 "DOCKER_HOST": "tcp://malicious.example:2375",
                 "DOCKER_CONTEXT": "remote-work",
                 "DOCKER_TLS_VERIFY": "1",
                 "DOCKER_CERT_PATH": "/private/key",
             }), patch.object(gate.subprocess, "run", side_effect=outputs) as run:
            exit_code, stdout, stderr = gate._execute(
                self.path.parent, self.path.parent, mode="docker")
        self.assertEqual((exit_code, stdout, stderr),
                         (0, '{"status":"static-pass"}', ""))
        self.assertEqual(run.call_count, 2)
        inspect_call, execute_call = run.call_args_list
        for call in (inspect_call, execute_call):
            command = call.args[0]
            self.assertEqual(command[0], "/usr/bin/docker")
            self.assertIn("--host=unix:///var/run/docker.sock", command)
            self.assertIn("--config", command)
            env = call.kwargs["env"]
            self.assertEqual(env["DOCKER_HOST"], "unix:///var/run/docker.sock")
            self.assertEqual(env["DOCKER_CONFIG"], env["HOME"])
            self.assertNotIn("DOCKER_CONTEXT", env)
            self.assertNotIn("DOCKER_TLS_VERIFY", env)
            self.assertNotIn("DOCKER_CERT_PATH", env)
            self.assertFalse(call.kwargs["check"])
            self.assertEqual(call.kwargs["cwd"], self.path.parent.parent)
        argv = execute_call.args[0]
        for flag in ("--pull=never", "--network=none", "--read-only",
                     "--cap-drop=ALL", "--security-opt=no-new-privileges",
                     "--user=65534:65534", "--entrypoint=node"):
            self.assertIn(flag, argv)
        self.assertNotIn("--privileged", argv)
        self.assertNotIn("--network=host", argv)
        self.assertEqual(argv[-3:],
                         ["node:22-alpine", "/vendor/scripts/check-skill.mjs",
                          "/candidate/flowpilot-3"])

    def test_g149_missing_local_image_does_not_run_or_pull(self):
        from subprocess import CompletedProcess
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(gate.subprocess, "run",
                          return_value=CompletedProcess([], 1, b"", b"")) as run:
            with self.assertRaisesRegex(gate.VerificationRefused, "no pull"):
                gate._execute(self.path.parent, self.path.parent, mode="docker")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][-3:],
                         ["image", "inspect", "node:22-alpine"])

    def test_g149_docker_never_emits_untrusted_stderr_from_bad_vendor(self):
        from subprocess import CompletedProcess
        stderr = b"PRIVATE_OWNER_FILE_PATH"
        with patch.object(gate.shutil, "which", return_value="/usr/bin/docker"), \
             patch.object(gate, "_local_docker_socket_ready", return_value=True), \
             patch.object(gate.subprocess, "run", side_effect=[
                 CompletedProcess([], 0, b"", b""),
                 CompletedProcess([], 2, b'{"status":"fail"}', stderr)]):
            code, stdout, err = gate._execute(self.path.parent, self.path.parent,
                                              mode="docker")
        self.assertEqual(code, 2)
        self.assertEqual(err, stderr.decode())
        sanitized = gate._sanitized_checker_result(code, stdout, err, mode="docker")
        self.assertNotIn("PRIVATE_OWNER", json.dumps(sanitized))
        self.assertEqual(sanitized["release_gate"], "HOLD")

    def test_g149_explicit_native_still_uses_node_not_docker(self):
        from subprocess import CompletedProcess
        with patch.object(gate.shutil, "which", return_value="/usr/bin/node"), \
             patch.object(gate, "_local_docker_socket_ready",
                          side_effect=AssertionError("native uses Docker")), \
             patch.object(gate.subprocess, "run",
                          return_value=CompletedProcess([], 0, b"{}", b"")) as invoke:
            result = gate._execute(self.path.parent, self.path.parent, mode="native")
        self.assertEqual(result, (0, "{}", ""))
        self.assertEqual(invoke.call_args.args[0][0], "/usr/bin/node")



if __name__ == "__main__":
    unittest.main()
