"""G61 normalized operator agent metadata intake; no actual vendor SDK runtime."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_agent_result_intake import evaluate_normalized_receipt, IntakeRefused

SOURCE = json.loads(
    (ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")
    .read_text(encoding="utf-8")
)


def changed(edit):
    row = copy.deepcopy(SOURCE)
    edit(row)
    return row


class G61NormalizedAgentReceipt(unittest.TestCase):
    def test_complete_claimed_receipt_is_never_live_verified(self):
        r = evaluate_normalized_receipt(SOURCE)
        self.assertEqual([x["state"] for x in r["item_results"]], ["PRESENT", "PRESENT"])
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertFalse(r["official_registered_agent_invocation_verified"])
        self.assertFalse(r["real_nas_verified"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_missing_on_claimed_complete_records_is_provisional_block(self):
        p = changed(lambda x: x["file_agent_report"]["observations"].pop())
        r = evaluate_normalized_receipt(p)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["item_results"][1]["state"], "MISSING")
        self.assertFalse(r["operator_claims_independently_verified"])

    def test_partial_listing_prevents_false_missing(self):
        p = changed(lambda x: (x["file_agent_report"].update(scan_complete=False),
                              x["file_agent_report"]["observations"].pop()))
        r = evaluate_normalized_receipt(p)
        self.assertEqual([x["state"] for x in r["item_results"]],
                         ["NOT_CHECKED", "NOT_CHECKED"])

    def test_unregistered_agent_claim_does_not_unlock_results(self):
        p = changed(lambda x: x["file_agent_report"].update(registered_adapter_confirmed=False))
        r = evaluate_normalized_receipt(p)
        self.assertEqual(r["item_results"][0]["state"], "NOT_CHECKED")

    def test_wrong_agent_and_operation_rejected(self):
        for patch in (
            {"agent": "shell-agent"},
            {"operation": "ug-filesystem delete"},
        ):
            with self.subTest(patch=patch):
                p = changed(lambda x: x["file_agent_report"].update(patch))
                with self.assertRaises(IntakeRefused):
                    evaluate_normalized_receipt(p)

    def test_unmatched_agent_scope_rejected(self):
        p = changed(lambda x: x["file_agent_report"].update(authorized_root="/volume1/other"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)

    def test_out_of_scope_path_cannot_be_passed(self):
        p = changed(lambda x: x["file_agent_report"]["observations"][0].update(relative_path="private/data.csv"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)

    def test_restricted_or_traversal_paths_never_accepted(self):
        for entry in ("../escape.md", ".env", "token.pem", "/etc/passwd"):
            with self.subTest(path=entry):
                p = changed(lambda x: x["required_paths"].__setitem__(0, entry))
                with self.assertRaises(IntakeRefused):
                    evaluate_normalized_receipt(p)

    def test_string_boolean_does_not_claim_permission(self):
        p = changed(lambda x: x["file_agent_report"].update(permission_confirmed="true"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)

    def test_string_approval_does_not_unlock_planning(self):
        p = changed(lambda x: x.update(metadata_approved="true"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)

    def test_disallowed_mutation_request_is_blocked(self):
        p = changed(lambda x: x.update(goal="check and deleting old files"))
        r = evaluate_normalized_receipt(p)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["item_results"], [])

    def test_no_owner_metadata_approval_does_not_evaluate_telemetry(self):
        p = changed(lambda x: x.update(metadata_approved=False))
        r = evaluate_normalized_receipt(p)
        self.assertEqual(r["status"], "WAITING_APPROVAL")
        self.assertEqual(r["item_results"], [])

    def test_versions_are_validated_and_competing_files_require_review(self):
        p = changed(lambda x: (
            x.update(goal="compare versions",
                     version_candidates={"release/output.pdf": ["release/output_v2.pdf"]}),
            x["file_agent_report"]["observations"].append(
                {"relative_path": "release/output_v2.pdf", "reference": "synthetic://alt-2",
                 "contained": True, "is_symlink": False})))
        r = evaluate_normalized_receipt(p)
        self.assertEqual(r["item_results"][1]["state"], "VERSION_REVIEW")

    def test_duplicate_reference_across_files_rejected(self):
        p = changed(lambda x: x["file_agent_report"]["observations"][1].update(reference="synthetic://README-1"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)

    def test_unknown_fields_or_raw_vendor_schema_rejected(self):
        p = changed(lambda x: x.update(authentication_token="SECRET"))
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt(p)
        with self.assertRaises(IntakeRefused):
            evaluate_normalized_receipt({"result": {"files": []}})

    def test_cli_accepts_json_without_echoing_paths_or_refs(self):
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_agent_result_intake.py"),
               "--input", str(ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json")]
        r = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        data = json.loads(r.stdout)
        self.assertEqual(data["observed_record_count"], 2)
        self.assertNotIn("synthetic://README-1", r.stdout)
        self.assertNotIn("/volume1/projects/synthetic-flowpilot", r.stdout)

    def test_cli_rejects_broken_receipt_without_echo(self):
        with tempfile.TemporaryDirectory() as d:
            x = Path(d) / "bad.json"
            x.write_text('{"secret": "SHOULD_NOT_SHOW"', encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "tools/flowpilot_agent_result_intake.py"),
                                "--input", str(x)], capture_output=True, text=True, timeout=15)
            self.assertEqual(r.returncode, 2)
            self.assertNotIn("SHOULD_NOT_SHOW", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
