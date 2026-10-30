"""Offline proof dashboard tests; no source checkouts or NAS access."""
from __future__ import annotations

import unittest
from tools.flowpilot_four_source_dashboard import EvidenceViewRefused, render_proof


def proof(n=2):
    return {
        "status": "PASS", "scope": "DISPOSABLE_SYNTHETIC_LOCAL_ONLY",
        "intent_count": n, "la_write_rows": n, "la_replay_duplicates": 0,
        "approval_receipts": 1, "dbvora_table_count": 1,
        "dbvora_column_count": 3, "temporary_fixture_deleted": True,
        "actual_private_hae_la_invoked": True,
        "actual_public_sovia_invoked": True,
        "actual_private_dbvora_invoked": True,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False, "release_gate": "HOLD",
    }


class OfflineFourSourceDashboardTests(unittest.TestCase):
    def test_disposable_four_source_claims_remain_labeled_unverified_nas(self):
        for n in (1, 2, 3):
            with self.subTest(n=n):
                html = render_proof(proof(n))
                self.assertIn(f"{n} synthetic writes", html)
                self.assertIn("NAS / Uliya", html)
                self.assertIn("RELEASE HOLD", html)
                self.assertIn("self-report", html)

    def test_preview_does_not_claim_execution(self):
        html = render_proof({
            "status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
            "scenario_count": 3, "synthetic_write_rows": 0,
            "dbvora_private_source_invoked_locally": False,
            "nas_verified": False, "release_gate": "HOLD",
        })
        self.assertIn("approval required", html)
        self.assertIn("Write NOT EXECUTED", html)

    def test_untrusted_json_string_is_not_rendered(self):
        row = proof()
        row["private_path"] = "</style><script>alert(1)</script>"
        row["secret_token"] = "UNAUTHORIZED_TOKEN"
        html = render_proof(row)
        self.assertNotIn("<script>", html)
        self.assertNotIn("UNAUTHORIZED_TOKEN", html)

    def test_forged_external_claims_rejected(self):
        for key, val in (
            ("actual_nas_verified", True),
            ("release_gate", "PASS"),
            ("la_write_rows", 0),
            ("dbvora_column_count", True),
            ("actual_private_dbvora_invoked", False),
        ):
            with self.subTest(key=key):
                row = {**proof(), key: val}
                with self.assertRaises(EvidenceViewRefused):
                    render_proof(row)

    def test_preview_false_dbvora_execution_rejected(self):
        with self.assertRaises(EvidenceViewRefused):
            render_proof({
                "status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                "scenario_count": 2, "synthetic_write_rows": 0,
                "dbvora_private_source_invoked_locally": True,
                "nas_verified": False, "release_gate": "HOLD",
            })

    def test_invalid_status_and_count_rejected(self):
        for row in ({"status": "SUCCESS"},
                    {"status": "PASS", "intent_count": 99},
                    {"status": "PASS", "intent_count": True}):
            with self.assertRaises(EvidenceViewRefused):
                render_proof(row)


if __name__ == "__main__":
    unittest.main()
