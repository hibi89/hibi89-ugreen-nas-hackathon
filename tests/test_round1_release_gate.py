"""Offline fail-closed release checker tests, no official services."""
import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from round1_release_gate import audit,markdown,ReleaseAuditError
class ReleaseAuditTests(unittest.TestCase):
 def setUp(self):
    self.zip=b"PK\x03\x04archive"
    self.pdf=b"%PDF-1.7draft"
    self.data={
      "kind":"UGREEN_ROUND1_PREVIEW_NOT_SUBMITTED",
      "official_rules_url":"https://ugreenhackathon.devpost.com/rules",
      "sha256_zip":hashlib.sha256(self.zip).hexdigest(),"zip_bytes":len(self.zip),
      "zip_member_count":4,"zip_contains_markdown_only":True,
      "zip_members":[{"path":x} for x in [
        "projectready-nas/SKILL.md","projectready-nas/references/decision-policy.md",
        "projectready-nas/references/catalog-actions.md","projectready-nas/references/attribution.md"]],
      "pdf":{"sha256":hashlib.sha256(self.pdf).hexdigest(),"bytes":len(self.pdf),
             "pages":1,"official_questions_in_pdf":10,"content_extractable":True},
      "proposal_question_count":10,"proposal_answer_words":351,
      "entrant_approval":"PENDING","license_and_dataflow_review":"NOT_CLEARED",
      "official_uliya_checker":"NOT_RUN","live_nas_validation":"NOT_RUN",
      "devpost_submission":"NOT_SUBMITTED",
    }
 def test_technical_pass_never_submission_ready(self):
    r=audit(self.data,self.zip,self.pdf)
    self.assertEqual(r["assessment"],"OFFLINE_TECHNICAL_PREVIEW_PASS")
    self.assertEqual(r["release_decision"],"NOT_APPROVED_FOR_SUBMISSION")
    self.assertIn("NOT SUBMITTED",markdown(r))
 def test_round1_required_vs_finalist_only_gates(self):
    report=audit(self.data,self.zip,self.pdf)
    round1={item["gate"] for item in report["required_reviews"]}
    deferred={item["gate"] for item in report["other_incomplete"]}
    self.assertIn("official_creation_tool_use",round1)
    self.assertIn("sdk_license_and_attribution",round1)
    self.assertIn("round1_dataflow_disclosure",round1)
    self.assertNotIn("real_nas_runtime",round1)
    self.assertNotIn("official_checker_execution",round1)
    self.assertIn("real_nas_runtime",deferred)
    self.assertIn("official_checker_execution",deferred)
    self.assertIn("Finalist-only",markdown(report))
 def test_zip_tamper_fails(self):
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip+b"x",self.pdf)
 def test_pdf_tamper_fails(self):
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf+b"x")
 def test_fake_license_clearance_fails(self):
    self.data["license_and_dataflow_review"]="CLEARED"
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf)
 def test_fake_submission_fails(self):
    self.data["devpost_submission"]="SUBMITTED"
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf)
 def test_fake_checker_fails(self):
    self.data["official_uliya_checker"]="PASS"
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf)
 def test_question_loss_fails(self):
    self.data["pdf"]["official_questions_in_pdf"]=9
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf)
 def test_duplicate_member_fails(self):
    self.data["zip_members"][1]["path"]=self.data["zip_members"][0]["path"]
    with self.assertRaises(ReleaseAuditError):audit(self.data,self.zip,self.pdf)
if __name__=="__main__":unittest.main()
