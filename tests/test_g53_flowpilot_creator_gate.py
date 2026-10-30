"""G53: failed or forged creator handoff never becomes a release PASS."""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from g53_flowpilot_creator_gate import (
    EXPECTED_KIT_SHA, EXPECTED_SKILL_SHA, review_creator_evidence
)

SKILL=(ROOT/"skill/flowpilot-nas/SKILL.md").read_bytes()

def declared(**changes):
    base={"kit_sha256":EXPECTED_KIT_SHA,
          "generated_skill_sha256":EXPECTED_SKILL_SHA,
          "checker_skill_sha256":EXPECTED_SKILL_SHA,
          "generation_performed":True,"official_tool_loaded":True,
          "checker_status":"static-pass","checker_errors":0,
          "checker_warnings":0,"checker_info":0}
    return {**base,**changes}

class CreatorGate(unittest.TestCase):
    def test_missing_creator_report_is_blocked(self):
        r=review_creator_evidence(None,None)
        self.assertEqual(r["status"],"CREATOR_NOT_EVIDENCED")
        self.assertEqual(r["release_gate"],"HOLD")

    def test_source_matched_attestation_is_not_independent_proof(self):
        self.assertEqual(hashlib.sha256(SKILL).hexdigest(),EXPECTED_SKILL_SHA)
        r=review_creator_evidence(SKILL,declared())
        self.assertEqual(r["status"],"SOURCE_MATCHED_OPERATOR_ATTESTATION_ONLY")
        self.assertIs(r["official_creator_execution_independently_verified"],False)
        self.assertIs(r["owner_release_approved"],False)
        self.assertIs(r["devpost_submitted"],False)

    def test_tampered_creator_skill_requires_review(self):
        forged=SKILL+b"\n# edited outside reviewed SHA\n"
        h=hashlib.sha256(forged).hexdigest()
        r=review_creator_evidence(forged,declared(generated_skill_sha256=h,checker_skill_sha256=h))
        self.assertEqual(r["status"],"GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")

    def test_windows_crlf_source_is_valid_identity_but_not_pinned_proof(self):
        # Windows-generated Skill bytes may use CRLF. Identity is semantic,
        # yet SHA256 receipts must remain bound to exact byte content.
        crlf = SKILL.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        self.assertTrue(crlf.startswith(b"---\r\nname: flowpilot-nas\r\n"))
        digest = hashlib.sha256(crlf).hexdigest()
        approved = declared(generated_skill_sha256=digest,
                            checker_skill_sha256=digest)
        report = review_creator_evidence(crlf, approved)
        self.assertEqual(report["status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(report["release_gate"], "HOLD")
        denied = review_creator_evidence(crlf, declared())
        self.assertEqual(denied["status"], "GENERATED_SOURCE_SHA_MISMATCH")

    def test_stale_checker_cannot_certify_new_source(self):
        forged=SKILL+b"\n"
        h=hashlib.sha256(forged).hexdigest()
        r=review_creator_evidence(forged,declared(generated_skill_sha256=h))
        self.assertEqual(r["status"],"CHECKER_SOURCE_SHA_MISMATCH")

    def test_missing_official_generation_refuses(self):
        self.assertEqual(review_creator_evidence(SKILL,declared(generation_performed=False))["status"],
                         "CREATOR_NOT_EVIDENCED")

    def test_unapproved_kit_version_requires_review(self):
        self.assertEqual(review_creator_evidence(SKILL,declared(kit_sha256="0"*64))["status"],
                         "KIT_VERSION_REVIEW_REQUIRED")

    def test_checker_errors_and_bool_zero_rejected(self):
        for kw in ({"checker_errors":1},{"checker_info":True},{"checker_status":"not-uploadable"}):
            with self.subTest(kw=kw):
                self.assertEqual(review_creator_evidence(SKILL,declared(**kw))["status"],
                                 "CHECKER_RESULT_NOT_CLEAN")

    def test_invalid_and_incomplete_reports(self):
        self.assertEqual(review_creator_evidence(SKILL,{})["status"],"INCOMPLETE_CREATOR_REPORT")
        self.assertEqual(review_creator_evidence(SKILL,declared(generated_skill_sha256="??"))["status"],
                         "INVALID_SHA_FORMAT")

    def test_no_skill_source(self):
        self.assertEqual(review_creator_evidence(b"not a skill",declared())["status"],"WRONG_SKILL_ID")

if __name__=="__main__":
    unittest.main()
