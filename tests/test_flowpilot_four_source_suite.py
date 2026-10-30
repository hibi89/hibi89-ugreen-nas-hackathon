"""Pure mock-source tests for offline 1-3 intent evidence bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.flowpilot_four_source_suite import run_suite, ProofBundleRefused


def fake(n, approved):
    if not approved:
        return {"status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                "scenario_count": n, "synthetic_write_rows": 0,
                "dbvora_private_source_invoked_locally": False,
                "nas_verified": False, "release_gate": "HOLD"}
    return {
        "status": "PASS", "scope": "DISPOSABLE_SYNTHETIC_LOCAL_ONLY",
        "intent_count": n, "la_write_rows": n, "la_replay_duplicates": 0,
        "approval_receipts": 1, "dbvora_table_count": 1, "dbvora_column_count": 3,
        "temporary_fixture_deleted": True,
        "actual_private_hae_la_invoked": True, "actual_public_sovia_invoked": True,
        "actual_private_dbvora_invoked": True, "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False, "release_gate": "HOLD",
    }


class FourSourceBundleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.roots = (Path("/HAE"), Path("/SOVIA"), Path("/DBVORA"))

    def test_previews_never_approve_disposable_writes(self):
        calls = []
        def stub(*args, **kw):
            calls.append(kw)
            return fake(kw["intent_count"], kw["approve_disposable_synthetic"])
        with patch("tools.flowpilot_four_source_suite.run_matrix", side_effect=stub):
            row = run_suite(*self.roots)
        self.assertEqual(row["status"], "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL")
        self.assertEqual([x["intent_count"] for x in calls], [1, 2, 3])
        self.assertTrue(all(not x["approve_disposable_synthetic"] for x in calls))

    def test_approved_bundle_has_three_json_html_and_verified_hashes(self):
        target = self.base / "synthetic-proof"
        def stub(*args, **kw):
            row = fake(kw["intent_count"], True)
            row["PRIVATE_PATH"] = "SECRET_PERSONAL_PATH"
            return row
        with patch("tools.flowpilot_four_source_suite.run_matrix", side_effect=stub):
            result = run_suite(*self.roots, approve_disposable_synthetic=True,
                               output_dir=target)
        self.assertEqual(result["status"], "PASS_SYNTHETIC_LOCAL_ONLY")
        manifest = json.loads((target / "manifest.json").read_text())
        self.assertEqual(len(manifest["file_sha256"]), 7)
        for name, expected in manifest["file_sha256"].items():
            self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), expected)
        for n in (1, 2, 3):
            receipt = json.loads((target / f"proof-{n}.json").read_text())
            self.assertEqual(receipt["la_write_rows"], n)
        self.assertNotIn("SECRET_PERSONAL_PATH",
                         "".join(f.read_text() for f in target.iterdir()))
        self.assertIn("RELEASE HOLD", (target / "index.html").read_text())

    def test_preview_bundle_uses_no_execution_labels(self):
        target = self.base / "preview"
        with patch("tools.flowpilot_four_source_suite.run_matrix",
                   side_effect=lambda *a, **kw: fake(kw["intent_count"], False)):
            run_suite(*self.roots, output_dir=target)
        self.assertIn("Write NOT EXECUTED", (target / "proof-3.html").read_text())
        self.assertEqual(json.loads((target / "manifest.json").read_text())["claim"],
                         "APPROVAL_PREVIEW_NO_WRITES")

    def test_existing_output_refused_before_private_source_access(self):
        target = self.base / "exists"
        target.mkdir()
        with patch("tools.flowpilot_four_source_suite.run_matrix",
                   side_effect=AssertionError("PRIVATE_SOURCE_READ")) as stub:
            with self.assertRaisesRegex(ProofBundleRefused, "OUTPUT_ALREADY_EXISTS"):
                run_suite(*self.roots, output_dir=target)
            self.assertEqual(stub.call_count, 0)

    def test_wrong_three_intent_receipt_refuses_bundle(self):
        target = self.base / "bad"
        def stub(*a, **kw):
            result = fake(kw["intent_count"], True)
            if kw["intent_count"] == 3:
                result["la_write_rows"] = 2
            return result
        with patch("tools.flowpilot_four_source_suite.run_matrix", side_effect=stub):
            with self.assertRaises(ProofBundleRefused):
                run_suite(*self.roots, approve_disposable_synthetic=True,
                          output_dir=target)
        self.assertFalse(target.exists())

    def test_forged_nas_claim_is_never_written(self):
        with patch("tools.flowpilot_four_source_suite.run_matrix",
                   side_effect=lambda *a, **kw: {**fake(kw["intent_count"], True),
                                                   "actual_nas_verified": True}):
            with self.assertRaisesRegex(ProofBundleRefused, "UNVERIFIED_SYNTHETIC_EVIDENCE"):
                run_suite(*self.roots, approve_disposable_synthetic=True)

    def test_relative_path_refused_before_approval(self):
        with patch("tools.flowpilot_four_source_suite.run_matrix",
                   side_effect=AssertionError("PRIVATE_SOURCE_READ")):
            with self.assertRaisesRegex(ProofBundleRefused, "OUTPUT_MUST_BE_ABSOLUTE"):
                run_suite(*self.roots, output_dir=Path("relative"))


if __name__ == "__main__":
    unittest.main()
