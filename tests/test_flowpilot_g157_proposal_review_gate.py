"""G157 PDF preflight regressions, synthetic only; no owner PDFs in public CI."""
import io
import json
from pathlib import Path
import sys
from contextlib import redirect_stdout
from unittest import TestCase, main

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g157_proposal_review_gate as g157


def example(*, prefix="", suffix="", answers=None):
    values = answers if answers is not None else [
        "An owner-approved read-only workflow avoids unsafe automatic mutation."
    ] * 10
    lines = [prefix]
    for i, answer in enumerate(values, 1):
        lines.extend([f"{i:02d} / Question {i}", answer])
    lines.extend(["DISCLOSURES & DEPENDENCIES",
                  "ChatGPT assisted drafting; UGREEN UGOS is a platform; entrant rights require review.",
                  suffix])
    return "\n".join(lines)


class G157ProposalTests(TestCase):
    def test_ten_answer_draft_structure_pass_hold(self):
        report = g157.audit_text(example())
        self.assertEqual(report["answer_count"], 10)
        self.assertFalse(report["owner_internal_labels_present"])
        self.assertFalse(report["entrant_rights_approved"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_original_owner_banner_identified_not_cleared(self):
        report = g157.audit_text(example(prefix="OWNER REVIEW - NOT SUBMITTED | G147 Review"))
        self.assertTrue(report["owner_internal_labels_present"])
        self.assertEqual(report["status"], "INTERNAL_REVIEW_LABELS_FOUND")

    def test_ten_numbered_period_style(self):
        report = g157.audit_text(example().replace(" / Question", ". Question"))
        self.assertEqual(report["answer_count"], 10)

    def test_missing_answer_refused(self):
        data = ["Valid completed answer with at least five words."] * 10
        data[4] = ""
        with self.assertRaisesRegex(g157.ProposalRefused, "ANSWER_EMPTY"):
            g157.audit_text(example(answers=data))

    def test_missing_number_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "TEN_NUMBERED"):
            g157.audit_text(example().replace("05 / Question 5", "Question 5"))

    def test_out_of_order_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "TEN_NUMBERED"):
            g157.audit_text(example().replace("05 / Question 5", "07 / Question 5"))

    def test_over_500_answer_words_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "500"):
            g157.audit_text(example(answers=["word " * 51] * 10))

    def test_missing_disclosure_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "DISCLOSURE"):
            g157.audit_text(example().replace("DISCLOSURES & DEPENDENCIES", "NO HEADER"))

    def test_missing_ai_usage_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "AI_PLATFORM"):
            g157.audit_text(example().replace("ChatGPT", "NoAI"))

    def test_pdf_wrong_pinned_digest_refused(self):
        with self.assertRaisesRegex(g157.ProposalRefused, "EXACT_PDF_SHA"):
            g157.audit_pdf(b"%PDF-synthetic", "g147-owner-review")

    def test_refusal_does_not_echo_local_owner_path(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = g157.main(["--pdf", "/owners/private-secret-file.pdf",
                            "--profile", "g147-owner-review"])
        self.assertEqual(rc, 2)
        self.assertNotIn("/owners/", out.getvalue())
        self.assertEqual(json.loads(out.getvalue())["release_gate"], "HOLD")


if __name__ == "__main__":
    main()
