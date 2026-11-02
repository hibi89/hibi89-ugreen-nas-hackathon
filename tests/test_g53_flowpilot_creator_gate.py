"""G53: failed or forged creator handoff never becomes a release PASS."""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from g53_flowpilot_creator_gate import (
    EXPECTED_KIT_SHA, EXPECTED_SKILL_SHA, G188_SKILL_SHA, review_creator_evidence
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

    def test_g198_g188_profile_is_separate_and_never_release(self):
        self.assertEqual(G188_SKILL_SHA,
                         "4baf816e7deafa7dec544d93209f8ae3d1fb6400515212d2eb1d9b5fe0f6acca")
        draft = b"---\nname: flowpilot-3\ndescription: Safe only\n---\n# Goal\n"
        h = hashlib.sha256(draft).hexdigest()
        evidence = declared(generated_skill_sha256=h, checker_skill_sha256=h)
        self.assertEqual(review_creator_evidence(draft, evidence)["status"], "WRONG_SKILL_ID")
        r = review_creator_evidence(draft, evidence, candidate_profile="g188")
        self.assertEqual(r["candidate"], "flowpilot-3")
        self.assertEqual(r["status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["release_gate"], "HOLD")
        self.assertIs(r["official_creator_execution_independently_verified"], False)

    def test_g198_wrong_profile_and_old_source_refused(self):
        r = review_creator_evidence(SKILL, declared(), candidate_profile="g188")
        self.assertEqual(r["status"], "WRONG_SKILL_ID")
        self.assertEqual(review_creator_evidence(SKILL, declared(),
                         candidate_profile="unsupported")["status"], "INVALID_CANDIDATE_PROFILE")

    def test_g210_round1_creator_only_report_is_reviewable_but_not_releasable(self):
        creator_only = {k: v for k, v in declared().items()
                        if not k.startswith("checker_")}
        r = review_creator_evidence(SKILL, creator_only)
        self.assertEqual(r["status"], "SOURCE_MATCHED_OPERATOR_ATTESTATION_ONLY")
        self.assertEqual(r["checker_report_status"], "NOT_REPORTED_OPTIONAL_ROUND1")
        self.assertFalse(r["official_creator_execution_independently_verified"])
        self.assertFalse(r["official_checker_execution_independently_verified"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g210_new_source_without_checker_remains_review_hold(self):
        changed = SKILL + b"\n# independently created source\n"
        sha = hashlib.sha256(changed).hexdigest()
        creator_only = {k: v for k, v in
                        declared(generated_skill_sha256=sha).items()
                        if not k.startswith("checker_")}
        r = review_creator_evidence(changed, creator_only)
        self.assertEqual(r["status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["checker_report_status"], "NOT_REPORTED_OPTIONAL_ROUND1")
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g210_partial_checker_evidence_refused_without_false_pass(self):
        creator_only = {k: v for k, v in declared().items()
                        if not k.startswith("checker_")}
        creator_only["checker_status"] = "static-pass"
        r = review_creator_evidence(SKILL, creator_only)
        self.assertEqual(r["status"], "INCOMPLETE_CHECKER_REPORT")
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g210_creator_sha_mismatch_without_checker_cannot_pass(self):
        creator_only = {k: v for k, v in declared().items()
                        if not k.startswith("checker_")}
        creator_only["generated_skill_sha256"] = "f" * 64
        r = review_creator_evidence(SKILL, creator_only)
        self.assertEqual(r["status"], "GENERATED_SOURCE_SHA_MISMATCH")
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g211_name_after_description_is_reviewed_not_wrong_identity(self):
        content = (b"---\ndescription: Bounded read-only Skill\n"
                   b"name: flowpilot-nas\n---\n# New source\n")
        sha = hashlib.sha256(content).hexdigest()
        creator_only = {k: v for k, v in
                        declared(generated_skill_sha256=sha).items()
                        if not k.startswith("checker_")}
        r = review_creator_evidence(content, creator_only)
        self.assertEqual(r["status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["checker_report_status"], "NOT_REPORTED_OPTIONAL_ROUND1")
        self.assertFalse(r["official_creator_execution_independently_verified"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g211_quoted_name_crlf_alternate_profile(self):
        content = (b"---\r\ndescription: Document workflow\n"
                   b"name: 'flowpilot-3'\r\n---\r\n# New Skill\n")
        sha = hashlib.sha256(content).hexdigest()
        creator_only = {k: v for k, v in
                        declared(generated_skill_sha256=sha).items()
                        if not k.startswith("checker_")}
        r = review_creator_evidence(content, creator_only,
                                    candidate_profile="g188")
        self.assertEqual(r["status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g211_duplicate_name_refused(self):
        content = (b"---\ndescription: Review\nname: flowpilot-nas\n"
                   b"name: flowpilot-nas\n---\n# Duplicate\n")
        sha = hashlib.sha256(content).hexdigest()
        r = review_creator_evidence(content,
                declared(generated_skill_sha256=sha, checker_skill_sha256=sha))
        self.assertEqual(r["status"], "WRONG_SKILL_ID")

    def test_g211_body_name_cannot_replace_missing_metadata(self):
        content = (b"---\ndescription: Missing name\n---\n"
                   b"# Body\nname: flowpilot-nas\n")
        sha = hashlib.sha256(content).hexdigest()
        r = review_creator_evidence(content,
                declared(generated_skill_sha256=sha, checker_skill_sha256=sha))
        self.assertEqual(r["status"], "WRONG_SKILL_ID")

    def test_g211_wrong_profile_still_refused_after_reorder(self):
        content = (b"---\ndescription: Wrong profile\n"
                   b"name: flowpilot-3\n---\n# Body\n")
        sha = hashlib.sha256(content).hexdigest()
        r = review_creator_evidence(content,
                declared(generated_skill_sha256=sha, checker_skill_sha256=sha))
        self.assertEqual(r["status"], "WRONG_SKILL_ID")

    def test_no_skill_source(self):
        self.assertEqual(review_creator_evidence(b"not a skill",declared())["status"],"WRONG_SKILL_ID")

if __name__=="__main__":
    unittest.main()
