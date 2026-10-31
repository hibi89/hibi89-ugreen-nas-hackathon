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
            "errors": 0, "warnings": 0, "info": 0}})
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

    def test_inspect_command_never_claims_success(self):
        with patch.object(sys, "argv", ["check", "--candidate-zip", str(self.path),
                    "--official-kit-zip", str(self.vendor)]), redirect_stdout(StringIO()) as out:
            code = gate.main()
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())["official_checker_executed"])


if __name__ == "__main__":
    unittest.main()
