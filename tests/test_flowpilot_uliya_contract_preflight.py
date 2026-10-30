"""G95: fail-closed offline first-party catalog trial planning, never NAS."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from test_sdk_parameter_matrix import fake
from inspect_official_sdk import UnsafePackage
from flowpilot_uliya_contract_preflight import (
    SCHEMA, TrialPreflightRefused, pinned_catalog_contract, preflight_trial,
)

REQ = {
    "schema": SCHEMA, "operation": "ug-filesystem find",
    "goal": "check required files",
    "authorized_root": "/volume1/projects/PRIVATE_CUSTOMER",
    "required_paths": ["README.md", "release/PRIVATE_OUTPUT.pdf"],
    "metadata_approved": True,
    "unknown_processing_accepted": True,
}


class G95PinnedCatalogTests(unittest.TestCase):
    def setUp(self):
        self.blob, self.sha = fake()

    def test_only_pinned_read_identifiers_are_listed(self):
        report = pinned_catalog_contract(self.blob, expected_sha=self.sha)
        self.assertEqual([row["operation"] for row in report["operations"]],
                         ["ug-filesystem ls", "ug-filesystem find", "ug-filesystem stat"])
        self.assertFalse(report["native_result_schema_verified"])
        self.assertFalse(report["registered_expert_verified"])
        self.assertEqual(report["release_gate"], "HOLD")
        self.assertNotIn("SENSITIVE_NOT_FOR_LOG", json.dumps(report))

    def test_no_pinned_hash_override_in_default_runtime(self):
        with self.assertRaises(UnsafePackage):
            pinned_catalog_contract(self.blob)

    def test_authorized_scope_still_cannot_dispatch_unverified_expert(self):
        report = preflight_trial(self.blob, REQ, expected_sha=self.sha)
        self.assertEqual(report["status"], "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA")
        self.assertEqual(report["owner_checklist_count"], 2)
        self.assertFalse(report["execution_payload_generated"])
        self.assertFalse(report["external_call_performed"])
        self.assertFalse(report["effective_nas_permissions_verified"])
        self.assertEqual(report["release_gate"], "HOLD")
        output = json.dumps(report)
        for fragment in ("PRIVATE_CUSTOMER", "PRIVATE_OUTPUT.pdf", "/volume1/projects"):
            self.assertNotIn(fragment, output)

    def test_consent_is_not_inferred_from_truthy_values(self):
        for value in (1, "true", [], {}, None):
            row = dict(REQ, metadata_approved=value)
            with self.subTest(value=value), self.assertRaises(TrialPreflightRefused):
                preflight_trial(self.blob, row, expected_sha=self.sha)

    def test_no_consent_never_generates_execution_payload(self):
        row = dict(REQ, metadata_approved=False)
        report = preflight_trial(self.blob, row, expected_sha=self.sha)
        self.assertEqual(report["status"], "WAITING_APPROVAL")
        self.assertFalse(report["execution_payload_generated"])

    def test_unknown_processing_location_requires_explicit_acceptance(self):
        row = dict(REQ, unknown_processing_accepted=False)
        report = preflight_trial(self.blob, row, expected_sha=self.sha)
        self.assertEqual(report["status"], "WAITING_APPROVAL")

    def test_mutating_goal_blocked_even_with_consent(self):
        for goal in ("delete project files", "옮겨줘 README.md"):
            with self.subTest(goal=goal):
                report = preflight_trial(self.blob, dict(REQ, goal=goal), expected_sha=self.sha)
                self.assertEqual(report["status"], "BLOCKED")
                self.assertFalse(report["external_call_performed"])

    def test_unsupported_action_and_untrusted_fields_refused(self):
        for change in ({"operation": "ug-filesystem cat"},
                       {"operation": "ug-filesystem rm"}, {"token": "DO_NOT_SHOW"}):
            req = dict(REQ)
            req.update(change)
            with self.subTest(change=change), self.assertRaises(TrialPreflightRefused):
                preflight_trial(self.blob, req, expected_sha=self.sha)

    def test_noncanonical_scope_and_duplicate_checklist_refused(self):
        for change in ({"authorized_root": "/volume1/../private"},
                       {"required_paths": ["../secret.txt"]},
                       {"required_paths": ["README.md", "README.md"]},
                       {"required_paths": ["secret.env"]}):
            req = dict(REQ)
            req.update(change)
            with self.subTest(change=change), self.assertRaises(TrialPreflightRefused):
                preflight_trial(self.blob, req, expected_sha=self.sha)

    def test_reject_missing_official_action(self):
        def change(c):
            group = next(g for g in c["clis"] if g["name"] == "ug-filesystem")
            group["actions"] = [a for a in group["actions"] if a["name"] != "stat"]
        blob, digest = fake(change)
        with self.assertRaises(UnsafePackage):
            pinned_catalog_contract(blob, expected_sha=digest)

    def test_reject_duplicate_official_parameter_names(self):
        def change(c):
            group = next(g for g in c["clis"] if g["name"] == "ug-filesystem")
            # SELECTION stores names as a set: action[0] changes with hash seed.
            # Exercise the supported read action explicitly, never arbitrary cat/hash.
            ls_action = next(a for a in group["actions"] if a["name"] == "ls")
            ls_action["parameters"].append(
                copy.deepcopy(ls_action["parameters"][0]))
        blob, digest = fake(change)
        with self.assertRaises(TrialPreflightRefused):
            pinned_catalog_contract(blob, expected_sha=digest)

    def test_unrecognized_goal_cannot_become_ready(self):
        report = preflight_trial(self.blob, dict(REQ, goal="launch fireworks"),
                                 expected_sha=self.sha)
        self.assertEqual(report["status"], "WAITING_USER")
        self.assertFalse(report["execution_payload_generated"])

    def test_invalid_schema_is_refused_before_catalog(self):
        row = dict(REQ, schema="untrusted")
        with self.assertRaises(TrialPreflightRefused):
            preflight_trial(self.blob, row, expected_sha=self.sha)


if __name__ == "__main__":
    unittest.main()
