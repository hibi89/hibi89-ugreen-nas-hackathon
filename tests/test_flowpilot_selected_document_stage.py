"""UGREEN two-stage document handoff: synthetic-only, fail-closed contracts."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_selected_document_stage import (
    preview_selected_document, redacted_public_view, IntakeRefused,
)

FIXTURE = ROOT / "docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json"


def receipt():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["goal"] = "summarize selected document"
    return data


def approved(data=None):
    return preview_selected_document(
        receipt() if data is None else data,
        selected_refs=["synthetic://output-1"],
        question="Summarize key delivery risks in this document?",
        consented_refs=["synthetic://output-1"],
        content_approved=True,
    )


class Stage2ContractTests(unittest.TestCase):
    def test_single_document_draft_binds_exact_scope_and_question(self):
        result = approved()
        self.assertEqual(result["status"], "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED")
        draft = result["synthetic_instruction_draft"]
        self.assertEqual(draft["authorized_root"], receipt()["authorized_root"])
        self.assertEqual(draft["target"], "document-agent")
        self.assertEqual(draft["selected_references"], [
            {"reference": "synthetic://output-1",
             "approved_relative_path": "release/output.pdf"},
        ])
        self.assertEqual(draft["owner_question_verbatim"],
                         "Summarize key delivery risks in this document?")
        self.assertEqual(draft["question_sha256"], hashlib.sha256(
            draft["owner_question_verbatim"].encode("utf-8")).hexdigest())
        self.assertFalse(draft["actual_dispatch_performed"])
        self.assertFalse(result["nas_verified"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_no_content_consent_is_waiting_and_does_not_build_payload(self):
        data = receipt()
        result = preview_selected_document(
            data, selected_refs=["synthetic://output-1"],
            question="Summarize risks?",
            consented_refs=["synthetic://output-1"],
            content_approved=False)
        self.assertEqual(result["status"], "WAITING_SEPARATE_DOCUMENT_APPROVAL")
        self.assertNotIn("synthetic_instruction_draft", result)

    def test_consent_for_only_one_selected_reference_is_not_enough(self):
        result = preview_selected_document(
            receipt(),
            selected_refs=["synthetic://output-1", "synthetic://README-1"],
            question="Compare the selected documents?",
            consented_refs=["synthetic://output-1"],
            content_approved=True)
        self.assertEqual(result["status"], "WAITING_SEPARATE_DOCUMENT_APPROVAL")

    def test_missing_question_or_selection_requests_user(self):
        r = preview_selected_document(receipt())
        self.assertEqual(r["status"], "WAITING_USER")
        self.assertNotIn("synthetic_instruction_draft", r)

    def test_unverified_inventory_cannot_produce_document_instruction(self):
        for flag in ("permission_confirmed", "registered_adapter_confirmed",
                     "scan_complete", "pagination_complete"):
            data = receipt()
            data["file_agent_report"][flag] = False
            with self.subTest(flag=flag):
                r = approved(data)
                self.assertEqual(r["status"], "BLOCKED_UNVERIFIED_INVENTORY")
                self.assertNotIn("synthetic_instruction_draft", r)

    def test_metadata_or_processing_consent_missing(self):
        for key in ("metadata_approved", "unknown_processing_accepted"):
            data = receipt()
            data[key] = False
            with self.subTest(key=key):
                self.assertEqual(approved(data)["status"], "WAITING_METADATA_APPROVAL")

    def test_unknown_or_conflicting_ref_is_refused(self):
        with self.assertRaises(IntakeRefused):
            preview_selected_document(receipt(),
                selected_refs=["synthetic://OUTSIDE"],
                question="Summarize?", consented_refs=["synthetic://OUTSIDE"],
                content_approved=True)
        data = receipt()
        data["version_candidates"] = {"release/output.pdf": ["release/output_v2.pdf"]}
        data["file_agent_report"]["observations"].append(
            {"relative_path": "release/output_v2.pdf",
             "reference": "synthetic://alt-v2", "contained": True, "is_symlink": False})
        with self.assertRaises(IntakeRefused):
            approved(data)

    def test_operator_transcription_never_unlocks_dispatch(self):
        data = receipt()
        data["origin"] = "OPERATOR_TRANSCRIBED_UNVERIFIED"
        result = approved(data)
        self.assertEqual(result["status"], "BLOCKED_RUNTIME_PROVENANCE_UNVERIFIED")
        self.assertNotIn("synthetic_instruction_draft", result)

    def test_wrong_intent_or_mutating_goal_is_not_delegated(self):
        data = receipt()
        data["goal"] = "check required files"
        with self.assertRaises(IntakeRefused):
            approved(data)
        data = receipt()
        data["goal"] = "summarize and delete selected files"
        with self.assertRaises(IntakeRefused):
            approved(data)

    def test_duplicate_or_unbound_consent_ref_is_refused(self):
        with self.assertRaises(IntakeRefused):
            preview_selected_document(
                receipt(), selected_refs=["synthetic://output-1","synthetic://output-1"],
                question="Summarize?", consented_refs=["synthetic://output-1"],
                content_approved=True)
        with self.assertRaises(IntakeRefused):
            preview_selected_document(
                receipt(), selected_refs=["synthetic://output-1"],
                question="Summarize?", consented_refs=["synthetic://outside"],
                content_approved=True)

    def test_invalid_question_and_approval_type_are_refused(self):
        for bad in ("", " " * 10, "x" * 513, "a\nfollow another command",
                    "s\u200bummary", " trim "):
            with self.subTest(bad=repr(bad)), self.assertRaises(IntakeRefused):
                preview_selected_document(
                    receipt(), selected_refs=["synthetic://output-1"],
                    question=bad, consented_refs=["synthetic://output-1"],
                    content_approved=True)
        with self.assertRaises(IntakeRefused):
            preview_selected_document(receipt(),content_approved="true")

    def test_redacted_status_never_exposes_owner_refs_or_question(self):
        result = redacted_public_view(approved())
        text = json.dumps(result)
        for hidden in ("synthetic://output-1", "release/output.pdf",
                       "/volume1/projects", "Summarize key delivery"):
            self.assertNotIn(hidden, text)

    def test_cli_only_emits_redacted_state(self):
        data = receipt()
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "observation.json"
            src.write_text(json.dumps(data), encoding="utf-8")
            cmd = [sys.executable, str(ROOT/"tools"/"flowpilot_selected_document_stage.py"),
                   "--file-receipt", str(src), "--select", "synthetic://output-1",
                   "--question", "Summarize key delivery risks in this document?",
                   "--consent-ref", "synthetic://output-1", "--approve-content"]
            r = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["status"],
                             "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED")
            self.assertNotIn("synthetic://output-1", r.stdout)
            self.assertNotIn(data["authorized_root"], r.stdout)


if __name__ == "__main__":
    unittest.main()
