"""Two-stage FlowPilot selected-document consent and provenance boundary.

Consumes only operator-normalized, UNTRUSTED file-agent claims from the
existing G61 intake contract, never raw Uliya SDK responses. This builds a
SYNTHETIC instruction DRAFT for an optional document-agent; it does not call
NAS, Uliya, an Expert, an LLM, or a filesystem. User data MUST NOT be passed
to any external runtime based on this draft alone.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from flowpilot_agent_result_intake import (
    evaluate_normalized_receipt,
    IntakeRefused,
    REF_ID,
)

MAX_QUESTION_CHARS = 512
MAX_SELECTED = 10


def _result(status: str, *, count: int = 0, reason: str = "", draft: dict | None = None) -> dict:
    value = {
        "schema": "flowpilot-selected-document-preview-v1",
        "status": status,
        "selected_count": count,
        "reason": reason,
        "file_agent_verified_at_runtime": False,
        "document_agent_invoked": False,
        "document_content_read": False,
        "nas_verified": False,
        "sovia_integrated": False,
        "release_gate": "HOLD",
        "devpost_submitted": False,
    }
    if draft is not None:
        value["synthetic_instruction_draft"] = draft
    return value


def _references(value: object) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_SELECTED:
        raise IntakeRefused("Invalid reference selection")
    if any(not isinstance(ref, str) or not REF_ID.fullmatch(ref) for ref in value):
        raise IntakeRefused("Unbound or invalid document reference")
    if len(set(value)) != len(value):
        raise IntakeRefused("Duplicate document reference")
    return value


def _question(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_QUESTION_CHARS:
        raise IntakeRefused("Missing or unbounded document question")
    if value != value.strip() or unicodedata.normalize("NFKC", value) != value:
        raise IntakeRefused("Noncanonical document question")
    if any(ord(c) < 32 or ord(c) == 127 or unicodedata.category(c) == "Cf" for c in value):
        raise IntakeRefused("Control character in document question")
    return value


def preview_selected_document(
    first_stage: dict,
    *,
    selected_refs: list[str] | None = None,
    question: str | None = None,
    consented_refs: list[str] | None = None,
    content_approved: bool = False,
) -> dict:
    """Require bound metadata evidence then separate exact-reference consent.

    File-agent 'complete/permission' flags are untrusted assertions.
    The only possible instruction payload is marked SYNTHETIC and NOT_RUN.
    """
    if type(content_approved) is not bool:
        raise IntakeRefused("Approval must be a strict boolean")
    evidence = evaluate_normalized_receipt(first_stage)
    if evidence["goal_type"] != "SUMMARIZE_SELECTED":
        raise IntakeRefused("Document delegation requires selected-document intent")
    if evidence["plan_state"] != "READY_FOR_ADAPTER_CHECK":
        return _result("WAITING_METADATA_APPROVAL", reason="Owner metadata/processing approval incomplete")
    agent = first_stage["file_agent_report"]
    flags = (
        agent["permission_confirmed"],
        agent["registered_adapter_confirmed"],
        agent["scan_complete"],
        agent["pagination_complete"],
    )
    if any(flag is not True for flag in flags) or agent["failed"] is not False:
        return _result("BLOCKED_UNVERIFIED_INVENTORY", reason="Incomplete or unverified file enumeration")
    if evidence["status"] == "BLOCKED":
        return _result("BLOCKED_UNVERIFIED_INVENTORY", reason="First-stage evidence blocked")
    if not selected_refs or question is None:
        return _result("WAITING_USER", reason="Select returned document references and supply the exact question")
    selection = _references(selected_refs)
    exact_question = _question(question)
    consented = _references(consented_refs if consented_refs is not None else [])
    if not set(consented).issubset(set(selection)):
        raise IntakeRefused("Consent refers to an unselected document")

    # The G61 normalized intake has already rejected out-of-scope paths,
    # restricted filenames, unregistered actions, duplicated references,
    # symlinks with false containment, and unknown receipt fields.
    present_paths = {
        first_stage["required_paths"][row["requirement_index"] - 1]
        for row in evidence["item_results"]
        if row["state"] == "PRESENT" and row["reference_count"] == 1
    }
    eligible: dict[str, str] = {}
    for row in agent["observations"]:
        if (row["relative_path"] in present_paths and row["contained"] is True
                and row["is_symlink"] is False and row["reference"]):
            eligible[row["reference"]] = row["relative_path"]
    if any(ref not in eligible for ref in selection):
        raise IntakeRefused("Selected reference is missing, conflicting, or outside owner scope")
    if content_approved is not True or set(consented) != set(selection):
        return _result("WAITING_SEPARATE_DOCUMENT_APPROVAL", count=len(selection),
                       reason="Exact-reference content consent required")
    if first_stage["origin"] != "SYNTHETIC_TEST":
        return _result("BLOCKED_RUNTIME_PROVENANCE_UNVERIFIED", count=len(selection),
                       reason="An operator-transcribed receipt cannot authorize dispatch")

    # This is a STRUCTURED DRAFT for future adapter code, never an executable
    # delegate invocation, shell script, or evidence of current capabilities.
    instructions = {
        "schema": "flowpilot-document-agent-instruction-draft-v1",
        "origin": "SYNTHETIC_TEST_ONLY",
        "target": "document-agent",
        "allowed_actions": ["ug-document metadata", "ug-document qa",
                            "ug-document extract", "ug-document reconcile"],
        "authorized_root": first_stage["authorized_root"],
        "selected_references": [
            {"reference": ref, "approved_relative_path": eligible[ref]}
            for ref in selection
        ],
        "owner_question_verbatim": exact_question,
        "question_sha256": hashlib.sha256(exact_question.encode("utf-8")).hexdigest(),
        "owner_scope_and_content_consent_asserted": True,
        "require_fresh_runtime_permission_verification": True,
        "require_registered_expert_and_supported_schema": True,
        "require_processing_location_disclosure": True,
        "read_only": True,
        "allow_extra_references": False,
        "allow_discovery_beyond_first_stage": False,
        "no_filesystem_mutation_or_network_transfer": True,
        "actual_dispatch_performed": False,
    }
    return _result("SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED",
                   count=len(selection), draft=instructions)


def redacted_public_view(result: dict) -> dict:
    """Safe status view; no owner root, refs, filenames or question are echoed."""
    return {key: value for key, value in result.items()
            if key != "synthetic_instruction_draft"}


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Offline document-stage preview. NOT Uliya/NAS.")
    parser.add_argument("--file-receipt", type=Path, required=True)
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--question", default=None)
    parser.add_argument("--consent-ref", action="append", default=[])
    parser.add_argument("--approve-content", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = args.file_receipt
        if (receipt.is_symlink() or not receipt.is_file()
                or not 0 < receipt.stat().st_size <= 65536):
            raise IntakeRefused("Unsupported source receipt")
        content = json.loads(receipt.read_text(encoding="utf-8"))
        outcome = preview_selected_document(
            content, selected_refs=args.select, question=args.question,
            consented_refs=args.consent_ref, content_approved=args.approve_content)
        print(json.dumps(redacted_public_view(outcome), ensure_ascii=False))
        return 0
    except (IntakeRefused, ValueError, OSError, UnicodeError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status": "SELECTED_DOCUMENT_STAGE_REFUSED",
                          "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
