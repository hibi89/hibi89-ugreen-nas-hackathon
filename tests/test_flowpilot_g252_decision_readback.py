"""G252 read-only local owner decision binding and refusal regression."""
from __future__ import annotations
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from flowpilot_g251_owner_decision import run
from flowpilot_g252_decision_readback import verify, ReadbackRefused
from test_flowpilot_g251_owner_decision import example_evidence


class G252ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.evidence=self.root/"evidence.json"
        self.decision=self.root/"decision.json"
        self.evidence.write_text(json.dumps(example_evidence()),encoding="utf-8")
        result=run(self.evidence,self.decision,"hold",approve_read_evidence=True,
                   approve_save_decision=True)
        self.assertTrue(result["output_created"])
        self.expected_digest=result["decision_sha256"]

    def check(self):
        return verify(self.evidence,self.decision,approve_local_read=True,
                      expected_decision_sha256=self.expected_digest)

    def test_consent_required_before_either_read(self):
        with patch("flowpilot_g251_owner_decision.os.open",side_effect=AssertionError("UNEXPECTED_READ")):
            result=verify(self.evidence,self.decision)
        self.assertFalse(result["input_read"])
        self.assertEqual(result["release_gate"],"HOLD")

    def test_verified_manual_hold_binding(self):
        result=self.check()
        self.assertEqual(result["status"],"LOCAL_OWNER_DECISION_BINDING_VERIFIED_NOT_NAS")
        self.assertEqual(result["owner_choice"],"OWNER_HOLD")
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["decision_is_authenticated"])
        self.assertTrue(result["decision_receipt_sha_verified"])
        self.assertFalse(result["source_file_contents_opened"])
        self.assertFalse(result["external_transfer"])

    def test_changed_source_evidence_detected(self):
        doc=example_evidence()
        doc["scope_sha256"]="a"*64
        self.evidence.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_DECISION_EVIDENCE_CONFLICT"):
            self.check()

    def test_same_semantics_reformatted_source_refused(self):
        doc=example_evidence()
        self.evidence.write_text(json.dumps(doc,indent=2),encoding="utf-8")
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_DECISION_EVIDENCE_CONFLICT"):
            self.check()

    def test_modified_decision_scope_detected(self):
        doc=json.loads(self.decision.read_text())
        doc["review_scope_sha256"]="b"*64
        self.decision.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_DECISION_EVIDENCE_CONFLICT"):
            self.check()

    def test_illegal_ready_state_refused(self):
        doc=json.loads(self.decision.read_text())
        doc["ready_for_delivery"]=True
        self.decision.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_EVIDENCE_OR_DECISION_INVALID"):
            self.check()

    def test_duplicate_json_key_denied(self):
        self.decision.write_bytes(self.decision.read_bytes().replace(b'"schema":',b'"schema": "garbage", "schema":',1))
        with self.assertRaises(ReadbackRefused):self.check()

    def test_private_field_injection_rejected(self):
        doc=json.loads(self.decision.read_text())
        doc["source_path"]="/secret/source.pdf"
        self.decision.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(ReadbackRefused):self.check()

    def test_symlink_file_rejected(self):
        actual=self.root/"actual.json"
        actual.write_bytes(self.decision.read_bytes())
        self.decision.unlink()
        try:self.decision.symlink_to(actual)
        except (OSError,NotImplementedError):self.skipTest("No symlink privilege")
        with self.assertRaises(ReadbackRefused):self.check()

    def test_existing_input_not_modified(self):
        original_evidence=self.evidence.read_bytes()
        original_decision=self.decision.read_bytes()
        self.check()
        self.assertEqual(self.evidence.read_bytes(),original_evidence)
        self.assertEqual(self.decision.read_bytes(),original_decision)

    def test_valid_owner_choice_substitution_detected_by_out_of_band_sha(self):
        doc=json.loads(self.decision.read_text())
        doc["owner_choice"]="OWNER_SELECTED_ALTERNATIVE"
        self.decision.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_DECISION_EVIDENCE_CONFLICT"):
            self.check()

    def test_wrong_previous_sha_denied(self):
        with self.assertRaisesRegex(ReadbackRefused,"LOCAL_DECISION_EVIDENCE_CONFLICT"):
            verify(self.evidence,self.decision,approve_local_read=True,
                   expected_decision_sha256="f"*64)

    def test_missing_previous_sha_denied_without_read(self):
        with patch("flowpilot_g251_owner_decision.os.open",side_effect=AssertionError("UNEXPECTED_READ")):
            with self.assertRaisesRegex(ReadbackRefused,"EXPECTED_G251_DECISION_SHA_REQUIRED"):
                verify(self.evidence,self.decision,approve_local_read=True)

    def test_invalid_approval_type(self):
        with self.assertRaisesRegex(ReadbackRefused,"EXACT_READ_CONSENT_REQUIRED"):
            verify(self.evidence,self.decision,approve_local_read=1)

    def test_oversize_decision_refused(self):
        self.decision.write_bytes(b"z"*8193)
        with self.assertRaises(ReadbackRefused):self.check()

    def test_missing_decision_refused(self):
        self.decision.unlink()
        with self.assertRaises(ReadbackRefused):self.check()


if __name__ == "__main__":unittest.main()
