"""Offline consent-bound FlowPilot report: scope, integrity and redaction."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_agent_result_intake import IntakeRefused
from flowpilot_selected_document_stage import preview_selected_document
from flowpilot_document_result_intake import fingerprint
from flowpilot_owner_review_report import assemble_review, verify_report_checksum

FIXTURE = ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json"
REF = "synthetic://output-1"
GOAL = "summarize selected document"
QUESTION = "Summarize risks?"


def first_stage(intent=GOAL):
    row = json.loads(FIXTURE.read_text(encoding="utf-8"))
    row["goal"] = intent
    return row


def stage3(first=None, *, question=QUESTION, refs=None):
    first = first if first is not None else first_stage()
    refs = refs if refs is not None else [REF]
    plan = preview_selected_document(first, selected_refs=refs,
                                     question=question, consented_refs=refs,
                                     content_approved=True)["synthetic_instruction_draft"]
    return {
        "schema": "flowpilot-normalized-document-result-v1",
        "origin": "SYNTHETIC_TEST",
        "agent": "document-agent",
        "operation": "ug-document qa",
        "authorized_root": plan["authorized_root"],
        "request_sha256": fingerprint(plan),
        "question_sha256": plan["question_sha256"],
        "permission_confirmed": True,
        "registered_adapter_confirmed": True,
        "scan_complete": True,
        "failed": False,
        "results": [{"reference": ref, "state": "ANSWERED", "answer": "synthetic internal answer"}
                    for ref in refs],
    }


def report(first=None, doc=None, *, refs=None, consent=True, question=QUESTION, consent_refs=None):
    first = first if first is not None else first_stage()
    refs = refs if refs is not None else [REF]
    return assemble_review(
        first,
        document_receipt=doc,
        selected_refs=refs,
        question=question,
        consented_refs=consent_refs if consent_refs is not None else refs,
        content_approved=consent,
    )


class ReviewReportTests(unittest.TestCase):
    def test_valid_synthetic_document_is_not_real_nas_ready(self):
        first = first_stage()
        outcome = report(first, stage3(first))
        self.assertEqual(outcome["status"], "SYNTHETIC_NEEDS_REVIEW")
        self.assertEqual(outcome["file_stage"]["counts"]["PRESENT"], 2)
        self.assertEqual(outcome["document_stage"]["claimed_answer_count"], 1)
        self.assertEqual(outcome["document_stage"]["status"],
                         "SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW")
        self.assertFalse(outcome["real_nas_verified"])
        self.assertFalse(outcome["overall_ready_certified"])
        self.assertFalse(outcome["document_agent_live_verified"])
        self.assertEqual(outcome["release_gate"], "HOLD")

    def test_public_report_redacts_all_sensitive_fields(self):
        first = first_stage()
        outcome = report(first, stage3(first))
        text = json.dumps(outcome, ensure_ascii=False)
        for private in (first["authorized_root"], "release/output.pdf",
                        "README.md", QUESTION, REF, "synthetic internal answer"):
            self.assertNotIn(private, text)
        self.assertFalse(outcome["contains_raw_paths_references_questions_or_answers"])

    def test_digest_detects_accidental_modification(self):
        outcome = report(doc=stage3())
        self.assertTrue(verify_report_checksum(outcome))
        altered = copy.deepcopy(outcome)
        altered["file_stage"]["counts"]["PRESENT"] = 999
        self.assertFalse(verify_report_checksum(altered))
        altered = copy.deepcopy(outcome)
        altered["public_report_sha256"] = "0" * 64
        self.assertFalse(verify_report_checksum(altered))

    def test_missing_separate_consent_cannot_process_preprovided_result(self):
        result = report(doc=stage3(), consent=False)
        self.assertEqual(result["document_stage"]["status"],
                         "WAITING_SEPARATE_DOCUMENT_APPROVAL")
        self.assertEqual(result["document_stage"]["claimed_answer_count"], 0)

    def test_missing_document_receipt_does_not_fake_answer(self):
        result = report(doc=None)
        self.assertEqual(result["document_stage"]["status"],
                         "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED")
        self.assertEqual(result["document_stage"]["claimed_answer_count"], 0)

    def test_missing_selected_references_asks_owner(self):
        outcome = assemble_review(first_stage())
        self.assertEqual(outcome["document_stage"]["status"], "WAITING_USER")
        self.assertEqual(outcome["document_stage"]["selected_count"], 0)

    def test_wrong_document_digest_is_refused(self):
        receipt = stage3()
        receipt["request_sha256"] = "0" * 64
        with self.assertRaises(IntakeRefused):
            report(doc=receipt)

    def test_changed_question_invalidates_previous_result(self):
        with self.assertRaises(IntakeRefused):
            report(doc=stage3(), question="A different question?")

    def test_unknown_document_reference_refused(self):
        claim = stage3()
        claim["results"][0]["reference"] = "synthetic://outside"
        with self.assertRaises(IntakeRefused):
            report(doc=claim)

    def test_partial_and_failed_document_claim_needs_review(self):
        claim = stage3()
        claim["scan_complete"] = False
        result = report(doc=claim)
        self.assertEqual(result["document_stage"]["status"],
                         "SYNTHETIC_INCOMPLETE_OR_FAILED_NEEDS_REVIEW")
        claim = stage3()
        claim["results"] = []
        claim["failed"] = True
        result = report(doc=claim)
        self.assertEqual(result["document_stage"]["claimed_answer_count"], 0)

    def test_partial_file_listing_cannot_certify_missing(self):
        first = first_stage()
        first["file_agent_report"]["scan_complete"] = False
        first["file_agent_report"]["observations"] = []
        result = report(first)
        self.assertEqual(result["file_stage"]["counts"]["MISSING"], 0)
        self.assertEqual(result["file_stage"]["counts"]["NOT_CHECKED"], 2)
        self.assertEqual(result["document_stage"]["status"],
                         "BLOCKED_UNVERIFIED_INVENTORY")

    def test_claimed_complete_missing_file_needs_owner_review(self):
        first = first_stage("check required files")
        first["file_agent_report"]["observations"].pop()
        result = assemble_review(first)
        self.assertEqual(result["status"], "SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW")
        self.assertEqual(result["file_stage"]["counts"]["MISSING"], 1)

    def test_non_document_intent_rejects_extra_stage(self):
        first = first_stage("check required files")
        with self.assertRaises(IntakeRefused):
            assemble_review(first, document_receipt=stage3())
        result = assemble_review(first)
        self.assertEqual(result["document_stage"]["status"], "NOT_REQUESTED")
        self.assertTrue(verify_report_checksum(result))

    def test_transcribed_receipt_never_unlocks_documents(self):
        first = first_stage()
        first["origin"] = "OPERATOR_TRANSCRIBED_UNVERIFIED"
        result = report(first, stage3())
        self.assertEqual(result["document_stage"]["status"],
                         "BLOCKED_RUNTIME_PROVENANCE_UNVERIFIED")

    def test_refuse_unknown_file_agent_fields(self):
        first = first_stage()
        first["file_agent_report"]["secret"] = "PRIVATE"
        with self.assertRaises(IntakeRefused):
            assemble_review(first)

    def test_refuse_unsafe_first_stage_checklist(self):
        first = first_stage()
        first["required_paths"][0] = "../private.md"
        with self.assertRaises(IntakeRefused):
            assemble_review(first)

    def test_cli_one_command_writes_only_redacted_new_json(self):
        first = first_stage()
        claim = stage3(first)
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            a, b, output = d / "a.json", d / "b.json", d / "report.json"
            a.write_text(json.dumps(first), encoding="utf-8")
            b.write_text(json.dumps(claim), encoding="utf-8")
            cmd = [
                sys.executable, str(ROOT / "tools" / "flowpilot_owner_review_report.py"),
                "--file-receipt", str(a), "--document-receipt", str(b),
                "--select", REF, "--consent-ref", REF,
                "--question", QUESTION, "--approve-content", "--output", str(output),
            ]
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(verify_report_checksum(data))
            self.assertEqual(json.loads(run.stdout), data)
            for private in (REF, first["authorized_root"], QUESTION, "synthetic internal answer"):
                self.assertNotIn(private, run.stdout)
            again = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(again.returncode, 2)
            self.assertEqual(json.loads(again.stdout)["status"], "OWNER_REVIEW_REFUSED")

    def test_cli_refuses_bad_json_without_echoing_private_text(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            bad = d / "receipt.json"
            bad.write_text('{"token":"SECRET_DATA"', encoding="utf-8")
            run = subprocess.run([
                sys.executable, str(ROOT / "tools" / "flowpilot_owner_review_report.py"),
                "--file-receipt", str(bad),
            ], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("SECRET_DATA", run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
