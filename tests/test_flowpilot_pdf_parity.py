"""Synthetic regression tests; never use private G103 assets."""
import sys
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_pdf_parity import check


class TestPDFParity(unittest.TestCase):
    def setUp(self):
        self.answers = [f"Answer number {i} has unique content {i}." for i in range(10)]
        self.source = {"questions": [{"question": f"Q{i}", "answer": answer}
                                     for i, answer in enumerate(self.answers)]}

    @staticmethod
    def pdf(answers):
        doc = fitz.open()
        page = doc.new_page()
        for i, answer in enumerate(answers):
            page.insert_text((40, 40 + i * 30), answer)
        result = doc.tobytes()
        doc.close()
        return result

    def test_all_ten_pass(self):
        self.assertEqual(check(self.pdf(self.answers), self.source)["matched_answers"], 10)

    def test_one_missing_refused(self):
        with self.assertRaisesRegex(ValueError, "PDF_ANSWER_MISMATCH"):
            check(self.pdf(self.answers[:-1]), self.source)

    def test_duplicate_answers_refused(self):
        self.source["questions"][1]["answer"] = self.answers[0]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ANSWERS"):
            check(self.pdf(self.answers), self.source)

    def test_invalid_pdf_refused(self):
        with self.assertRaises(ValueError):
            check(b"bad", self.source)

    def test_invalid_count_refused(self):
        self.source["questions"].pop()
        with self.assertRaisesRegex(ValueError, "INVALID_TEN_ANSWERS"):
            check(self.pdf(self.answers), self.source)


if __name__ == "__main__":
    unittest.main()
