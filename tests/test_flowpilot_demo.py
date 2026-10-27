"""G48: only synthetic fixture/report regressions, no real NAS."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_offline_demo import CASES, simulate, run_cases


class G48Demonstration(unittest.TestCase):
    def test_exact_five_fixture_scenarios(self):
        self.assertEqual(len(CASES), 5)
        self.assertEqual(len(run_cases()["cases"]), 5)

    def test_complete_case_does_not_claim_live_nas_ready(self):
        s = simulate("ok", CASES["complete_synthetic_handoff"])
        self.assertEqual([r["state"] for r in s["items"]], ["PRESENT", "PRESENT"])
        self.assertEqual(s["overall"], "NEEDS_REVIEW")
        self.assertEqual(s["live_nas"], "NOT_RUN")
        self.assertFalse(s["actual_nas_verified"])

    def test_missing_required_positively_blocked_synthetic_only(self):
        s = simulate("missing", CASES["missing_required_synthetic"])
        self.assertEqual([r["state"] for r in s["items"]], ["PRESENT", "MISSING"])
        self.assertEqual(s["overall"], "BLOCKED")

    def test_version_conflict_never_picks_latest(self):
        s = simulate("versions", CASES["conflicting_versions_synthetic"])
        self.assertEqual(s["items"][0]["state"], "VERSION_REVIEW")
        self.assertEqual(s["items"][0]["evidence"], [])

    def test_denied_scan_must_not_prove_missing(self):
        s = simulate("denied", CASES["truncated_or_denied_synthetic"])
        self.assertEqual(s["items"][0]["state"], "NOT_CHECKED")
        self.assertFalse(s["scope_complete_claimed_by_fixture"])

    def test_symlink_unverified_never_presents(self):
        s = simulate("link", CASES["symlink_unknown_synthetic"])
        self.assertEqual(s["items"][0]["state"], "NOT_CHECKED")

    def test_rejects_hidden_extra_inputs_in_fixture(self):
        bad = {**CASES["complete_synthetic_handoff"], "external_api": "https://example.com"}
        with self.assertRaises(ValueError): simulate("bad", bad)

    def test_secret_injected_as_evidence_is_rejected(self):
        fixture = {**CASES["complete_synthetic_handoff"], "observations": [
            {"relative_path": ".ssh/id_rsa", "reference": "bad", "contained": True}]}
        with self.assertRaises(ValueError): simulate("bad", fixture)


if __name__ == "__main__":
    unittest.main()
