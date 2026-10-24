"""Strict synthetic tests; never assert actual official Creator or NAS validity."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_creator_source import CreatorReviewError, review

class CreatorReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.folder = self.base / "projectready-nas"
        (self.folder / "references").mkdir(parents=True)
        self.skill = self.folder / "SKILL.md"
        self.skill.write_text("---\nname: projectready-nas\ndescription: Demo\n---\n[reference](references/policy.md)\n", encoding="utf-8")
        (self.folder / "references/policy.md").write_text("# Policy\nread only\n", encoding="utf-8")
        self.baseline = self.base / "baseline.md"
        self.baseline.write_text("original", encoding="utf-8")

    def expected(self):
        return hashlib.sha256(self.skill.read_bytes()).hexdigest()

    def test_read_only_integrity_receipt(self):
        report = review(self.skill, self.expected(), self.baseline)
        self.assertEqual(report["assessment"], "LOCAL_SOURCE_INTEGRITY_REVIEW_PASS_ONLY")
        self.assertEqual(report["linked_markdown_files"], 1)
        self.assertFalse(report["same_bytes_as_baseline"])
        self.assertEqual(report["devpost_submission"], "NOT_SUBMITTED")

    def test_modified_file_cannot_reuse_reported_sha(self):
        sha = self.expected()
        self.skill.write_text(self.skill.read_text() + "tamper", encoding="utf-8")
        with self.assertRaises(CreatorReviewError):
            review(self.skill, sha, self.baseline)

    def test_missing_reference_fails(self):
        (self.folder / "references/policy.md").unlink()
        with self.assertRaises(CreatorReviewError):
            review(self.skill, self.expected(), self.baseline)

    def test_extra_file_fails(self):
        (self.folder / "notes.txt").write_text("unexpected")
        with self.assertRaises(CreatorReviewError):
            review(self.skill, self.expected(), self.baseline)

    def test_hidden_secret_fails(self):
        (self.folder / "references/policy.md").write_text("AKIA" + "A" * 16)
        with self.assertRaises(CreatorReviewError):
            review(self.skill, self.expected(), self.baseline)

    def test_mismatched_frontmatter_fails(self):
        self.skill.write_text(self.skill.read_text().replace("name: projectready-nas", "name: other"))
        with self.assertRaises(CreatorReviewError):
            review(self.skill, self.expected(), self.baseline)

    def test_symlink_reference_fails(self):
        ref = self.folder / "references/policy.md"
        ref.unlink()
        try:
            ref.symlink_to(self.baseline)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(CreatorReviewError):
            review(self.skill, self.expected(), self.baseline)

    def test_generated_source_never_mutated(self):
        before = self.skill.read_bytes()
        review(self.skill, self.expected(), self.baseline)
        self.assertEqual(self.skill.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()
