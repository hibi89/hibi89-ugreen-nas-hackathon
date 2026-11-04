"""G251 independent owner-choice receipt from synthetic redacted G249 evidence."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_g251_owner_decision import run, OwnerDecisionRefused


def example_evidence():
    return {"schema":"flowpilot-local-version-evidence-g249-v1",
            "status":"REDACTED_LOCAL_VERSION_EVIDENCE_NOT_NAS",
            "scope_sha256":"e"*64, "required_count":1, "version_candidate_count":1,
            "stages":["SCOPED_READ","VERSION_COMPARE","OWNER_REVIEW","REDACTED_EVIDENCE"],
            "findings":[{"index":1,"state":"VERSION_REVIEW"}],
            "manual_owner_review_required":True,"auto_selected_final_version":False,
            "owner_file_contents_opened":False,"original_files_modified":False,
            "owner_paths_included":False,"nas_verified":False,"release_gate":"HOLD"}

class G251DecisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.evidence=self.root/"version-evidence.json"
        self.destination=self.root/"owner-choice.json"
        self.write_evidence(example_evidence())

    def write_evidence(self,item):
        self.evidence.write_text(json.dumps(item),encoding="utf-8")

    def run_it(self, **kw):
        return run(self.evidence,self.destination,"alternative",**kw)

    def test_before_consent_no_file_access_or_output(self):
        with patch("flowpilot_g251_owner_decision.os.open",side_effect=AssertionError("unauthorized read")):
            result=self.run_it()
        self.assertEqual(result["status"],"WAITING_LOCAL_EVIDENCE_READ_APPROVAL")
        self.assertFalse(self.destination.exists())

    def test_second_consent_distinct_from_read(self):
        result=self.run_it(approve_read_evidence=True)
        self.assertEqual(result["status"],"WAITING_SEPARATE_OWNER_DECISION_APPROVAL")
        self.assertEqual(result["choices"],["hold","primary","alternative"])
        self.assertFalse(self.destination.exists())

    def test_no_write_without_first_consent(self):
        with self.assertRaisesRegex(OwnerDecisionRefused,"INDEPENDENT_READ_APPROVAL_REQUIRED"):
            self.run_it(approve_save_decision=True)

    def test_actual_choice_is_redacted_not_ready(self):
        result=self.run_it(approve_read_evidence=True,approve_save_decision=True)
        self.assertTrue(result["output_created"])
        raw=self.destination.read_bytes()
        self.assertEqual(result["decision_sha256"],sha256(raw).hexdigest())
        doc=json.loads(raw)
        self.assertEqual(doc["owner_choice"],"OWNER_SELECTED_ALTERNATIVE")
        self.assertTrue(doc["manual_selection_not_source_verified"])
        self.assertFalse(doc["ready_for_delivery"])
        self.assertFalse(doc["nas_capability_verified"])
        self.assertNotIn(str(self.root),raw.decode())
        self.assertNotIn("version-evidence.json",raw.decode())

    def test_holder_may_explicitly_defer(self):
        result=run(self.evidence,self.destination,"hold",approve_read_evidence=True,approve_save_decision=True)
        self.assertTrue(result["output_created"])
        self.assertEqual(json.loads(self.destination.read_text())["owner_choice"],"OWNER_HOLD")

    def test_invalid_choice_cannot_create(self):
        with self.assertRaisesRegex(OwnerDecisionRefused,"EXACT_OWNER_CHOICE_REQUIRED"):
            run(self.evidence,self.destination,"latest-by-mtime",approve_read_evidence=True,approve_save_decision=True)
        self.assertFalse(self.destination.exists())

    def test_wrong_schema_fails_closed(self):
        doc=example_evidence();doc["nas_verified"]=True
        self.write_evidence(doc)
        with self.assertRaisesRegex(OwnerDecisionRefused,"UNSUPPORTED_OR_UNVERIFIED_VERSION_EVIDENCE"):
            self.run_it(approve_read_evidence=True,approve_save_decision=True)

    def test_extra_path_field_fails_closed(self):
        doc=example_evidence();doc["private_path"]="/private-file.pdf"
        self.write_evidence(doc)
        with self.assertRaises(OwnerDecisionRefused):
            self.run_it(approve_read_evidence=True,approve_save_decision=True)

    def test_duplicate_json_keys_fail_closed(self):
        self.evidence.write_text('{"schema":"x","schema":"y"}',encoding="utf-8")
        with self.assertRaises(OwnerDecisionRefused):
            self.run_it(approve_read_evidence=True)

    def test_large_evidence_refused(self):
        self.evidence.write_bytes(b"x"*10001)
        with self.assertRaisesRegex(OwnerDecisionRefused,"UNTRUSTED_EVIDENCE_FILE"):
            self.run_it(approve_read_evidence=True)

    def test_existing_decision_never_overwritten(self):
        self.destination.write_bytes(b"original decision")
        with self.assertRaisesRegex(OwnerDecisionRefused,"CREATE_ONLY_DECISION_OUTPUT_REFUSED"):
            self.run_it(approve_read_evidence=True,approve_save_decision=True)
        self.assertEqual(self.destination.read_bytes(),b"original decision")

    def test_symlink_input_refused(self):
        other=self.root/"other.json"; other.write_text(json.dumps(example_evidence()))
        self.evidence.unlink()
        try:self.evidence.symlink_to(other)
        except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
        with self.assertRaises(OwnerDecisionRefused):
            self.run_it(approve_read_evidence=True)

    def test_multiple_requirements_not_supported_yet(self):
        doc=example_evidence();doc["required_count"]=2
        self.write_evidence(doc)
        with self.assertRaises(OwnerDecisionRefused):
            self.run_it(approve_read_evidence=True)

if __name__=="__main__":unittest.main()
