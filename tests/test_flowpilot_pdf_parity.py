"""Only synthetic fixtures. No private G103 PDF, NAS, or vendor SDK."""
from __future__ import annotations

import contextlib
from io import StringIO
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_pdf_parity import check, main

try:
    import fitz
except ImportError:
    fitz = None


@unittest.skipUnless(fitz is not None, "PyMuPDF optional; PDF integration not tested")
class PDFParityTests(unittest.TestCase):
    def setUp(self):
        self.answers = [f"Answer number {i} has unique content {i}." for i in range(10)]
        self.source = {"questions": [{"question": f"Q{i}", "answer": a}
                                     for i, a in enumerate(self.answers)]}

    @staticmethod
    def pdf(answers):
        doc = fitz.open()
        page = doc.new_page()
        for i, answer in enumerate(answers):
            page.insert_text((40, 40 + 30 * i), answer)
        raw = doc.tobytes()
        doc.close()
        return raw

    def test_all_ten_pass(self):
        result = check(self.pdf(self.answers), self.source)
        self.assertEqual(result["matched_answers"], 10)
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["official_checker_executed"])

    def test_one_missing_refused(self):
        with self.assertRaisesRegex(ValueError, "PDF_ANSWER_MISMATCH_OR_ORDER"):
            check(self.pdf(self.answers[:-1]), self.source)

    def test_duplicate_answers_refused(self):
        self.source["questions"][1]["answer"] = self.answers[0]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ANSWERS"):
            check(self.pdf(self.answers), self.source)

    def test_invalid_pdf_refused(self):
        with self.assertRaisesRegex(ValueError, "INVALID_PDF"):
            check(b"bad", self.source)

    def test_invalid_count_refused(self):
        self.source["questions"].pop()
        with self.assertRaisesRegex(ValueError, "INVALID_TEN_ANSWERS"):
            check(self.pdf(self.answers), self.source)

    def test_out_of_order_answers_refused(self):
        reordered = [self.answers[1], self.answers[0], *self.answers[2:]]
        with self.assertRaisesRegex(ValueError, "PDF_ANSWER_MISMATCH_OR_ORDER"):
            check(self.pdf(reordered), self.source)

    def test_answer_substring_inside_larger_word_refused(self):
        self.source["questions"][0]["answer"] = "Answer"
        self.answers[0] = "Answers"
        with self.assertRaisesRegex(ValueError, "PDF_ANSWER_MISMATCH_OR_ORDER"):
            check(self.pdf(self.answers), self.source)

    def test_whitespace_wrapping_preserves_parity(self):
        self.source["questions"][0]["answer"] = "Answer  number 0 has\n unique content 0."
        self.assertEqual(check(self.pdf(self.answers), self.source)["matched_answers"], 10)

    def test_cli_success_and_bounded_source(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "review.pdf"
            source = Path(temp) / "source.json"
            pdf.write_bytes(self.pdf(self.answers))
            source.write_text(json.dumps(self.source), encoding="utf-8")
            stdout = StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["--pdf", str(pdf), "--source", str(source)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["matched_answers"], 10)
            source.write_text("x" * (128 * 1024 + 1), encoding="utf-8")
            stdout = StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["--pdf", str(pdf), "--source", str(source)]), 2)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "PDF_PARITY_REFUSED")


class ParityWithoutPyMuPDF(unittest.TestCase):
    def test_dependency_missing_refuses_without_traceback(self):
        with patch.dict(sys.modules, {"fitz": None}):
            with self.assertRaisesRegex(RuntimeError, "PYMUPDF_REQUIRED"):
                check(b"%PDF-1.4", {"questions": []})

    def test_nonexistent_files_refused_no_private_path_echo(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--pdf", "/owner/private/secret.pdf", "--source", "/owner/private/source.json"])
        self.assertEqual(code, 2)
        data = json.loads(output.getvalue())
        self.assertEqual(data["release_gate"], "HOLD")
        self.assertNotIn("owner/private", output.getvalue())


if __name__ == "__main__":
    unittest.main()
