"""End-to-end static owner-review UI checks from synthetic redacted receipts."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_owner_review_dashboard import (
    DashboardRefused, render_owner_review, verify_public_report,
)

HERE = Path(__file__).resolve().parents[1] / "tools"


def fixture(states=("PRESENT", "PRESENT", "VERSION_REVIEW", "NOT_CHECKED")):
    summary = {k: states.count(k) for k in ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")}
    report = {
        "schema": "flowpilot-synthetic-owner-review-v1",
        "source": "UNTRUSTED_OPERATOR_NORMALIZED_LOCAL_ONLY",
        "status": "SYNTHETIC_NEEDS_REVIEW",
        "goal_type": "SUMMARIZE_SELECTED",
        "file_stage": {
            "status": "NEEDS_REVIEW", "item_count": len(states), "counts": summary,
            "items": [
                {"requirement_index": i, "unverified_state": state}
                for i, state in enumerate(states, 1)
            ],
            "official_registered_file_agent_invoked": False,
        },
        "document_stage": {
            "status": "SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW",
            "selected_count": 1, "claimed_answer_count": 1,
            "actual_document_agent_invoked": False,
            "reported_complete_claim": True,
        },
        "trace": [
            {"stage": "file_agent", "state": "UNTRUSTED_OFFLINE_CLAIM"},
            {"stage": "separate_document_consent", "state": "ASSERTED_ONLY_NOT_RUNTIME_VERIFIED"},
            {"stage": "document_agent", "state": "SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW"},
            {"stage": "owner_review", "state": "SYNTHETIC_NEEDS_REVIEW"},
        ],
        "contains_raw_paths_references_questions_or_answers": False,
        "file_agent_live_verified": False,
        "document_agent_live_verified": False,
        "real_nas_verified": False,
        "overall_ready_certified": False,
        "sovia_integrated": False,
        "dbvora_integrated": False,
        "release_gate": "HOLD",
        "devpost_submitted": False,
        "checksum_kind": "UNSIGNED_LOCAL_INTEGRITY_ONLY_NOT_PROVENANCE",
    }
    resign(report)
    return report


def resign(report):
    no_hash = {k: v for k, v in report.items() if k != "public_report_sha256"}
    report["public_report_sha256"] = hashlib.sha256(
        json.dumps(no_hash, ensure_ascii=False, sort_keys=True, allow_nan=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class ReviewDashboardTests(unittest.TestCase):
    def test_safe_report_rendered_with_full_stage_flow(self):
        row = fixture()
        page = render_owner_review(row)
        for needle in ("NAS FLOWPILOT 3.0", "Owner Review &amp; Audit Trail", "File inventory",
                       "Separate consent", "Document review", "Owner decision",
                       "SYNTHETIC_NEEDS_REVIEW", row["public_report_sha256"], "LOCAL ONLY"):
            self.assertIn(needle, page)
        self.assertEqual(page.count("<tr>"), 5)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("https://", page.lower())

    def test_report_modification_without_new_hash_rejected(self):
        row = fixture()
        row["file_stage"]["items"][0]["unverified_state"] = "MISSING"
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_forged_production_ready_claim_rejected_even_if_resigned(self):
        row = fixture()
        row["real_nas_verified"] = True
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)
        row = fixture()
        row["status"] = "READY"
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_self_contradictory_counts_rejected_even_if_resigned(self):
        row = fixture()
        row["file_stage"]["counts"]["PRESENT"] = 9
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_inconsistent_file_index_and_trace_rejected(self):
        row = fixture()
        row["file_stage"]["items"][1]["requirement_index"] = 1
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)
        row = fixture()
        row["trace"][2]["state"] = "NOT_RUN"
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_unrequested_document_results_rejected(self):
        row = fixture()
        row["document_stage"]["status"] = "NOT_REQUESTED"
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_boolean_count_or_claims_rejected(self):
        row = fixture()
        row["file_stage"]["counts"]["PRESENT"] = True
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)
        row = fixture()
        row["document_stage"]["selected_count"] = "1"
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_no_external_assets_or_inline_user_content(self):
        row = fixture()
        row["raw_secret"] = "SECRET_PERSONAL_DATA"
        resign(row)
        self.assertNotIn("SECRET_PERSONAL_DATA", render_owner_review(row))

    def test_invalid_schema_or_invalid_digest_rejected(self):
        row = fixture()
        row["schema"] = "other"
        resign(row)
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)
        row = fixture()
        row["public_report_sha256"] = "x" * 64
        with self.assertRaises(DashboardRefused):
            render_owner_review(row)

    def test_blocked_case_displays_missing(self):
        row = fixture(("PRESENT", "MISSING"))
        row["status"] = "SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW"
        row["trace"][-1]["state"] = row["status"]
        resign(row)
        page = render_owner_review(row)
        self.assertIn("SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW", page)
        self.assertIn("MISSING", page)

    def test_cli_writes_new_html_only_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            inp, out = d / "input.json", d / "dashboard.html"
            inp.write_text(json.dumps(fixture()), encoding="utf-8")
            cmd = [sys.executable, str(HERE / "flowpilot_owner_review_dashboard.py"),
                   "--input", str(inp), "--output", str(out)]
            a = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertIn("Owner Review", out.read_text(encoding="utf-8"))
            b = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(b.returncode, 2)
            self.assertEqual(json.loads(b.stdout)["status"], "OWNER_REVIEW_DASHBOARD_REFUSED")

    def test_cli_refuses_malformed_json_without_leaking(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            inp, out = d / "bad.json", d / "dashboard.html"
            inp.write_text('{"userSecret":"NON_PUBLIC_TEXT"', encoding="utf-8")
            cmd = [sys.executable, str(HERE / "flowpilot_owner_review_dashboard.py"),
                   "--input", str(inp), "--output", str(out)]
            a = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(a.returncode, 2)
            self.assertNotIn("NON_PUBLIC_TEXT", a.stdout + a.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
