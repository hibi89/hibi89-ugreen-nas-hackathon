"""G96: bounded offline G95 -> G87/G88 integration; no NAS."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from test_sdk_parameter_matrix import fake
from flowpilot_uliya_contract_preflight import SCHEMA as REQ_SCHEMA
from flowpilot_multi_read_intake import SCHEMA as MULTI_SCHEMA
from flowpilot_uliya_trial_rehearsal import SCHEMA, RehearsalRefused, rehearse

BASE = json.loads((ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")
                  .read_text(encoding="utf-8"))


def fixture():
    record = copy.deepcopy(BASE)
    return {
        "schema": SCHEMA,
        "request": {
            "schema": REQ_SCHEMA,
            "operation": record["file_agent_report"]["operation"],
            "goal": record["goal"],
            "authorized_root": record["authorized_root"],
            "required_paths": record["required_paths"],
            "metadata_approved": True,
            "unknown_processing_accepted": True,
        },
        "normalized_receipts": {"schema": MULTI_SCHEMA, "receipts": [record]},
    }


class G96RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.archive, self.sha = fake()

    def run_trial(self, request):
        return rehearse(self.archive, request, expected_sha=self.sha)

    def test_e2e_consistent_claim_only(self):
        value = self.run_trial(fixture())
        self.assertEqual(value["status"], "REVIEW_PREPARED_UNVERIFIED")
        self.assertEqual(value["consistency"], "CONSISTENT_CLAIM_ONLY")
        self.assertEqual(value["review_item_count"], 2)
        self.assertEqual(value["decision"], "HOLD")
        for key in ("operator_claims_independently_verified", "owner_approval_granted_by_tool",
                    "official_creator_verified", "registered_expert_invocation_verified",
                    "real_nas_verified", "execution_payload_generated"):
            self.assertFalse(value[key], key)

    def test_no_receipts_wait(self):
        p = fixture()
        p["normalized_receipts"]["receipts"] = []
        self.assertEqual(self.run_trial(p)["status"], "WAITING_NORMALIZED_RECEIPTS")

    def test_no_consent_does_not_process_bogus_receipt(self):
        p = fixture()
        p["request"]["metadata_approved"] = False
        p["normalized_receipts"]["receipts"] = [{"untrusted": "do_not_read"}]
        self.assertEqual(self.run_trial(p)["status"], "WAITING_APPROVAL")

    def test_unknown_processing_location_requires_approval(self):
        p = fixture()
        p["request"]["unknown_processing_accepted"] = False
        self.assertEqual(self.run_trial(p)["status"], "WAITING_APPROVAL")

    def test_write_intent_blocked(self):
        p = fixture()
        p["request"]["goal"] = "delete project files"
        self.assertEqual(self.run_trial(p)["status"], "BLOCKED")

    def test_root_mismatch_refused(self):
        p = fixture()
        p["normalized_receipts"]["receipts"][0]["authorized_root"] = "/volume1/different"
        with self.assertRaises(RehearsalRefused):
            self.run_trial(p)

    def test_operation_mismatch_refused(self):
        p = fixture()
        p["request"]["operation"] = "ug-filesystem stat"
        with self.assertRaises(RehearsalRefused):
            self.run_trial(p)

    def test_stat_only_cannot_prove_missing(self):
        p = fixture()
        p["request"]["operation"] = "ug-filesystem stat"
        p["normalized_receipts"]["receipts"][0]["file_agent_report"]["operation"] = "ug-filesystem stat"
        value = self.run_trial(p)
        self.assertEqual(value["consistency"], "INCOMPLETE")
        self.assertEqual(value["status"], "OFFLINE_INCOMPLETE_HOLD")
        self.assertTrue(all(x["claimed_state"] == "NOT_CHECKED" for x in value["review_queue"]))

    def test_missing_file_remains_hold(self):
        p = fixture()
        p["normalized_receipts"]["receipts"][0]["file_agent_report"]["observations"].pop()
        value = self.run_trial(p)
        self.assertEqual(value["finding_counts"]["MISSING"], 1)
        self.assertEqual(value["status"], "OFFLINE_BLOCKED_HOLD")
        self.assertEqual(value["decision"], "HOLD")

    def test_conflicting_scans_downgraded(self):
        p = fixture()
        other = copy.deepcopy(p["normalized_receipts"]["receipts"][0])
        other["file_agent_report"]["observations"].pop()
        p["normalized_receipts"]["receipts"].append(other)
        value = self.run_trial(p)
        self.assertEqual(value["consistency"], "CONFLICT")
        self.assertEqual(value["status"], "OFFLINE_CONFLICT_HOLD")
        self.assertTrue(all(x["claimed_state"] == "NOT_CHECKED" for x in value["review_queue"]))

    def test_unauthorized_version_scope_refused(self):
        p = fixture()
        p["normalized_receipts"]["receipts"][0]["version_candidates"] = {
            "release/output.pdf": ["release/output_v2.pdf"]}
        with self.assertRaises(RehearsalRefused):
            self.run_trial(p)

    def test_owner_path_and_references_not_leaked(self):
        p = fixture()
        output = json.dumps(self.run_trial(p))
        for private in (p["request"]["authorized_root"], "README.md",
                        "release/output.pdf", "synthetic://README-1"):
            self.assertNotIn(private, output)

    def test_nine_receipts_refused(self):
        p = fixture()
        p["normalized_receipts"]["receipts"] *= 9
        with self.assertRaises(RehearsalRefused):
            self.run_trial(p)

    def test_unknown_envelope_key_refused(self):
        p = fixture()
        p["token"] = "must-not-log"
        with self.assertRaises(RehearsalRefused):
            self.run_trial(p)

    def test_default_sha_pin_refuses_synthetic_archive(self):
        with self.assertRaises(Exception):
            rehearse(self.archive, fixture())


if __name__ == "__main__":
    unittest.main()
