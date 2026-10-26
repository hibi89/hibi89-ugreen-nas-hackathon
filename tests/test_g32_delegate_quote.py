"""G32 quotation and fail-closed source regression; NOT vendor validation."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"docs/submission/checker_inputs"
class DelegateQuotationTests(unittest.TestCase):
    def test_exactly_two_single_quoted_standard_examples(self):
        s=(P/"G32_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
        commands=re.findall(r"`delegate --target (file-agent|document-agent) --instruction ([^`]+)`",s)
        self.assertEqual(["file-agent","document-agent"],[n for n,_ in commands])
        for _,instruction in commands:
            self.assertTrue(instruction.startswith("'") and instruction.endswith("'"))
            self.assertIn("Do not",instruction)
            self.assertNotIn("$FILE_AGENT_INSTRUCTION",instruction)
            self.assertNotIn("$DOCUMENT_AGENT_INSTRUCTION",instruction)
        self.assertIn("mandatory binding",s)
        self.assertIn("owner-approved",s)
    def test_g31_original_still_uses_rejected_double_quotes(self):
        old=(P/"G31_20261025/projectready-nas/SKILL.md").read_text(encoding="utf-8")
        new=(P/"G32_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('--instruction "$FILE_AGENT_INSTRUCTION"',old)
        self.assertIn('--instruction "$DOCUMENT_AGENT_INSTRUCTION"',old)
        self.assertNotIn('--instruction "$FILE_AGENT_INSTRUCTION"',new)
        self.assertNotIn('--instruction "$DOCUMENT_AGENT_INSTRUCTION"',new)
    def test_no_unapproved_runtime_or_false_pass(self):
        s=(P/"G32_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
        for term in ("NOT_CHECKED","waiting_user","owner","permission","read-only"):
            self.assertIn(term,s)
        self.assertNotIn("G32 static-pass",s)
if __name__=="__main__":
    unittest.main()
