"""G67 exact Creator candidate, proposed PDF/ZIP and release-HOLD regressions."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import g67_creator_round1_preview as preview


class G67CreatorPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.work.name)
        cls.report = preview.build(cls.folder)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_exact_candidate_not_original(self):
        actual = hashlib.sha256(preview.SKILL.read_bytes()).hexdigest()
        self.assertEqual(actual, preview.PIN)
        self.assertEqual(actual, self.report["skill_sha256"])
        self.assertNotEqual(actual,
            hashlib.sha256((ROOT / "skill/flowpilot-nas/SKILL.md").read_bytes()).hexdigest())

    def test_zip_one_markdown_entry_exact_bytes(self):
        path = self.folder / (preview.FILEROOT + ".zip")
        with ZipFile(path) as z:
            self.assertEqual(z.namelist(), ["flowpilot-nas/SKILL.md"])
            self.assertEqual(z.read("flowpilot-nas/SKILL.md"), preview.SKILL.read_bytes())
        self.assertTrue(self.report["zip_composition"]["source_exact_match"])

    def test_pdf_one_page_all_official_questions(self):
        path = self.folder / (preview.FILEROOT + ".pdf")
        pdf = PdfReader(path)
        self.assertEqual(len(pdf.pages), 1)
        text = pdf.pages[0].extract_text()
        for i in range(1, 11):
            self.assertIn(f"Q{i}.", text)
        self.assertIn(preview.PIN, "".join(text.split()))
        self.assertIn("Owner release: HOLD", " ".join(text.split()))

    def test_qas_current_creator_and_no_false_nas_claim(self):
        skill, qs, disclosure, count = preview.validate_inputs()
        self.assertEqual(len(qs), 10)
        self.assertLessEqual(count, 500)
        self.assertGreater(count, 100)
        self.assertIn("Skill Creation Tool", qs[7]["answer"])
        self.assertIn("40547404706", qs[7]["answer"])
        self.assertIn("Codex", disclosure)
        self.assertNotIn("has NOT yet been generated", disclosure)

    def test_frozen_source_sha_refuses_drift(self):
        with patch.object(preview, "PIN", "0" * 64):
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                preview.validate_inputs()

    def test_no_release_from_preview_metadata(self):
        r = self.report
        self.assertEqual(r["owner_release"], "HOLD")
        self.assertEqual(r["devpost"], "NOT_SUBMITTED")
        self.assertEqual(r["nas_runtime"], "NOT_RUN")
        self.assertEqual(r["registered_uliya_expert"], "NOT_RUN")
        self.assertEqual(r["official_creator"], "OPERATOR_REPORTED_CODEX_ULIYA_0.7.3_EN")

    def test_report_sha_matches_both_real_artifacts(self):
        for ext in ("pdf","zip"):
            path=self.folder / (preview.FILEROOT + "." + ext)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             self.report[ext+"_sha256"])
        manifest=json.loads((self.folder/(preview.FILEROOT+"_manifest.json")).read_text())
        self.assertEqual(manifest,self.report)

if __name__ == "__main__":
    unittest.main()
