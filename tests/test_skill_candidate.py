"""Purely offline tests for the Markdown-only candidate, not official Uliya validation."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "skill" / "projectready-nas"
SKILL = DIR / "SKILL.md"

class SkillDraftTests(unittest.TestCase):
    def test_identity(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: projectready-nas\n"))
        self.assertIn("description:", text)

    def test_markdown_only_layout(self):
        files = sorted(p.relative_to(DIR).as_posix() for p in DIR.rglob("*") if p.is_file())
        self.assertEqual(files, ["SKILL.md", "references/attribution.md", "references/catalog-actions.md", "references/decision-policy.md"])

    def test_direct_reference_resolves(self):
        refs = re.findall(r"\]\((references/[^)#]+\.md)\)", SKILL.read_text(encoding="utf-8"))
        self.assertEqual(refs, ["references/catalog-actions.md", "references/decision-policy.md", "references/attribution.md"])
        for ref in refs:
            path = (DIR / ref).resolve()
            self.assertTrue(path.is_relative_to(DIR.resolve()))
            self.assertTrue(path.is_file())

    def test_first_party_catalog_is_documented_but_not_runtime_authorized(self):
        text = SKILL.read_text(encoding="utf-8")
        official = (DIR / "references/catalog-actions.md").read_text(encoding="utf-8")
        for term in ("ug-filesystem", "ug-document", "file-agent", "document-agent",
                     "NOT live Agent registration", "NOT_CHECKED"):
            self.assertIn(term, text)
        for term in ("knowledgeStatus", "unknown", "effect=read", "approval=none",
                     "NOT_RUN", "sha256sum"):
            self.assertIn(term, official)

    def test_catalog_hardens_exceptions_to_read_only(self):
        text = SKILL.read_text(encoding="utf-8")
        official = (DIR / "references/catalog-actions.md").read_text(encoding="utf-8")
        self.assertIn("does NOT establish pagination/completeness", text)
        self.assertIn("selected files", text)
        self.assertIn("Never invoke", official)
        self.assertIn("Do not upload, transmit, copy, modify, rename, move or delete files.", text)

    def test_official_sensitive_materials_exclusion(self):
        text = SKILL.read_text(encoding="utf-8")
        policy = (DIR / "references/decision-policy.md").read_text(encoding="utf-8")
        attribution = (DIR / "references/attribution.md").read_text(encoding="utf-8")
        for marker in ("`.env`", "`.git`", "`config.json`", "browser sessions", "Do NOT probe", "redact", "NOT_CHECKED"):
            self.assertIn(marker, text)
        self.assertIn("NOT_CHECKED (restricted; do not probe or disclose the path)", policy)
        self.assertIn("instruction-only preflight guard", attribution)

    def test_report_redacts_sensitive_paths_and_example_never_claims_nas_evidence(self):
        text = SKILL.read_text(encoding="utf-8")
        response = text.split("## Response", 1)[1].split("## Safety", 1)[0]
        self.assertIn("display only `[restricted item]`", response)
        self.assertIn("never echo its original name", response)
        example = response.split("## Illustrative result", 1)[1]
        for phrase in ("synthetic scenario, NOT an actual NAS scan", "**NOT_CHECKED**, not MISSING",
                       "truncated", "VERSION_REVIEW", "NEEDS_REVIEW", "not READY",
                       "not a real file-agent reference"):
            self.assertIn(phrase, example)
        self.assertNotIn("secret", example.lower())

    def test_no_placeholders(self):
        for p in DIR.rglob("*.md"):
            self.assertIsNone(re.search(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", p.read_text(), re.I))

    def test_read_only_and_no_invented_commands(self):
        text = SKILL.read_text(encoding="utf-8")
        for term in ("read-only", "Do not invent Agent IDs", "Do not upload", "NOT_CHECKED"):
            self.assertIn(term, text)
        for term in ("sudo ", "curl ", "python "):
            self.assertNotIn(term, text)

    def test_conservative_gate(self):
        text = SKILL.read_text(encoding="utf-8")
        rule = (DIR / "references/decision-policy.md").read_text(encoding="utf-8")
        for term in ("NEEDS_REVIEW", "BLOCKED", "VERSION_REVIEW"):
            self.assertIn(term, text)
        self.assertIn("READY is possible only when", rule)
        self.assertIn("a demonstrably complete, authorized listing", rule)

if __name__ == "__main__":
    unittest.main()
