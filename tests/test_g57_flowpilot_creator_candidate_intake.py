"""G57 read-only generated FlowPilot source inspection synthetic contract."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
        self.assertEqual(result["operator_receipt_gate_scope"], "g188")
        self.assertEqual(result["release_gate"], "HOLD")

    def test_g198_g188_uppercase_references_and_reported_receipt_hold(self):
        alternate = self.root / "flowpilot-3"
        (alternate / "references").mkdir(parents=True)
        source = GOOD.replace("name: flowpilot-nas", "name: flowpilot-3")
        source += "\n[contract](references/CAPABILITY_AND_PLAN_CONTRACT.md)\n"
        (alternate / "SKILL.md").write_text(source, encoding="utf-8")
        (alternate / "references" / "CAPABILITY_AND_PLAN_CONTRACT.md").write_text(
            "# Reference only\n", encoding="utf-8")
        raw = (alternate / "SKILL.md").read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        receipt = {"kit_sha256": "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3",
                   "generated_skill_sha256": sha, "checker_skill_sha256": sha,
                   "generation_performed": True, "official_tool_loaded": True,
                   "checker_status": "static-pass", "checker_errors": 0,
                   "checker_warnings": 0, "checker_info": 0}
        r = inspect_candidate(alternate, BASE, receipt)
        self.assertEqual(r["reference_count"], 1)
        self.assertEqual(r["operator_receipt_gate_scope"], "g188")
        self.assertEqual(r["operator_receipt_status"], "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["release_gate"], "HOLD")
        self.assertFalse(r["creator_execution_independently_verified"])


    def test_g201_g188_uses_profile_modes_and_processing_location_cues(self):
        alternate = self.root / "flowpilot-3"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text(
            "---\nname: flowpilot-3\ndescription: Bounded review\n---\n"
            "# Goal\nDELIVERY_CHECK VERSION_REVIEW DOCUMENT_REVIEW DESIGN_ONLY\n"
            "file-agent document-agent NOT_CHECKED\n"
            "third-party AI processing location unknown\n",
            encoding="utf-8",
        )
        report = inspect_candidate(alternate, BASE)
        self.assertEqual(report["missing_design_signals_for_owner_review"], [])
        self.assertEqual(report["missing_disclosure_signals_for_owner_review"], [])
        self.assertEqual(report["status"], "SOURCE_DIFF_IDENTITY_REVIEW_REQUIRED")
        self.assertEqual(report["operator_receipt_status"], "CREATOR_NOT_EVIDENCED")
        self.assertEqual(report["release_gate"], "HOLD")

    def test_g201_g188_still_flags_missing_mode_and_location(self):
        alternate = self.root / "flowpilot-3"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text(
            "---\nname: flowpilot-3\ndescription: Thin candidate\n---\n"
            "# Goal\nDELIVERY_CHECK third-party AI\n",
            encoding="utf-8",
        )
        report = inspect_candidate(alternate, BASE)
        self.assertIn("VERSION_REVIEW", report["missing_design_signals_for_owner_review"])
        self.assertIn("data flow", report["missing_disclosure_signals_for_owner_review"])
        self.assertEqual(report["release_gate"], "HOLD")

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

    def test_g211_g57_g53_agree_on_reordered_frontmatter(self):
        from g53_flowpilot_creator_gate import EXPECTED_KIT_SHA
        source = (b"---\ndescription: Bounded reviewer\n"
                  b"name: flowpilot-nas\n---\n# Goal\n"
                  b"HANDOFF_AUDIT CHECK_REQUIRED REVIEW_VERSIONS SUMMARIZE_SELECTED\n"
                  b"file-agent document-agent NOT_CHECKED VERSION_REVIEW\n"
                  b"third-party AI data flow described\n")
        self.skill.write_bytes(source)
        receipt = {"kit_sha256": EXPECTED_KIT_SHA,
                   "generated_skill_sha256": hashlib.sha256(source).hexdigest(),
                   "generation_performed": True, "official_tool_loaded": True}
        r = self.check(BASE, receipt)
        self.assertEqual(r["operator_receipt_status"],
                         "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertEqual(r["candidate"], "flowpilot-nas")
        self.assertFalse(r["creator_execution_independently_verified"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_g210_creator_only_report_distinguishes_optional_checker(self):
        from g53_flowpilot_creator_gate import EXPECTED_KIT_SHA
        skill = self.skill.read_bytes()
        receipt = {
            "kit_sha256": EXPECTED_KIT_SHA,
            "generated_skill_sha256": hashlib.sha256(skill).hexdigest(),
            "generation_performed": True, "official_tool_loaded": True,
        }
        report = self.check(BASE, receipt)
        self.assertEqual(report["operator_checker_report_status"],
                         "NOT_REPORTED_OPTIONAL_ROUND1")
        self.assertEqual(report["operator_receipt_status"],
                         "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED")
        self.assertFalse(report["creator_execution_independently_verified"])
        self.assertFalse(report["entrant_release_approved"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_g209_symlinked_grandparent_is_refused(self):
        actual = self.root / "actual"
        nested = actual / "nested" / "flowpilot-nas"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text(GOOD, encoding="utf-8")
        alias = self.root / "alias"
        try:
            alias.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlinks unavailable")
        # The immediate parent (alias/nested) isn't itself a symlink;
        # G207's old parent-only check would accept this redirected tree.
        with self.assertRaises(CandidateError):
            inspect_candidate(alias / "nested" / "flowpilot-nas", BASE)

    def test_g209_windows_reparse_attribute_refused(self):
        original_lstat = Path.lstat
        target = self.folder
        def with_reparse_flag(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if Path(path) == target:
                return SimpleNamespace(
                    st_mode=result.st_mode,
                    st_file_attributes=getattr(result, "st_file_attributes", 0) | 0x400,
                )
            return result
        with patch.object(Path, "lstat", autospec=True, side_effect=with_reparse_flag):
            with self.assertRaises(CandidateError):
                self.check()

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
