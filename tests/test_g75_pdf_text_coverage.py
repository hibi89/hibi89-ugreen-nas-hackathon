"""G75 PDF extraction text coverage regression."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
QA = ROOT / "docs/submission/flowpilot_round1_qas_20261027.json"


class G75PDFTextTests(unittest.TestCase):
    def test_builder_has_explicit_rendered_content_guard(self):
        source=(ROOT/"tools/flowpilot_round1_preview.py").read_text(encoding="utf-8")
        self.assertIn("Rendered PDF lost official question or answer text",source)
        self.assertIn("Rendered PDF lost AI/third-party disclosure",source)
        self.assertIn("autojunk=False",source)

    def test_source_answers_and_disclosure_nonempty(self):
        import json
        data=json.loads(QA.read_text(encoding="utf-8"))
        self.assertEqual(len(data["questions"]),10)
        self.assertTrue(all(q["question"].strip() and q["answer"].strip() for q in data["questions"]))
        self.assertTrue(data["disclosure"].strip())


if __name__=="__main__":
    unittest.main()
