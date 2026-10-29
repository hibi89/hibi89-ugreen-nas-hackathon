"""FlowPilot 3.0 owner-review report from three offline, UNTRUSTED stages.

Stage 1: untrusted normalized file-agent metadata claim.
Stage 2: exact document selection and separate content-consent checks.
Stage 3: optional untrusted normalized document-agent result.

This is not a Uliya adapter or NAS execution proof. All externally supplied
flags, claimed document answers, and checksums are unverified. The JSON report
contains neither owner paths/references nor document content. Reports carry a
deterministic checksum for accidental-change detection, NOT authentication.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from flowpilot_agent_result_intake import evaluate_normalized_receipt, IntakeRefused
from flowpilot_selected_document_stage import preview_selected_document, redacted_public_view
from flowpilot_document_result_intake import assess_document_result

MAX_RECEIPT_BYTES = 65536
SCHEMA = "flowpilot-synthetic-owner-review-v1"
CHECKSUM_FIELD = "public_report_sha256"
_ALLOWED_STATES = frozenset({"PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW"})


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def verify_report_checksum(report: dict) -> bool:
    """Detect accidental edits. SHA-256 alone does not authenticate a claim."""
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        return False
    checksum = report.get(CHECKSUM_FIELD)
    if not isinstance(checksum, str) or len(checksum) != 64:
        return False
    try:
        unsigned = {key: value for key, value in report.items()
                    if key != CHECKSUM_FIELD}
        return hashlib.sha256(_canonical(unsigned)).hexdigest() == checksum
    except (TypeError, ValueError, UnicodeError):
        return False


def assemble_review(
    file_receipt: dict,
    *,
    document_receipt: dict | None = None,
    selected_refs: list[str] | None = None,
    question: str | None = None,
    consented_refs: list[str] | None = None,
    content_approved: bool = False,
) -> dict:
    """Produce a redacted complete local review without invoking any Expert.

    For a selected-document request, stage 3 stays NOT_CHECKED until approved
    and a bounded result is supplied. Any unsupported or malformed document
    receipt is refused rather than silently counted as a successful check.
    """
    if type(content_approved) is not bool:
        raise IntakeRefused("Content approval must be a strict boolean")
    try:
        first = evaluate_normalized_receipt(file_receipt)
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise IntakeRefused("First-stage claim invalid") from exc
    states = first["item_results"]
    if not isinstance(states, list) or any(
        not isinstance(row, dict) or row.get("state") not in _ALLOWED_STATES
        for row in states
    ):
        raise IntakeRefused("Invalid first-stage item states")
    counts = Counter(row["state"] for row in states)
    summary = {state: counts[state] for state in
               ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")}
    goal_type = first["goal_type"]
    document_requested = goal_type == "SUMMARIZE_SELECTED"
    if not document_requested and (
        document_receipt is not None or selected_refs or question is not None
        or consented_refs or content_approved
    ):
        raise IntakeRefused("Unexpected document stage for this intent")

    document_stage = {
        "status": "NOT_REQUESTED" if not document_requested else "CONTENT_NOT_CHECKED",
        "selected_count": 0,
        "claimed_answer_count": 0,
        "actual_document_agent_invoked": False,
    }
    if document_requested:
        try:
            preview = preview_selected_document(
                file_receipt,
                selected_refs=selected_refs,
                question=question,
                consented_refs=consented_refs,
                content_approved=content_approved,
            )
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            raise IntakeRefused("Document plan or consent invalid") from exc
        safe_preview = redacted_public_view(preview)
        document_stage["status"] = safe_preview["status"]
        document_stage["selected_count"] = safe_preview["selected_count"]
        if document_receipt is not None:
            if preview["status"] == "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED":
                try:
                    result = assess_document_result(
                        file_receipt, document_receipt,
                        selected_refs=selected_refs, question=question,
                        consented_refs=consented_refs,
                        content_approved=content_approved,
                    )
                except (KeyError, ValueError, TypeError, AttributeError) as exc:
                    raise IntakeRefused("Document claim fails approved binding") from exc
                document_stage["status"] = result["status"]
                document_stage["claimed_answer_count"] = result["unverified_answer_claims"]
                document_stage["reported_complete_claim"] = result["reported_complete_claim"]
            else:
                # An unapproved pre-supplied document payload is never
                # evaluated, stored, forwarded, or treated as evidence.
                document_stage["status"] = safe_preview["status"]

    first_status = first["status"]
    if first_status == "BLOCKED" or counts["MISSING"]:
        status = "SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW"
    elif first_status in ("WAITING_USER", "WAITING_APPROVAL"):
        status = "WAITING_OWNER_INPUT_OR_APPROVAL"
    else:
        status = "SYNTHETIC_NEEDS_REVIEW"
    report = {
        "schema": SCHEMA,
        "status": status,
        "source": "UNTRUSTED_OPERATOR_NORMALIZED_LOCAL_ONLY",
        "goal_type": goal_type,
        "file_stage": {
            "status": first_status,
            "item_count": len(states),
            "counts": summary,
            "items": [
                {"requirement_index": row["requirement_index"],
                 "unverified_state": row["state"]}
                for row in states
            ],
            "official_registered_file_agent_invoked": False,
        },
        "document_stage": document_stage,
        "trace": [
            {"stage": "file_agent", "state": "UNTRUSTED_OFFLINE_CLAIM"},
            {"stage": "separate_document_consent",
             "state": ("NOT_APPLICABLE" if not document_requested
                       else "ASSERTED_ONLY_NOT_RUNTIME_VERIFIED"
                       if content_approved else "WAITING_OR_NOT_APPROVED")},
            {"stage": "document_agent", "state": document_stage["status"]},
            {"stage": "owner_review", "state": status},
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
    report[CHECKSUM_FIELD] = hashlib.sha256(_canonical(report)).hexdigest()
    return report


def _load_bounded(path: Path) -> dict:
    if (not isinstance(path, Path) or path.is_symlink() or path.parent.is_symlink()
            or not path.is_file() or not 0 < path.stat().st_size <= MAX_RECEIPT_BYTES):
        raise IntakeRefused("Unsafe or oversized receipt")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise IntakeRefused("Receipt must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redacted offline owner review. NOT NAS.")
    parser.add_argument("--file-receipt", required=True, type=Path)
    parser.add_argument("--document-receipt", type=Path)
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--question")
    parser.add_argument("--consent-ref", action="append", default=[])
    parser.add_argument("--approve-content", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional new-only public report JSON")
    args = parser.parse_args(argv)
    try:
        first = _load_bounded(args.file_receipt)
        document = (_load_bounded(args.document_receipt)
                    if args.document_receipt is not None else None)
        report = assemble_review(
            first, document_receipt=document,
            selected_refs=args.select or None, question=args.question,
            consented_refs=args.consent_ref or None,
            content_approved=args.approve_content,
        )
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
        if args.output is not None:
            if args.output.is_symlink() or args.output.parent.is_symlink():
                raise IntakeRefused("Output symlink not allowed")
            with args.output.open("x", encoding="utf-8") as f:
                f.write(rendered + "\n")
        print(rendered)
        return 0
    except (IntakeRefused, OSError, UnicodeError, ValueError, TypeError,
            KeyError, json.JSONDecodeError):
        print(json.dumps({"status": "OWNER_REVIEW_REFUSED", "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
