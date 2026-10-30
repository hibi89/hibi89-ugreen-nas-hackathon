"""Approval and safety semantics for owner-local UI; no real source invocation."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch
from tools.flowpilot_four_source_local_ui import CONSENT, HTML, Operator, OperatorRefused


class OperatorUITests(unittest.TestCase):
    def setUp(self):
        self.operator = Operator(Path("/hae"), Path("/sovia"), Path("/dbvora"))

    def test_preview_does_not_write_or_import_dbvora(self):
        calls = []
        def fake(*args, **kwargs):
            calls.append(kwargs["approve_disposable_synthetic"])
            return {"status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                    "scenario_count": 3, "actual_nas_verified": False,
                    "release_gate": "HOLD"}
        with (patch.object(self.operator, "sources",
                           return_value={"owner_local_synthetic_source_readiness": True}),
              patch("tools.flowpilot_four_source_local_ui.run_suite",
                    side_effect=fake)):
            row = self.operator.preview()
        self.assertEqual(calls, [False])
        self.assertFalse(row["synthetic_writes_executed"])
        self.assertEqual(row["intent_counts"], [1, 2, 3])

    def test_no_approval_before_preview(self):
        with self.assertRaisesRegex(OperatorRefused, "NO_PENDING_APPROVAL"):
            self.operator.execute("wrong", CONSENT)

    def test_only_exact_challenge_and_consent_can_execute_once(self):
        calls = []
        def fake(*args, **kw):
            calls.append(kw["approve_disposable_synthetic"])
            if kw["approve_disposable_synthetic"]:
                return {"status": "PASS_SYNTHETIC_LOCAL_ONLY", "scenario_count": 3,
                        "actual_nas_verified": False,
                        "registered_uliya_expert_invoked": False,
                        "evidence_bundle_created": False, "release_gate": "HOLD"}
            return {"status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                    "scenario_count": 3, "actual_nas_verified": False,
                    "release_gate": "HOLD"}
        with (patch.object(self.operator, "sources",
                           return_value={"owner_local_synthetic_source_readiness": True}),
              patch("tools.flowpilot_four_source_local_ui.run_suite", side_effect=fake)):
            challenge = self.operator.preview()["challenge"]
            with self.assertRaisesRegex(OperatorRefused, "EXACT_DISPOSABLE_APPROVAL_REQUIRED"):
                self.operator.execute(challenge, "NO")
            row = self.operator.execute(challenge, CONSENT)
            with self.assertRaisesRegex(OperatorRefused, "NO_PENDING_APPROVAL"):
                self.operator.execute(challenge, CONSENT)
        self.assertEqual(calls, [False, True])
        self.assertEqual(row["status"], "OPERATOR_REPORTED_SYNTHETIC_PASS")
        self.assertFalse(row["actual_nas_verified"])

    def test_no_preview_with_invalid_three_git_sources(self):
        with (patch.object(self.operator, "sources",
                           return_value={"owner_local_synthetic_source_readiness": False}),
              patch("tools.flowpilot_four_source_local_ui.run_suite",
                    side_effect=AssertionError("MUST_NOT_RUN")) as called):
            with self.assertRaisesRegex(OperatorRefused, "EXACT_GIT_CHECKOUTS_NOT_READY"):
                self.operator.preview()
            called.assert_not_called()

    def test_browser_has_separate_approval_checkbox_and_vendor_disclaimer(self):
        self.assertIn('type="checkbox"', HTML)
        self.assertIn("I_APPROVE_DISPOSABLE_SYNTHETIC_WRITES", HTML)
        self.assertIn("NAS/ULIYA NOT VERIFIED", HTML)
        self.assertNotIn("<script src=", HTML)


if __name__ == "__main__":
    unittest.main()
