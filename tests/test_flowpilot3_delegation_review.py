"""G99 known failure regression; no official Uliya invocation."""
import sys
from pathlib import Path
import unittest
from hashlib import sha256

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot3_delegation_review import review_source


class DelegationGateTests(unittest.TestCase):
    def setUp(self):
        self.source = ("---\nname: flowpilot-3\ndescription: Scope-safe review\n---\n"
            "# Orchestration\n1. Gate scope and consent.\n"
            "2. Delegate CHECK_REQUIRED REVIEW_VERSIONS HANDOFF_AUDIT SUMMARIZE_SELECTED to file-agent.\n"
            "3. After approved references and separate consent, delegate to document-agent.\n"
            "4. Maintain scope reference evidence. Optional sha256sum requires separate file consent.\n"
            "# Result classification\n").encode()

    def test_valid_workflow_still_holds_release(self):
        result = review_source(self.source)
        self.assertEqual(result["status"], "STRUCTURAL_PASS_OFFICIAL_CHECKER_REQUIRED")
        self.assertEqual(result["skill_sha256"], sha256(self.source).hexdigest())
        self.assertFalse(result["official_checker_executed"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_missing_summary_inventory_fails_closed(self):
        issues = review_source(self.source.replace(b" SUMMARIZE_SELECTED", b""))["issues"]
        self.assertIn("SUMMARY_MISSING_FILE_AGENT_INVENTORY", issues)

    def test_unbound_delegate_template_fails_closed(self):
        issues = review_source(self.source + b"delegate --target file-agent --instruction '<include path>'\n")["issues"]
        self.assertIn("UNBOUND_INSTRUCTION_PLACEHOLDER", issues)

    def test_missing_document_agent_fails_closed(self):
        issues = review_source(self.source.replace(b"document-agent", b"unbound-agent"))["issues"]
        self.assertIn("MISSING_DELEGATION_CHAIN", issues)

    def test_non_utf8_fails_closed(self):
        self.assertIn("INVALID_UTF8", review_source(self.source + b"\xff")["issues"])

    def test_wrong_candidate_identity_fails_closed(self):
        issues = review_source(self.source.replace(b"flowpilot-3", b"flowpilot-nas"))["issues"]
        self.assertIn("UNEXPECTED_SKILL_ID_OR_FRONTMATTER", issues)


if __name__ == "__main__":
    unittest.main()
