"""G87 read-only, multi-observation reconciliation security and E2E fixtures."""
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
from flowpilot_multi_read_intake import (
    SCHEMA, IntakeRefused, evaluate_multi_read,
)

SOURCE = json.loads(
    (ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")
    .read_text(encoding="utf-8")
)


def receipt(*, operation="ug-filesystem find", full=True):
    row = copy.deepcopy(SOURCE)
    row["file_agent_report"]["operation"] = operation
    row["file_agent_report"]["scan_complete"] = full
    row["file_agent_report"]["pagination_complete"] = full
    return row


def bundle(*receipts):
    return {"schema": SCHEMA, "receipts": list(receipts)}


def states(report):
    return [item["state"] for item in report["item_results"]]


class G87MultiReadIntakeTests(unittest.TestCase):
    def test_full_find_and_matching_stat_form_bounded_offline_consensus(self):
        first = receipt()
        stat = receipt(operation="ug-filesystem stat", full=False)
        stat["file_agent_report"]["observations"] = [
            stat["file_agent_report"]["observations"][0]
        ]
        result = evaluate_multi_read(bundle(first, stat))
        self.assertEqual(states(result), ["PRESENT", "PRESENT"])
        self.assertEqual(result["consistency"], "CONSISTENT_CLAIM_ONLY")
        self.assertEqual(result["full_enumeration_claims"], 1)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["receipts_reviewed"], 2)
        self.assertFalse(result["operator_claims_independently_verified"])
        self.assertFalse(result["registered_expert_invocation_verified"])
        self.assertFalse(result["real_nas_verified"])
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertNotIn(first["authorized_root"], str(result))
        self.assertNotIn("synthetic://README-1", str(result))

    def test_claimed_complete_missing_is_provisional_block(self):
        first = receipt()
        first["file_agent_report"]["observations"].pop()
        result = evaluate_multi_read(bundle(first))
        self.assertEqual(states(result), ["PRESENT", "MISSING"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["real_nas_verified"])

    def test_partial_find_does_not_prove_missing(self):
        first = receipt(full=False)
        first["file_agent_report"]["observations"].pop()
        result = evaluate_multi_read(bundle(first))
        self.assertEqual(states(result), ["NOT_CHECKED", "NOT_CHECKED"])
        self.assertEqual(result["consistency"], "INCOMPLETE")

    def test_stat_alone_cannot_assert_complete_inventory(self):
        result = evaluate_multi_read(bundle(receipt(operation="ug-filesystem stat")))
        self.assertEqual(states(result), ["NOT_CHECKED", "NOT_CHECKED"])
        self.assertEqual(result["full_enumeration_claims"], 0)

    def test_matching_partial_stat_does_not_invalidate_complete_find(self):
        stat = receipt(operation="ug-filesystem stat", full=False)
        stat["file_agent_report"]["observations"] = []
        result = evaluate_multi_read(bundle(receipt(), stat))
        self.assertEqual(states(result), ["PRESENT", "PRESENT"])
        self.assertEqual(result["status"], "NEEDS_REVIEW")

    def test_unexpected_stat_item_does_not_turn_missing_into_present(self):
        first = receipt()
        first["file_agent_report"]["observations"].pop()
        stat = receipt(operation="ug-filesystem stat", full=False)
        stat["file_agent_report"]["observations"] = [
            stat["file_agent_report"]["observations"][1]
        ]
        result = evaluate_multi_read(bundle(first, stat))
        self.assertEqual(result["consistency"], "CONFLICT")
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(states(result), ["NOT_CHECKED", "NOT_CHECKED"])

    def test_conflicting_complete_enumerations_are_not_merged(self):
        second = receipt()
        second["file_agent_report"]["observations"].pop()
        result = evaluate_multi_read(bundle(receipt(), second))
        self.assertEqual(result["full_enumeration_claims"], 2)
        self.assertEqual(result["consistency"], "CONFLICT")
        self.assertEqual(states(result), ["NOT_CHECKED", "NOT_CHECKED"])

    def test_changed_reference_same_path_is_conflict(self):
        stat = receipt(operation="ug-filesystem stat", full=False)
        stat["file_agent_report"]["observations"][0]["reference"] = "synthetic://different"
        stat["file_agent_report"]["observations"].pop()
        result = evaluate_multi_read(bundle(receipt(), stat))
        self.assertEqual(result["consistency"], "CONFLICT")

    def test_symlink_or_containment_mismatch_is_not_upgraded(self):
        for field, value in (("is_symlink", True), ("contained", False),
                             ("contained", None)):
            with self.subTest(field=field, value=value):
                stat = receipt(operation="ug-filesystem stat", full=False)
                stat["file_agent_report"]["observations"].pop()
                stat["file_agent_report"]["observations"][0][field] = value
                result = evaluate_multi_read(bundle(receipt(), stat))
                self.assertEqual(result["consistency"], "CONFLICT")

    def test_denied_or_failed_supplementary_agent_downgrades_inventory(self):
        for field, value in (("permission_confirmed", False),
                             ("registered_adapter_confirmed", False),
                             ("failed", True)):
            with self.subTest(field=field):
                stat = receipt(operation="ug-filesystem stat", full=False)
                stat["file_agent_report"]["observations"] = []
                stat["file_agent_report"][field] = value
                result = evaluate_multi_read(bundle(receipt(), stat))
                self.assertEqual(states(result), ["NOT_CHECKED", "NOT_CHECKED"])

    def test_mixed_owners_and_checklists_are_refused(self):
        other = receipt()
        other["authorized_root"] = "/volume1/projects/other"
        other["file_agent_report"]["authorized_root"] = other["authorized_root"]
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read(bundle(receipt(), other))
        other = receipt()
        other["required_paths"] = ["README.md"]
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read(bundle(receipt(), other))

    def test_different_owner_consent_or_origin_is_refused(self):
        for field, value in (("metadata_approved", False),
                             ("unknown_processing_accepted", False),
                             ("origin", "OPERATOR_TRANSCRIBED_UNVERIFIED")):
            with self.subTest(field=field):
                other = receipt()
                other[field] = value
                with self.assertRaises(IntakeRefused):
                    evaluate_multi_read(bundle(receipt(), other))

    def test_duplicate_conflicting_path_in_one_receipt_is_rejected(self):
        first = receipt()
        second = copy.deepcopy(first["file_agent_report"]["observations"][0])
        second["reference"] = "synthetic://alternate"
        first["file_agent_report"]["observations"].append(second)
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read(bundle(first))

    def test_unapproved_operations_and_extra_fields_are_refused(self):
        for mutation in ("operation", "field"):
            first = receipt()
            if mutation == "operation":
                first["file_agent_report"]["operation"] = "ug-filesystem delete"
            else:
                first["api_key"] = "SENSITIVE"
            with self.subTest(mutation=mutation), self.assertRaises(IntakeRefused):
                evaluate_multi_read(bundle(first))

    def test_bounded_input_and_wrong_schema_are_refused(self):
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read(bundle())
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read(bundle(*[receipt() for _ in range(9)]))
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read({"schema": "wrong", "receipts": [receipt()]})
        with self.assertRaises(IntakeRefused):
            evaluate_multi_read({"schema": SCHEMA, "receipts": [receipt()],
                                 "approved_for_real_nas": True})

    def test_versions_still_require_manual_review(self):
        first = receipt()
        first["goal"] = "compare versions"
        first["version_candidates"] = {
            "release/output.pdf": ["release/output_v2.pdf"]
        }
        first["file_agent_report"]["observations"].append({
            "relative_path": "release/output_v2.pdf",
            "reference": "synthetic://output-v2",
            "contained": True, "is_symlink": False,
        })
        result = evaluate_multi_read(bundle(first))
        self.assertEqual(states(result), ["PRESENT", "VERSION_REVIEW"])
        self.assertEqual(result["status"], "NEEDS_REVIEW")

    def test_cli_removes_paths_and_raw_references(self):
        first = receipt()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "multi.json"
            path.write_text(json.dumps(bundle(first)), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(ROOT / "tools/flowpilot_multi_read_intake.py"),
                 "--input", str(path)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            payload = json.loads(process.stdout)
            self.assertFalse(payload["real_nas_verified"])
            self.assertNotIn(first["authorized_root"], process.stdout)
            self.assertNotIn("synthetic://README-1", process.stdout)
            self.assertNotIn("release/output.pdf", process.stdout)

    def test_cli_refuses_duplicate_keys_without_leaking_values(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                '{"schema":"%s","schema":"%s","receipts":[],"token":"LEAK"}'
                % (SCHEMA, SCHEMA), encoding="utf-8",
            )
            process = subprocess.run(
                [sys.executable, str(ROOT / "tools/flowpilot_multi_read_intake.py"),
                 "--input", str(path)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(process.returncode, 2)
            self.assertEqual(json.loads(process.stdout)["status"], "G87_MULTI_READ_REFUSED")
            self.assertNotIn("LEAK", process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
