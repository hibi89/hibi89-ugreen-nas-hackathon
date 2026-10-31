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



if __name__ == "__main__":
    unittest.main()
