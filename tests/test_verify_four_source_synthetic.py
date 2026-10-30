"""Test local four-source contract with a fake verifier, not private source."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_four_source_synthetic import (
    FourSourceProofRefused, run_matrix,
)
from tools.verify_private_hae_chain import EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA
from tools.verify_local_metadata_la_chain import EXPECTED_DBVORA_SHA


def fixture_response(*, approved=False):
    if not approved:
        return {
            "pinned_sources": "PASS",
            "hae_la_commit": EXPECTED_HAE_SHA,
            "sovia_commit": EXPECTED_SOVIA_SHA,
            "dbvora_commit": None,
            "dbvora_private_checkout_pinned": False,
            "dbvora_private_source_invoked_locally": False,
            "independent_public_ci_private_hae_executed": False,
            "local_inspection_performed": True,
            "sovia_advisory": "REVIEW_ONLY",
            "sovia_finding_count": 2,
            "status": "WAITING_EXACT_LOCAL_PLAN_APPROVAL",
            "approve_plan_sha256": "a" * 64,
            "la_execution_verified": False,
            "dbvora_metadata_inspected": False,
            "synthetic_write_rows": 0,
            "actual_nas_verified": False, "release_gate": "HOLD",
        }
    return {
        "pinned_sources": "PASS",
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "dbvora_commit": EXPECTED_DBVORA_SHA,
        "dbvora_private_checkout_pinned": True,
        "independent_public_ci_private_hae_executed": False,
        "local_inspection_performed": True,
        "sovia_advisory": "REVIEW_ONLY",
        "sovia_finding_count": 2,
        "file_contents_opened": False,
        "raw_paths_or_names_returned": False,
        "customer_file_contents_used": False,
        "status": "PASS",
        "la_execution_verified": True,
        "dbvora_metadata_inspected": True,
        "dbvora_private_source_invoked_locally": True,
        "synthetic_write_rows": 2,
        "approval_receipts": 1,
        "replay_duplicate_writes": 0,
        "ephemeral_sqlite_deleted_after_run": True,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
        "dbvora": {
            "status": "SYNTHETIC_SCHEMA_METADATA_ONLY",
            "contract": "ugreen-dbvora-p0-redacted.v1",
            "scope": "DISPOSABLE_LOCAL_LA_SQLITE_NOT_NAS",
            "source_implementation_independently_verified": False,
            "main_database_file_bytes": 8192,
            "table_count": 1, "column_count": 3,
            "real_nas_or_customer_database_inspected": False,
        }
    }


class FourSourceSyntheticMatrixTests(unittest.TestCase):
    def setUp(self):
        self.args = (Path("/HAE"), Path("/SOVIA"), Path("/DBVORA"))

    def test_default_never_loads_private_dbvora(self):
        calls = []
        def fake(*args, **kwargs):
            self.assertIsNone(kwargs.get("dbvora_root"))
            self.assertIsNone(kwargs.get("approved_sha256"))
            calls.append(args[3])
            self.assertEqual((args[3] / "README.md").read_text(),
                             "synthetic fixture only\n")
            return fixture_response()
        with patch("tools.verify_four_source_synthetic.verify", side_effect=fake):
            result = run_matrix(*self.args)
        self.assertEqual(result["status"],
                         "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL")
        self.assertEqual(result["synthetic_write_rows"], 0)
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0].exists())

    def test_approved_calls_pinned_private_dbvora_only_after_preview(self):
        calls = []
        def fake(*args, **kwargs):
            calls.append((args[3], dict(kwargs)))
            if len(calls) == 1:
                return fixture_response()
            self.assertEqual(kwargs["approved_sha256"], "a" * 64)
            self.assertEqual(kwargs["dbvora_root"], self.args[2])
            self.assertTrue(kwargs["metadata_consent"])
            return fixture_response(approved=True)
        with patch("tools.verify_four_source_synthetic.verify", side_effect=fake):
            result = run_matrix(*self.args, approve_disposable_synthetic=True)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["la_write_rows"], 2)
        self.assertFalse(calls[0][0].exists())
        self.assertFalse(result["actual_nas_verified"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_refuse_non_boolean_approval_without_source_access(self):
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=AssertionError("VERIFIER_CALLED")):
            with self.assertRaisesRegex(FourSourceProofRefused,
                                        "INVALID_SYNTHETIC_APPROVAL"):
                run_matrix(*self.args, approve_disposable_synthetic="true")

    def test_preview_claiming_execution_refused_without_second_call(self):
        unsafe = {**fixture_response(), "synthetic_write_rows": 1}
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=[unsafe, AssertionError("EXECUTED")]) as called:
            with self.assertRaisesRegex(FourSourceProofRefused,
                                        "UNSAFE_SYNTHETIC_PREVIEW"):
                run_matrix(*self.args, approve_disposable_synthetic=True)
            self.assertEqual(called.call_count, 1)

    def test_missing_dbvora_receipt_never_reports_pass(self):
        bad = {**fixture_response(approved=True),
               "dbvora_private_source_invoked_locally": False}
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=[fixture_response(), bad]):
            with self.assertRaisesRegex(FourSourceProofRefused,
                                        "FOUR_SOURCE_SYNTHETIC_EVIDENCE_INCOMPLETE"):
                run_matrix(*self.args, approve_disposable_synthetic=True)

    def test_invalid_sha_preview_is_rejected_before_any_write(self):
        for invalid in ("g" * 64, "A" * 64):
            with self.subTest(invalid=invalid[0]):
                bad = {**fixture_response(), "approve_plan_sha256": invalid}
                with patch("tools.verify_four_source_synthetic.verify",
                           side_effect=[bad, AssertionError("MUST_NOT_EXECUTE")]) as seen:
                    with self.assertRaisesRegex(
                            FourSourceProofRefused, "UNSAFE_SYNTHETIC_PREVIEW"):
                        run_matrix(*self.args, approve_disposable_synthetic=True)
                    self.assertEqual(seen.call_count, 1)

    def test_wrong_hae_sha_preview_is_rejected_without_write(self):
        bad = {**fixture_response(), "hae_la_commit": "0" * 40}
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=[bad, AssertionError("MUST_NOT_EXECUTE")]) as seen:
            with self.assertRaisesRegex(
                    FourSourceProofRefused, "UNSAFE_SYNTHETIC_PREVIEW"):
                run_matrix(*self.args, approve_disposable_synthetic=True)
            self.assertEqual(seen.call_count, 1)

    def test_wrong_dbvora_sha_approved_result_is_not_pass(self):
        bad = {**fixture_response(approved=True), "dbvora_commit": "0" * 40}
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=[fixture_response(), bad]):
            with self.assertRaisesRegex(
                    FourSourceProofRefused, "FOUR_SOURCE_SYNTHETIC_EVIDENCE_INCOMPLETE"):
                run_matrix(*self.args, approve_disposable_synthetic=True)

    def test_unverified_or_unredacted_dbvora_result_is_not_pass(self):
        base = fixture_response(approved=True)
        for field, value in (
            ("source_implementation_independently_verified", True),
            ("scope", "CUSTOMER_NAS"),
            ("column_count", True),
        ):
            with self.subTest(field=field):
                bad = {**base, "dbvora": {**base["dbvora"], field: value}}
                with patch("tools.verify_four_source_synthetic.verify",
                           side_effect=[fixture_response(), bad]):
                    with self.assertRaisesRegex(
                            FourSourceProofRefused, "FOUR_SOURCE_SYNTHETIC_EVIDENCE_INCOMPLETE"):
                        run_matrix(*self.args, approve_disposable_synthetic=True)

    def test_bad_nas_claim_refused(self):
        bad = {**fixture_response(approved=True), "actual_nas_verified": True}
        with patch("tools.verify_four_source_synthetic.verify",
                   side_effect=[fixture_response(), bad]):
            with self.assertRaisesRegex(FourSourceProofRefused,
                                        "FOUR_SOURCE_SYNTHETIC_EVIDENCE_INCOMPLETE"):
                run_matrix(*self.args, approve_disposable_synthetic=True)


if __name__ == "__main__":
    unittest.main()
