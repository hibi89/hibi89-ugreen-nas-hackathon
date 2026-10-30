"""G57 read-only generated FlowPilot source inspection synthetic contract."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from g57_flowpilot_creator_candidate_intake import inspect_candidate, CandidateError

BASE = b"---\nname: flowpilot-nas\ndescription: Baseline owner review\n---\n# Goal\nold\n"
GOOD = (
    "---\nname: flowpilot-nas\ndescription: New candidate\n---\n"
    "# Goal\nHANDOFF_AUDIT CHECK_REQUIRED REVIEW_VERSIONS SUMMARIZE_SELECTED\n"
    "file-agent document-agent NOT_CHECKED VERSION_REVIEW\n"
    "AI, third-party component disclosures and data flow required.\n"
)


class CreatorCandidateIntakeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.folder = self.root / "flowpilot-nas"
        self.folder.mkdir()
        self.skill = self.folder / "SKILL.md"
        self.skill.write_text(GOOD, encoding="utf-8")

    def check(self, baseline=BASE, receipt=None):
        return inspect_candidate(self.folder, baseline, receipt)

    def test_source_diff_is_review_hold(self):
        r = self.check()
        self.assertEqual(r["status"], "SOURCE_DIFF_HUMAN_REVIEW_REQUIRED")
        self.assertTrue(r["added_lines"] > 0)
        self.assertEqual(r["release_gate"], "HOLD")
        self.assertFalse(r["creator_execution_independently_verified"])

    def test_matching_source_is_still_review_hold(self):
        source = self.skill.read_bytes()
        r = self.check(source)
        self.assertEqual(r["status"], "SOURCE_MATCHED_HUMAN_PROVENANCE_REVIEW")
        self.assertEqual(r["added_lines"], 0)
        self.assertEqual(r["removed_lines"], 0)
        self.assertEqual(r["operator_receipt_status"], "CREATOR_NOT_EVIDENCED")

    def test_forged_operator_claim_cannot_clear_release(self):
        source = self.skill.read_bytes()
        sha = hashlib.sha256(source).hexdigest()
        declaration = {
            "kit_sha256": "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3",
            "generated_skill_sha256": sha, "checker_skill_sha256": sha,
            "generation_performed": True, "official_tool_loaded": True,
            "checker_status": "static-pass", "checker_errors": 0,
            "checker_warnings": 0, "checker_info": 0,
        }
        r = self.check(BASE, declaration)
        self.assertEqual(r["operator_receipt_status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertFalse(r["entrant_release_approved"])
        self.assertFalse(r["devpost_submitted"])

    def test_reference_markdown_directly_linked(self):
        ref = self.folder / "references"
        ref.mkdir()
        (ref / "policy.md").write_text("# Review only\n", encoding="utf-8")
        self.skill.write_text(GOOD + "\n[policy](references/policy.md)\n", encoding="utf-8")
        r = self.check()
        self.assertEqual(r["reference_count"], 1)
        self.assertEqual(r["markdown_file_count"], 2)

    def test_unlinked_reference_rejected(self):
        d = self.folder / "references"
        d.mkdir()
        (d / "orphan.md").write_text("orphan")
        with self.assertRaises(CandidateError):
            self.check()

    def test_missing_reference_target_rejected(self):
        self.skill.write_text(GOOD + "\n[policy](references/missing.md)\n")
        with self.assertRaises(CandidateError):
            self.check()

    def test_unexpected_script_rejected(self):
        (self.folder / "run.py").write_text("print('bad')")
        with self.assertRaises(CandidateError):
            self.check()

    def test_extra_nested_folder_rejected(self):
        (self.folder / "references").mkdir()
        (self.folder / "references" / "sub").mkdir()
        with self.assertRaises(CandidateError):
            self.check()

    def test_secret_rejected_without_source_in_report(self):
        self.skill.write_text(GOOD + "AKIA" + "A" * 16)
        with self.assertRaises(CandidateError):
            self.check()

    def test_missing_or_bad_identity_rejected(self):
        self.skill.write_text(GOOD.replace("name: flowpilot-nas", "name: changed"))
        with self.assertRaises(CandidateError):
            self.check()

    def test_official_creator_alternate_identity_is_review_only(self):
        alternate = self.root / "flowpilot-3"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text(
            GOOD.replace("name: flowpilot-nas", "name: flowpilot-3"),
            encoding="utf-8",
        )
        result = inspect_candidate(alternate, BASE)
        self.assertEqual(result["candidate"], "flowpilot-3")
        self.assertEqual(result["canonical_candidate"], "flowpilot-nas")
        self.assertFalse(result["canonical_identity_matches"])
        self.assertFalse(result["candidate_adoption_approved"])
        self.assertEqual(result["status"], "SOURCE_DIFF_IDENTITY_REVIEW_REQUIRED")
        self.assertEqual(result["operator_receipt_status"], "CREATOR_NOT_EVIDENCED")
        self.assertEqual(result["operator_receipt_gate_scope"], "flowpilot-nas-only")
        self.assertEqual(result["release_gate"], "HOLD")

    def test_alt_identity_directory_mismatch_rejected(self):
        alternate = self.root / "flowpilot-3"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text(GOOD, encoding="utf-8")
        with self.assertRaises(CandidateError):
            inspect_candidate(alternate, BASE)

    def test_unapproved_candidate_directory_rejected(self):
        unexpected = self.root / "flowpilot-other"
        unexpected.mkdir()
        (unexpected / "SKILL.md").write_text(
            GOOD.replace("name: flowpilot-nas", "name: flowpilot-other"),
            encoding="utf-8",
        )
        with self.assertRaises(CandidateError):
            inspect_candidate(unexpected, BASE)

    def test_canonical_identity_remains_canonical(self):
        result = self.check()
        self.assertEqual(result["candidate"], "flowpilot-nas")
        self.assertTrue(result["canonical_identity_matches"])
        self.assertFalse(result["candidate_adoption_approved"])
        self.assertEqual(result["status"], "SOURCE_DIFF_HUMAN_REVIEW_REQUIRED")

    def test_symlink_to_external_file_rejected(self):
        outside = self.root / "outside"
        outside.write_text("private", encoding="utf-8")
        try:
            (self.folder / "hidden.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(CandidateError):
            self.check()

    def test_missing_feature_signals_need_review_not_false_ready(self):
        self.skill.write_text(
            "---\nname: flowpilot-nas\ndescription: Minimal\n---\n# Goal\nread only\n",
            encoding="utf-8")
        r = self.check()
        self.assertIn("file-agent", r["missing_design_signals_for_owner_review"])
        self.assertEqual(r["release_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
