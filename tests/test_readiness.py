"""Synthetic offline tests. No official SDK/CLI/NAS interactions."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from projectready.readiness import Overall, Requirement, ScanStatus, Verdict, evaluate

R = (Requirement("design", "final/design.pdf"), Requirement("quote", "final/quote.pdf"))
FULL = {"version": Verdict.PASS, "access": Verdict.PASS, "privacy": Verdict.PASS}

class ReadinessTests(unittest.TestCase):
    def test_complete_verified_ready(self):
        self.assertEqual(Overall.READY, evaluate(R, ["final/design.pdf", "final/quote.pdf"], ScanStatus.COMPLETE, FULL).overall)
    def test_missing_gate_never_ready(self):
        a = evaluate(R, ["final/design.pdf", "final/quote.pdf"], ScanStatus.COMPLETE)
        self.assertEqual(Overall.NEEDS_REVIEW, a.overall)
        self.assertIn("gate:privacy", [c.id for c in a.checks])
    def test_missing_file_in_complete_scan_blocks(self):
        a = evaluate(R, ["final/design.pdf"], ScanStatus.COMPLETE, FULL)
        self.assertEqual(Overall.BLOCKED, a.overall)
        self.assertEqual(Verdict.FAIL, a.checks[1].verdict)
    def test_partial_scan_never_proves_absence(self):
        a = evaluate(R, ["final/design.pdf"], ScanStatus.PARTIAL, FULL)
        self.assertEqual(Overall.NEEDS_REVIEW, a.overall)
        self.assertEqual(Verdict.NOT_CHECKED, a.checks[1].verdict)
    def test_denied_with_names_never_proves_presence(self):
        a = evaluate(R, ["final/design.pdf"], ScanStatus.DENIED, FULL)
        self.assertEqual(Verdict.NOT_CHECKED, a.checks[0].verdict)
        self.assertEqual(Overall.NEEDS_REVIEW, a.overall)
    def test_not_run_is_not_checked(self):
        self.assertEqual(Overall.NEEDS_REVIEW, evaluate(R, [], ScanStatus.NOT_RUN, FULL).overall)
    def test_version_ambiguity_requires_review(self):
        a = evaluate(R, ["final/design.pdf", "final/quote.pdf"], ScanStatus.COMPLETE, dict(FULL, version=Verdict.REVIEW))
        self.assertEqual(Overall.NEEDS_REVIEW, a.overall)
    def test_security_failure_blocks(self):
        a = evaluate(R, ["final/design.pdf", "final/quote.pdf"], ScanStatus.COMPLETE, dict(FULL, privacy=Verdict.FAIL))
        self.assertEqual(Overall.BLOCKED, a.overall)
    def test_case_sensitive_does_not_guess(self):
        a = evaluate(R, ["final/Design.pdf", "final/quote.pdf"], ScanStatus.COMPLETE, FULL)
        self.assertEqual(Overall.BLOCKED, a.overall)
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([Requirement("a", "a"), Requirement("a", "b")], [], ScanStatus.COMPLETE, FULL)
    def test_traversal_rejected(self):
        for path in ("../secret", "/private/a", "a/../b", "a//b", "a\\b", "a/./b", "a\x00b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                evaluate([Requirement("a", path)], [], ScanStatus.COMPLETE, FULL)
    def test_observed_traversal_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(R, ["../secret"], ScanStatus.PARTIAL, FULL)
    def test_empty_requirements_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], [], ScanStatus.COMPLETE, FULL)
    def test_unknown_gate_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(R, [], ScanStatus.COMPLETE, {**FULL, "unsafe_bypass": Verdict.PASS})
    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(R, [], "UNKNOWN", FULL)
    def test_nonmandatory_missing_not_auto_block(self):
        req = (Requirement("only", "final/a.pdf"), Requirement("bonus", "optional/a.pdf", False))
        self.assertEqual(Overall.READY, evaluate(req, ["final/a.pdf"], ScanStatus.COMPLETE, FULL).overall)

if __name__ == "__main__":
    unittest.main()
