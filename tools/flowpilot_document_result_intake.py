"""Fail-closed *synthetic* document-result intake for NAS FlowPilot.

Stage 1 is an operator-normalized, untrusted file-agent receipt. Stage 2 is
explicit per-reference document-content approval. This third stage checks an
untrusted document-agent-shaped result against the exact approved draft.

No official Uliya/NAS/Expert is invoked, no content is opened, and the output
never exposes owner paths, references, questions, or document answer text.
All apparent expert success remains an unverified synthetic claim.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from flowpilot_agent_result_intake import IntakeRefused
from flowpilot_selected_document_stage import (
    preview_selected_document,
    redacted_public_view,
)

SCHEMA = "flowpilot-normalized-document-result-v1"
MAX_RECEIPT_BYTES = 65536
MAX_ANSWER_CHARS = 4096
OPERATIONS = frozenset({
    "ug-document metadata", "ug-document qa",
    "ug-document extract", "ug-document reconcile",
})
RESULT_KEYS = frozenset({
    "schema", "origin", "agent", "operation", "authorized_root",
    "request_sha256", "question_sha256", "permission_confirmed",
    "registered_adapter_confirmed", "scan_complete", "failed", "results",
})
ITEM_KEYS = frozenset({"reference", "state", "answer"})
ITEM_STATES = frozenset({"ANSWERED", "CONTENT_NOT_CHECKED", "FAILED"})


def fingerprint(draft: dict) -> str:
    """SHA of the full ordered consented instruction, not a NAS attestation."""
    if not isinstance(draft, dict) or draft.get("schema") != "flowpilot-document-agent-instruction-draft-v1":
        raise IntakeRefused("Invalid synthetic document instruction")
    data = json.dumps(draft, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate(receipt: Any, draft: dict) -> list[dict]:
    if not isinstance(receipt, dict) or set(receipt) != RESULT_KEYS:
        raise IntakeRefused("Unexpected document result structure")
    try:
        size = len(json.dumps(receipt, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise IntakeRefused("Invalid result serialization") from exc
    if size > MAX_RECEIPT_BYTES:
        raise IntakeRefused("Document result exceeds bounded size")
    if (receipt["schema"] != SCHEMA or receipt["origin"] != "SYNTHETIC_TEST"
            or receipt["agent"] != "document-agent"
            or not isinstance(receipt["operation"], str)
            or receipt["operation"] not in OPERATIONS):
        raise IntakeRefused("Unrecognized or non-synthetic document result")
    if (receipt["authorized_root"] != draft["authorized_root"]
            or receipt["request_sha256"] != fingerprint(draft)
            or receipt["question_sha256"] != draft["question_sha256"]):
        raise IntakeRefused("Result does not bind to approved root, references and question")
    for field in ("permission_confirmed", "registered_adapter_confirmed", "scan_complete", "failed"):
        if type(receipt[field]) is not bool:
            raise IntakeRefused("Untrusted permission, completeness or failure flag")
    expected_refs = [entry["reference"] for entry in draft["selected_references"]]
    rows = receipt["results"]
    if not isinstance(rows, list) or len(rows) > len(expected_refs):
        raise IntakeRefused("Invalid bounded document result rows")
    if receipt["failed"] and rows:
        raise IntakeRefused("A failed operation cannot include accepted result rows")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != ITEM_KEYS:
            raise IntakeRefused("Unknown document result fields")
        ref = row["reference"]
        if not isinstance(ref, str) or ref not in expected_refs or ref in seen:
            raise IntakeRefused("Unknown, duplicate, or unauthorized document reference")
        seen.add(ref)
        if not isinstance(row["state"], str) or row["state"] not in ITEM_STATES:
            raise IntakeRefused("Unknown document result state")
        text = row["answer"]
        if row["state"] == "ANSWERED":
            if (not isinstance(text, str) or not text.strip()
                    or len(text) > MAX_ANSWER_CHARS or "\x00" in text):
                raise IntakeRefused("Invalid or unbounded document answer")
        elif text is not None:
            raise IntakeRefused("Unverified answer supplied for an unprocessed document")
    return rows


def assess_document_result(
    first_stage: dict,
    document_receipt: dict,
    *,
    selected_refs: list[str] | None = None,
    question: str | None = None,
    consented_refs: list[str] | None = None,
    content_approved: bool = False,
) -> dict:
    """Validate the synthetic stage-3 result; never promote to actual NAS READY."""
    preview = preview_selected_document(
        first_stage, selected_refs=selected_refs, question=question,
        consented_refs=consented_refs, content_approved=content_approved,
    )
    if preview["status"] != "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED":
        return redacted_public_view(preview)
    draft = preview["synthetic_instruction_draft"]
    rows = _validate(document_receipt, draft)
    by_ref = {row["reference"]: row for row in rows}
    claims = []
    for index, entry in enumerate(draft["selected_references"], 1):
        row = by_ref.get(entry["reference"])
        state = row["state"] if row is not None else "CONTENT_NOT_CHECKED"
        claims.append({"selection_index": index, "unverified_state": state})
    all_answered = (len(rows) == len(claims) and
                    all(row["unverified_state"] == "ANSWERED" for row in claims))
    flags = ("permission_confirmed", "registered_adapter_confirmed", "scan_complete")
    claims_complete = (all(document_receipt[f] is True for f in flags)
                       and document_receipt["failed"] is False)
    return {
        "schema": "flowpilot-document-stage-assessment-v1",
        "status": ("SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW"
                   if all_answered and claims_complete else
                   "SYNTHETIC_INCOMPLETE_OR_FAILED_NEEDS_REVIEW"),
        "draft_sha256": fingerprint(draft),
        "selected_count": len(claims),
        "reported_count": len(rows),
        "unverified_answer_claims": sum(row["unverified_state"] == "ANSWERED" for row in claims),
        "unverified_items": claims,
        "reported_complete_claim": claims_complete,
        "contains_raw_paths_references_questions_or_answers": False,
        "document_agent_invoked": False,
        "document_content_read": False,
        "effective_permissions_verified": False,
        "nas_verified": False,
        "ready_certified": False,
        "release_gate": "HOLD",
        "devpost_submitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Offline claimed document-result audit; NOT NAS")
    parser.add_argument("--file-receipt", required=True, type=Path)
    parser.add_argument("--document-receipt", required=True, type=Path)
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--question", required=True)
    parser.add_argument("--consent-ref", action="append", default=[])
    parser.add_argument("--approve-content", action="store_true")
    args = parser.parse_args(argv)
    try:
        def read_bounded(path: Path) -> dict:
            if (path.is_symlink() or path.parent.is_symlink() or not path.is_file()
                    or not 0 < path.stat().st_size <= MAX_RECEIPT_BYTES):
                raise IntakeRefused("Unsafe or oversized normalized receipt")
            return json.loads(path.read_text(encoding="utf-8"))
        result = assess_document_result(
            read_bounded(args.file_receipt), read_bounded(args.document_receipt),
            selected_refs=args.select, question=args.question,
            consented_refs=args.consent_ref,
            content_approved=args.approve_content)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (IntakeRefused, ValueError, TypeError, OSError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"status": "DOCUMENT_RESULT_REFUSED", "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
