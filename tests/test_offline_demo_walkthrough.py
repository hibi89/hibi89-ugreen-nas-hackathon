"""Check the actual deterministic engine walkthrough, never an official NAS test."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "offline_demo_walkthrough", ROOT / "tools/offline_demo_walkthrough.py")
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class OfflineWalkthroughTests(unittest.TestCase):
    def setUp(self):
        self.doc = demo.build()
        self.cases = {x["id"]: x for x in self.doc["cases"]}

    def test_all_present_still_not_officially_ready(self):
        x = self.cases["all_present"]
        self.assertEqual(["PASS", "PASS"], [p["verdict"] for p in x["presence"]])
        self.assertEqual("NEEDS_REVIEW", x["overall"])
        self.assertFalse(x["is_real_nas_validation"])
        self.assertEqual("NOT_CHECKED", x["privacy_gate"])

    def test_missing_only_from_complete_hypothesis(self):
        x = self.cases["confirmed_missing"]
        self.assertEqual("BLOCKED", x["overall"])
        self.assertEqual("FAIL", x["presence"][1]["verdict"])

    def test_truncated_listing_does_not_falsely_block(self):
        x = self.cases["partial_listing"]
        self.assertEqual("NOT_CHECKED", x["presence"][1]["verdict"])
        self.assertEqual("NEEDS_REVIEW", x["overall"])

    def test_permission_denied_never_trusts_absence(self):
        x = self.cases["permission_denied"]
        self.assertEqual(["NOT_CHECKED", "NOT_CHECKED"],
                         [p["verdict"] for p in x["presence"]])
        self.assertEqual("NEEDS_REVIEW", x["overall"])

    def test_ambiguous_versions_never_autoapprove(self):
        x = self.cases["version_ambiguity"]
        self.assertEqual("CANDIDATES_REVIEW", x["versions"][0]["signal"])
        self.assertEqual("NEEDS_REVIEW", x["overall"])
        self.assertEqual("NOT_CHECKED", x["authoritative_version_gate"])

    def test_all_outputs_clear_simulation_labels_and_deterministic(self):
        self.assertEqual(5, len(self.doc["cases"]))
        self.assertEqual(self.doc, demo.build())
        self.assertEqual(demo.markdown(self.doc), demo.markdown(demo.build()))
        self.assertIn("SYNTHETIC ONLY", demo.markdown(self.doc))
        self.assertIn("NOT_OFFICIAL_VALIDATION", self.doc["status"])
        self.assertTrue(all(not x["is_real_nas_validation"] for x in self.doc["cases"]))
        self.assertTrue(all(x["privacy_gate"] == "NOT_CHECKED" for x in self.doc["cases"]))


if __name__ == "__main__":
    unittest.main()
