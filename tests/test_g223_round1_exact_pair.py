"""G223 synthetic regression; private PDF and Skill ZIP never committed."""
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import g223_round1_exact_pair as gate

def synthetic_skill():
    out = io.BytesIO()
    with ZipFile(out, "w") as z:
        z.writestr("flowpilot-3/SKILL.md", "---\nname: flowpilot-3\ndescription: synthetic\n---\nreferences/modes-and-evidence.md references/failure-and-disclosure.md")
        z.writestr("flowpilot-3/references/modes-and-evidence.md", "modes")
        z.writestr("flowpilot-3/references/failure-and-disclosure.md", "boundary")
    return out.getvalue()

class ExactPairGateTests(unittest.TestCase):
    def setUp(self):
        self.zip = synthetic_skill()
        with ZipFile(io.BytesIO(self.zip)) as z:
            self.root = z.read("flowpilot-3/SKILL.md")
        self.pdf = b"%PDF-1.4\nsynthetic only\n%%EOF\n"
        self.pins = {"expected_zip": gate.digest(self.zip), "expected_root": gate.digest(self.root),
                     "expected_pdf": gate.digest(self.pdf)}

    def test_accepts_only_matching_pinned_bytes_but_keeps_hold(self):
        result = gate.review(self.zip, self.pdf, **self.pins)
        self.assertEqual(result["status"], "EXACT_PAIR_BYTES_VERIFIED_OFFLINE_NOT_OFFICIAL")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["official_checker_executed"])
        self.assertFalse(result["official_creator_executed"])

    def test_pdf_mutation_refused(self):
        with self.assertRaisesRegex(gate.PairRejected, "PDF_BYTE_DRIFT"):
            gate.review(self.zip, self.pdf + b"extra", **self.pins)

    def test_zip_mutation_refused(self):
        with self.assertRaisesRegex(gate.PairRejected, "SKILL_ZIP_BYTE_DRIFT"):
            gate.review(self.zip + b"extra", self.pdf, **self.pins)

    def test_stale_previous_report_refused(self):
        stale = json.dumps({"new_pdf_sha256": gate.SUPERSEDED_G222_REPORT_SHA256,
                            "source_skill_zip_sha256": self.pins["expected_zip"]}).encode()
        with self.assertRaisesRegex(gate.PairRejected, "STALE_OR_DIFFERENT_PAIR_REPORT"):
            gate.review(self.zip, self.pdf, previous_report=stale, **self.pins)

    def test_matching_previous_report_observed_not_official(self):
        valid = json.dumps({"new_pdf_sha256": self.pins["expected_pdf"],
                            "source_skill_zip_sha256": self.pins["expected_zip"]}).encode()
        got = gate.review(self.zip, self.pdf, previous_report=valid, **self.pins)
        self.assertEqual(got["previous_report"], "PINNED_PAIR_MATCH")
        self.assertEqual(got["release_gate"], "HOLD")

    def test_symlink_and_zip_traversal_denied(self):
        out = io.BytesIO()
        with ZipFile(out, "w") as z:
            z.writestr("../SKILL.md", "bad")
        with self.assertRaisesRegex(gate.PairRejected, "SKILL_MEMBERS_INVALID"):
            gate.check_package(out.getvalue(), gate.digest(out.getvalue()), gate.digest(b"bad"))

    def test_invalid_pdf_marker_refused_even_pinned(self):
        bad = b"not actually pdf"
        with self.assertRaisesRegex(gate.PairRejected, "INVALID_PDF_BYTES"):
            gate.review(self.zip, bad, **{**self.pins, "expected_pdf": gate.digest(bad)})

    def test_zip_missing_reference_is_denied(self):
        out = io.BytesIO()
        with ZipFile(out, "w") as z:
            z.writestr("flowpilot-3/SKILL.md", "---\nname: flowpilot-3\ndescription: test\n---\nnone")
            z.writestr("flowpilot-3/references/modes-and-evidence.md", "a")
            z.writestr("flowpilot-3/references/failure-and-disclosure.md", "b")
        raw = out.getvalue()
        with ZipFile(io.BytesIO(raw)) as z:
            root = z.read("flowpilot-3/SKILL.md")
        with self.assertRaisesRegex(gate.PairRejected, "UNLINKED_REFERENCE"):
            gate.check_package(raw, gate.digest(raw), gate.digest(root))

    def test_missing_or_nonfile_input_refused(self):
        with self.assertRaises(gate.PairRejected):
            gate.safe_read(Path("/a/path/that/does/not/exist"), 100)

if __name__ == "__main__":
    unittest.main()
