"""G52 regression: proposal proof must match the exact-source Uliya static checker."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PIN="47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"
RUN="40505339535"

class ProposalProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa=json.loads((ROOT/"docs/submission/flowpilot_round1_qas_20261027.json").read_text(encoding="utf-8"))
        cls.builder=(ROOT/"tools/flowpilot_round1_preview.py").read_text(encoding="utf-8")

    def test_q8_static_pass_but_creator_pending(self):
        answer=self.qa["questions"][7]["answer"]
        for phrase in ("static checker", "0 errors", "0 warnings", "0 info", RUN, "Official Creator generation"):
            self.assertIn(phrase,answer)

    def test_q10_does_not_claim_real_nas(self):
        answer=self.qa["questions"][9]["answer"]
        self.assertIn("Static validation does not prove",answer)
        self.assertIn("real NAS completeness",answer)
        self.assertIn("entrant approval",answer)

    def test_exact_skill_sha_and_build_manifest(self):
        skill=(ROOT/"skill/flowpilot-nas/SKILL.md").read_bytes()
        self.assertEqual(hashlib.sha256(skill).hexdigest(),PIN)
        self.assertIn('CHECKER_RUN="https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/'+RUN+'"',self.builder)
        self.assertIn('"official_checker":CHECKER_STATUS',self.builder)
        self.assertIn('G52 OWNER REVIEW DRAFT - NOT SUBMITTED',self.builder)

    def test_rights_creator_and_submission_not_claimed(self):
        self.assertEqual(self.qa["status"],"OWNER_REVIEW_NOT_SUBMITTED")
        disclosure=self.qa["disclosure"]
        self.assertIn("NOT yet been generated through the official Uliya Skill Creation Tool",disclosure)
        self.assertIn("Actual NAS execution",disclosure)
        self.assertIn('"official_creator":"NOT_RUN"',self.builder)
        self.assertIn('"devpost":"NOT_SUBMITTED"',self.builder)

if __name__=="__main__":unittest.main()
