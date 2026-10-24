"""Negative and positive offline package preflight tests, never real SDK/NAS."""
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from round1_package_audit import PackageError, audit_skill, build_candidate_zip


class Round1PackageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "projectready-nas"
        (self.root / "references").mkdir(parents=True)
        (self.root / "SKILL.md").write_text(
            "---\nname: projectready-nas\ndescription: Test candidate.\n---\n"
            "[policy](references/decision-policy.md) [credit](references/attribution.md)\n")
        (self.root / "references/decision-policy.md").write_text("Review if unclear.")
        (self.root / "references/attribution.md").write_text(
            "# AI Tools\nChatGPT\n# Third-Party Components\nNone bundled\n# Data Flow\nNo outbound services\n")

    def test_actual_repository_skill_candidate(self):
        candidate = Path(__file__).resolve().parents[1] / "skill" / "projectready-nas"
        result = audit_skill(candidate)
        self.assertEqual(result["file_count"], 4)
        self.assertEqual(result["official_validator"], "NOT_RUN")
        with zipfile.ZipFile(BytesIO(build_candidate_zip(candidate))) as z:
            self.assertEqual(len(z.namelist()), 4)

    def test_accept_minimum_markdown_package(self):
        self.assertEqual(audit_skill(self.root)["file_count"], 3)

    def test_zip_deterministic_and_restricted(self):
        data = build_candidate_zip(self.root)
        self.assertEqual(data, build_candidate_zip(self.root))
        with zipfile.ZipFile(BytesIO(data)) as z:
            self.assertEqual(len(z.namelist()), 3)
            self.assertTrue(all(p.startswith("projectready-nas/") and p.endswith(".md") for p in z.namelist()))

    def test_reject_executable(self):
        (self.root / "bad.py").write_text("pass")
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_unlinked_reference(self):
        (self.root / "references/unlinked.md").write_text("not linked")
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_missing_reference(self):
        (self.root / "references/decision-policy.md").unlink()
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_missing_skill(self):
        (self.root / "SKILL.md").unlink()
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_wrong_folder_name(self):
        other = self.root.rename(self.root.parent / "Wrong_Name")
        with self.assertRaises(PackageError): audit_skill(other)

    def test_reject_oversized_description(self):
        p = self.root / "SKILL.md"
        p.write_text(p.read_text().replace("Test candidate.", "x" * 1025))
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_oversized_file(self):
        (self.root / "references/decision-policy.md").write_text("x" * (1024 * 1024 + 1))
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_duplicate_frontmatter(self):
        p = self.root / "SKILL.md"
        p.write_text(p.read_text().replace("name: projectready-nas", "name: projectready-nas\nname: projectready-nas"))
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_secret(self):
        (self.root / "references/decision-policy.md").write_text("AKIA" + "A" * 16)
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_todo(self):
        (self.root / "references/decision-policy.md").write_text("TODO")
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_missing_disclosures(self):
        (self.root / "references/attribution.md").write_text("# AI Tools\n# Third-Party Components\n")
        with self.assertRaises(PackageError): audit_skill(self.root)

    def test_reject_symlink(self):
        target = self.root.parent / "x.md"
        target.write_text("not owned")
        try:
            (self.root / "references/linked.md").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unsupported")
        with self.assertRaises(PackageError): audit_skill(self.root)


if __name__ == "__main__":
    unittest.main()
