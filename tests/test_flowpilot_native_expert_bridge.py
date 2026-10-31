"""G120 pinned catalog + typed NL + G87 normalized read evidence boundary."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from flowpilot_native_expert_bridge import route_native_review
from flowpilot_uliya_contract_preflight import TrialPreflightRefused
from flowpilot_multi_read_intake import IntakeRefused, SCHEMA as RECEIPTS_SCHEMA
from test_sdk_parameter_matrix import fake

ROOT_SCOPE = "/volume1/projects/synthetic-flowpilot"
GOAL = "필수 파일 확인해줘"
REQUIRED = ["README.md", "release/output.pdf"]
FIXTURE = json.loads(
    (ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")
    .read_text(encoding="utf-8")
)


def receipts(*rows):
    return {"schema": RECEIPTS_SCHEMA, "receipts": list(rows)}


class G120NativeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.archive, self.sha = fake()

    def route(self, **overrides):
        data = {
            "goal": GOAL, "authorized_root": ROOT_SCOPE,
            "required_paths": REQUIRED, "metadata_approved": True,
            "unknown_processing_accepted": True, "expected_sha": self.sha,
        }
        data.update(overrides)
        return route_native_review(self.archive, **data)

    def test_routes_only_fixed_supported_metadata_goal(self):
        result = self.route()
        self.assertEqual(result["status"], "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA")
        self.assertEqual(result["source"], "SYNTHETIC_CATALOG_TEST_ONLY")
        self.assertEqual(result["chosen_action_label"], "ug-filesystem find")
        self.assertEqual(result["owner_checklist_count"], 2)
        self.assertFalse(result["native_command_generated"])
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["registered_expert_invocation_verified"])

    def test_missing_consent_never_invokes_or_normalizes_receipts(self):
        x = self.route(metadata_approved=False, normalized_receipts=receipts(FIXTURE))
        self.assertEqual(x["status"], "WAITING_APPROVAL")
        self.assertEqual(x["receipt_status"], "RECEIPTS_NOT_EVALUATED_NO_APPROVAL")
        self.assertFalse(x["native_command_generated"])

    def test_unsupported_csv_cannot_be_labeled_native_capability(self):
        with patch("flowpilot_native_expert_bridge.preflight_trial",
                   side_effect=AssertionError("No SDK analysis for unsupported task")):
            x = self.route(goal="고객별 매출 보고서 만들어줘")
        self.assertEqual(x["status"], "BLOCKED_NO_VERIFIED_NATIVE_CSV_EXECUTION")
        self.assertFalse(x["native_command_generated"])

    def test_unsafe_compound_and_delete_request_blocked(self):
        for goal in ("필수 파일 확인해줘 그리고 삭제해줘", "매일 파일을 백업해줘",
                     "모든 파일 지워줘", "run docker", ""):
            with self.subTest(goal=goal):
                self.assertEqual(self.route(goal=goal)["status"],
                                 "BLOCKED_UNSUPPORTED_NATURAL_LANGUAGE_GOAL")

    def test_complete_synthetic_evidence_only_prepares_review(self):
        out = self.route(normalized_receipts=receipts(copy.deepcopy(FIXTURE)))
        self.assertEqual(out["receipt_status"], "REVIEW_PREPARED_UNVERIFIED")
        self.assertEqual(out["claimed_consistency"], "CONSISTENT_CLAIM_ONLY")
        self.assertEqual([r["state"] for r in out["item_results"]], ["PRESENT", "PRESENT"])
        self.assertFalse(out["operator_claims_independently_verified"])
        self.assertFalse(out["nas_verified"])
        self.assertNotIn(ROOT_SCOPE, json.dumps(out))
        self.assertNotIn("synthetic://README-1", json.dumps(out))

    def test_missing_file_is_only_provisional(self):
        row = copy.deepcopy(FIXTURE)
        row["file_agent_report"]["observations"].pop()
        out = self.route(normalized_receipts=receipts(row))
        self.assertEqual(out["claimed_workflow_status"], "BLOCKED")
        self.assertEqual([r["state"] for r in out["item_results"]], ["PRESENT", "MISSING"])
        self.assertFalse(out["nas_verified"])

    def test_partial_scan_cannot_infer_missing(self):
        row = copy.deepcopy(FIXTURE)
        row["file_agent_report"]["scan_complete"] = False
        row["file_agent_report"]["observations"].pop()
        out = self.route(normalized_receipts=receipts(row))
        self.assertEqual(out["claimed_consistency"], "INCOMPLETE")
        self.assertEqual([r["state"] for r in out["item_results"]],
                         ["NOT_CHECKED", "NOT_CHECKED"])

    def test_conflicting_stat_is_not_silent_success(self):
        one, two = copy.deepcopy(FIXTURE), copy.deepcopy(FIXTURE)
        two["file_agent_report"]["operation"] = "ug-filesystem stat"
        two["file_agent_report"]["observations"] = [two["file_agent_report"]["observations"][0]]
        two["file_agent_report"]["observations"][0]["reference"] = "synthetic://different"
        out = self.route(normalized_receipts=receipts(one, two))
        self.assertEqual(out["claimed_consistency"], "CONFLICT")
        self.assertEqual([r["state"] for r in out["item_results"]],
                         ["NOT_CHECKED", "NOT_CHECKED"])

    def test_mismatched_private_scope_and_action_refused(self):
        for modify in ("scope", "paths", "action", "consent"):
            row = copy.deepcopy(FIXTURE)
            if modify == "scope":
                row["authorized_root"] = "/volume1/private"
            elif modify == "paths":
                row["required_paths"].append("owner_secret.txt")
            elif modify == "action":
                row["file_agent_report"]["operation"] = "ug-filesystem cat"
            else:
                row["metadata_approved"] = False
            with self.subTest(modify=modify), self.assertRaises(IntakeRefused):
                self.route(normalized_receipts=receipts(row))

    def test_unpinned_real_catalog_rejected(self):
        with self.assertRaises(Exception):
            route_native_review(
                self.archive, goal=GOAL, authorized_root=ROOT_SCOPE,
                required_paths=REQUIRED, metadata_approved=True,
                unknown_processing_accepted=True,
            )

    def test_malformed_boolean_and_path_rejected(self):
        for data in ({"metadata_approved": "yes"},
                     {"required_paths": ["../secret"]},
                     {"authorized_root": "/volume1/../private"}):
            with self.subTest(data=data), self.assertRaises((TrialPreflightRefused, ValueError)):
                self.route(**data)

    def test_evidence_is_not_ingested_before_user_authorization(self):
        with patch("flowpilot_native_expert_bridge.evaluate_multi_read",
                   side_effect=AssertionError("Should not process receipts")):
            x = self.route(metadata_approved=False,
                           normalized_receipts=receipts(copy.deepcopy(FIXTURE)))
        self.assertEqual(x["receipt_status"], "RECEIPTS_NOT_EVALUATED_NO_APPROVAL")


if __name__ == "__main__":
    unittest.main()
