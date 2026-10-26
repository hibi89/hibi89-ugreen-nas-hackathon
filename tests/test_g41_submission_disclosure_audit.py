"""G41 owner-independent disclosure and hold tests; no auto-approval."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import g41_submission_disclosure_audit as g
D={
 "ai_assistance":"OpenAI ChatGPT and Codex assisted the creator.",
 "platform":"UGREEN kit license has not been cleared or verified.",
 "other_libraries":"Python, ReportLab and pypdf offline.",
 "data_flow":"Local versus cloud data flow is unverified."
}
SKILL="UGREEN ChatGPT Codex source: https://ai.ugreen.com/pages/hackathon-starter-kit license rights are still pending"
class G41Tests(unittest.TestCase):
 def test_ai_and_source_identified(self):
  x=g.declarations({"disclosures":D},SKILL)
  self.assertEqual(x["ai_tools_in_pdf"],["OpenAI ChatGPT","OpenAI Codex"])
  self.assertFalse(x["applicable_license_disclosure_complete"])
 def test_pymupdf_in_qa_only_missing_in_pdf_is_flagged(self):
  x=g.declarations({"disclosures":D},SKILL)
  self.assertEqual(x["qa_only_pymupdf_disclosure_review"],"OPEN_QA_DEPENDENCY_INVENTORY")
 def test_pymupdf_can_be_listed_without_claiming_rights(self):
  d=dict(D,other_libraries=D["other_libraries"]+" PyMuPDF QA rasterizer.")
  x=g.declarations({"disclosures":d},SKILL)
  self.assertEqual(x["qa_only_pymupdf_disclosure_review"],"COMPLETE")
  self.assertFalse(x["applicable_license_disclosure_complete"])
 def test_missing_ai_disclosure_refuses(self):
  with self.assertRaisesRegex(ValueError,"AI development tools"):
   g.declarations({"disclosures":dict(D,ai_assistance="AI assisted.")},SKILL)
 def test_missing_processing_unknown_refuses(self):
  with self.assertRaisesRegex(ValueError,"processing"):
   g.declarations({"disclosures":dict(D,data_flow="No data leaves.")},SKILL)
 def test_fabricated_license_pass_refuses(self):
  with self.assertRaisesRegex(ValueError,"License uncertainty disappeared"):
   g.declarations({"disclosures":dict(D,platform="UGREEN MIT License granted")},SKILL.replace("license rights are still pending","license cleared"))
 def test_no_unspecified_artifact_dir(self):
  with self.assertRaisesRegex(ValueError,"Missing/symlinked artifact"):
   g.assess(ROOT/"not-a-g41-original-artifact-dir")
 def test_exact_fixed_digests(self):
  self.assertEqual(len(g.SHA_PDF),64)
  self.assertNotEqual(g.SHA_PDF,g.SHA_ZIP)
  self.assertNotEqual(g.SHA_ZIP,g.SHA_SOURCE)
if __name__=="__main__":unittest.main()
