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
        self.assertEqual(files, ["SKILL.md", "references/attribution.md", "references/decision-policy.md"])

    def test_direct_reference_resolves(self):
        refs = re.findall(r"\]\((references/[^)#]+\.md)\)", SKILL.read_text(encoding="utf-8"))
        self.assertEqual(refs, ["references/decision-policy.md", "references/attribution.md"])
        for ref in refs:
            path = (DIR / ref).resolve()
            self.assertTrue(path.is_relative_to(DIR.resolve()))
            self.assertTrue(path.is_file())

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
