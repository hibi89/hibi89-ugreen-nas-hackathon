"""G88: independent, redacted review of bounded G87 multi-read claims."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_multi_read_intake import SCHEMA
from flowpilot_multi_read_review import build_review, IntakeRefused

BASE = json.loads(
    (ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")
    .read_text(encoding="utf-8")
)


def receipt(*, complete=True):
    value = copy.deepcopy(BASE)
    value["file_agent_report"]["operation"] = "ug-filesystem find"
    value["file_agent_report"]["scan_complete"] = complete
    value["file_agent_report"]["pagination_complete"] = complete
    return value


def bundle(*rows):
    return {"schema": SCHEMA, "receipts": list(rows)}


class G88MultiReadReviewTests(unittest.TestCase):
    def test_consistent_all_present_remains_hold_for_unverified_source(self):
        row = receipt()
        review = build_review(bundle(row))
        self.assertEqual(review["source_status"], "NEEDS_REVIEW")
        self.assertEqual(review["decision"], "HOLD")
        self.assertEqual(review["review_item_count"], len(row["required_paths"]))
        self.assertTrue(review["review_required"])
        self.assertEqual(
            review["blocking_reasons"], ["SOURCE_NOT_INDEPENDENTLY_VERIFIED"])
        self.assertFalse(review["registered_expert_invocation_verified"])
        self.assertFalse(review["owner_approval_granted_by_this_tool"])

    def test_missing_and_version_review_are_indexed_without_names(self):
        missing = receipt()
        missing["file_agent_report"]["observations"].pop()
        review = build_review(bundle(missing))
        self.assertTrue(any(
            x["reason_code"] == "CLAIMED_MISSING_NEEDS_OWNER_REVIEW"
            for x in review["review_queue"]))
        self.assertEqual(review["decision"], "HOLD")
        candidate = receipt()
        candidate["goal"] = "compare versions"
        candidate["version_candidates"] = {
            "release/output.pdf": ["release/output_v2.pdf"]}
        candidate["file_agent_report"]["observations"].append({
            "relative_path": "release/output_v2.pdf",
            "reference": "synthetic://version-2",
            "contained": True, "is_symlink": False,
        })
        review = build_review(bundle(candidate))
        self.assertTrue(any(
            x["reason_code"] == "VERSION_CONFLICT_REVIEW"
            for x in review["review_queue"]))
        self.assertNotIn("release/output", str(review))
        self.assertNotIn("synthetic://", str(review))

    def test_conflicting_evidence_fail_closed_for_all_items(self):
        a, b = receipt(), receipt()
        b["file_agent_report"]["observations"].pop()
        review = build_review(bundle(a, b))
        self.assertEqual(review["consistency"], "CONFLICT")
        self.assertIn("CONTRADICTORY_EVIDENCE", review["blocking_reasons"])
        self.assertTrue(all(
            row["claimed_state"] == "NOT_CHECKED"
            and row["reason_code"] == "CONTRADICTORY_EVIDENCE"
            for row in review["review_queue"]))
        self.assertFalse(review["real_nas_verified"])

    def test_partial_or_stat_only_never_promoted_to_present(self):
        partial = build_review(bundle(receipt(complete=False)))
        self.assertEqual(partial["consistency"], "INCOMPLETE")
        self.assertTrue(all(
            row["reason_code"] == "INCOMPLETE_OR_UNCONFIRMED_READ"
            for row in partial["review_queue"]))
        stat = receipt()
        stat["file_agent_report"]["operation"] = "ug-filesystem stat"
        review = build_review(bundle(stat))
        self.assertEqual(review["consistency"], "INCOMPLETE")
        self.assertEqual(review["decision"], "HOLD")

    def test_waiting_approval_and_write_intent_remain_blocked(self):
        row = receipt()
        row["metadata_approved"] = False
        review = build_review(bundle(row))
        self.assertEqual(review["source_status"], "WAITING_APPROVAL")
        self.assertIn("OWNER_APPROVAL_REQUIRED", review["blocking_reasons"])
        self.assertEqual(review["review_queue"], [])
        row = receipt()
        row["goal"] = "delete project files"
        review = build_review(bundle(row))
        self.assertEqual(review["source_status"], "BLOCKED")
        self.assertIn("PLAN_BLOCKED_OR_CLAIMED_MISSING", review["blocking_reasons"])
        self.assertEqual(review["decision"], "HOLD")

    def test_reject_untrusted_raw_api_and_scope_changes(self):
        row = receipt()
        row["file_agent_report"]["operation"] = "ug-filesystem delete"
        with self.assertRaises(IntakeRefused):
            build_review(bundle(row))
        a, b = receipt(), receipt()
        b["authorized_root"] = "/volume1/elsewhere"
        b["file_agent_report"]["authorized_root"] = "/volume1/elsewhere"
        with self.assertRaises(IntakeRefused):
            build_review(bundle(a, b))

    def test_cli_good_input_contains_no_names_references_or_paths(self):
        row = receipt()
        with TemporaryDirectory() as temp:
            p = Path(temp) / "receipt.json"
            p.write_text(json.dumps(bundle(row)), encoding="utf-8")
            got = subprocess.run(
                [sys.executable, str(ROOT / "tools/flowpilot_multi_read_review.py"),
                 "--input", str(p)], capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(got.returncode, 0, got.stderr)
        result = json.loads(got.stdout)
        self.assertTrue(result["review_required"])
        self.assertNotIn(row["authorized_root"], got.stdout)
        self.assertNotIn("synthetic://", got.stdout)
        for path in row["required_paths"]:
            self.assertNotIn(path, got.stdout)

    def test_cli_duplicate_key_and_symlink_refused_without_leaks(self):
        with TemporaryDirectory() as temp:
            p = Path(temp) / "bad.json"
            p.write_text(
                '{"schema":"%s","schema":"%s","receipts":[],"token":"NEVER_SHOW"}'
                % (SCHEMA, SCHEMA), encoding="utf-8",
            )
            cmd = [sys.executable, str(ROOT / "tools/flowpilot_multi_read_review.py"),
                   "--input", str(p)]
            got = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(got.returncode, 2)
            self.assertEqual(json.loads(got.stdout)["status"], "G88_REVIEW_REFUSED")
            self.assertNotIn("NEVER_SHOW", got.stdout + got.stderr)
            other = Path(temp) / "link.json"
            try:
                other.symlink_to(p)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation not permitted")
            got = subprocess.run(cmd[:-1] + [str(other)], capture_output=True,
                                 text=True, timeout=15)
            self.assertEqual(got.returncode, 2)


if __name__ == "__main__":
    unittest.main()
