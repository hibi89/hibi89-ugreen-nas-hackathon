"""Regression checks for sanitized owner-submitted local synthetic proof.

The fixture came from an owner-provided Windows CLI stdout transcript,
not independently executed HAE in public CI.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from integrations.local_proof_receipt import ReceiptRejected, validate_owner_reported_local_proof

FIXTURE = Path(__file__).resolve().parents[1] / "integrations" / "evidence" / "owner_reported_local_e2e_20261030.json"


class LocalProofReceiptTests(unittest.TestCase):
    def setUp(self):
        self.proof = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def check(self, **updates):
        return validate_owner_reported_local_proof({**self.proof, **updates})

    def test_exact_owner_report_is_consistent_with_local_synthetic_scope(self):
        result = self.check()
        self.assertEqual(result["result"], "ACCEPTED_OWNER_REPORTED_SYNTHETIC_PROOF")
        self.assertFalse(result["independently_replayed_in_ugreen_ci"])
        self.assertEqual(result["reported_actual_la_sqlite"], "PASS")
        self.assertEqual(result["reported_actual_sovia_advisory"], "PASS")
        self.assertEqual(result["release_gate"], "HOLD")

    def test_public_release_never_unlocked_by_report(self):
        result = self.check()
        self.assertFalse(result["actual_nas_verified"])
        self.assertFalse(result["registered_uliya_expert_invoked"])
        self.assertFalse(result["official_creator_execution_verified"])
        self.assertFalse(result["devpost_submitted"])

    def test_mismatching_source_revision_rejected(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_HAE_LA_COMMIT"):
            self.check(hae_la_commit="0" * 40)
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_SOVIA_COMMIT"):
            self.check(sovia_commit="0" * 40)

    def test_untrusted_approval_receipt_count_rejected(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_SYNTHETIC_COUNT"):
            self.check(real_la_approval_receipts=0)

    def test_boolean_disguised_as_integer_rejected(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_SYNTHETIC_COUNT"):
            self.check(real_la_approved_write_rows=True)

    def test_duplicate_write_detected(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_SYNTHETIC_COUNT"):
            self.check(real_la_replay_duplicate_writes=1)

    def test_bad_sha256_and_extra_fields_rejected(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_SOURCE_DIGEST"):
            self.check(la_runtime_sha256="not_sha256")
        with self.assertRaisesRegex(ReceiptRejected, "UNEXPECTED_REPORT_FIELDS"):
            self.check(owner_private_path="C:/synthetic-secret")

    def test_claimed_external_nas_access_rejected(self):
        with self.assertRaisesRegex(ReceiptRejected, "UNVERIFIED_EXTERNAL_ACTION"):
            self.check(actual_nas_verified=True)
        with self.assertRaisesRegex(ReceiptRejected, "UNVERIFIED_EXTERNAL_ACTION"):
            self.check(devpost_submitted=True)

    def test_no_implicit_sovia_authorization(self):
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_RELEASE_GATE"):
            self.check(release_gate="READY")
        with self.assertRaisesRegex(ReceiptRejected, "INVALID_REAL_SOVIA_ADVISORY"):
            self.check(real_sovia_advisory="READY_FOR_EXECUTION")

    def test_fails_on_non_object_and_wrong_types(self):
        for unsupported in (None, [], "PASS"):
            with self.subTest(unsupported=unsupported):
                with self.assertRaises(ReceiptRejected):
                    validate_owner_reported_local_proof(unsupported)


if __name__ == "__main__":
    unittest.main()
