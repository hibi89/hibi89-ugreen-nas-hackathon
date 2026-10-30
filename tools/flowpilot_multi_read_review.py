"""G88: redacted operator review of G87 read-only evidence; never NAS proof.

A normalized multi-read bundle is UNTRUSTED even when internally consistent.
This module exposes a bounded, indexed decision queue for a human operator
without showing paths, references, filenames, contents or claiming release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from flowpilot_multi_read_intake import (
    IntakeRefused, MAX_FILE_BYTES, _nonfinite, _strict_object,
    evaluate_multi_read,
)

OUTPUT_SCHEMA = "flowpilot-multi-read-review-v1"
ISSUE_CODES = {
    "PRESENT": "CLAIMED_PRESENT_NEEDS_INDEPENDENT_VERIFICATION",
    "MISSING": "CLAIMED_MISSING_NEEDS_OWNER_REVIEW",
    "VERSION_REVIEW": "VERSION_CONFLICT_REVIEW",
    "NOT_CHECKED": "EVIDENCE_NOT_CHECKED",
}


def build_review(bundle: Any) -> dict:
    """Convert strict G87 assessment to non-authorizing, redacted next steps."""
    assessment = evaluate_multi_read(bundle)
    status = assessment["status"]
    consistency = assessment["consistency"]

    blockers: list[str] = []
    if status == "WAITING_APPROVAL":
        blockers.append("OWNER_APPROVAL_REQUIRED")
    if status == "WAITING_USER":
        blockers.append("OWNER_INPUT_REQUIRED")
    if status == "BLOCKED":
        blockers.append(
            "CLAIMED_REQUIRED_FILE_MISSING"
            if any(item["state"] == "MISSING"
                   for item in assessment["item_results"])
            else "READ_ONLY_PLAN_BLOCKED"
        )
    if consistency == "CONFLICT":
        blockers.append("CONTRADICTORY_EVIDENCE")
    elif consistency == "INCOMPLETE":
        blockers.append("INCOMPLETE_OR_UNCONFIRMED_READ")
    if not blockers:
        blockers.append("SOURCE_NOT_INDEPENDENTLY_VERIFIED")

    queue: list[dict] = []
    for item in assessment["item_results"]:
        idx, state = item["requirement_index"], item["state"]
        if state not in ISSUE_CODES or type(idx) is not int or not 1 <= idx <= 100:
            raise IntakeRefused("Unsupported assessment item")
        reason = ("CONTRADICTORY_EVIDENCE" if consistency == "CONFLICT"
                  else "INCOMPLETE_OR_UNCONFIRMED_READ"
                  if consistency == "INCOMPLETE"
                  else ISSUE_CODES[state])
        queue.append({
            "requirement_index": idx,
            "claimed_state": state,
            "reason_code": reason,
            "owner_review_required": True,
        })

    return {
        "schema": OUTPUT_SCHEMA,
        "mode": "OFFLINE_OPERATOR_NORMALIZED_REVIEW_ONLY",
        "source_schema": assessment["schema"],
        "source_status": status,
        "consistency": consistency,
        "receipt_count": assessment["receipts_reviewed"],
        "finding_counts": {
            state: sum(row["claimed_state"] == state for row in queue)
            for state in ISSUE_CODES
        },
        "review_queue": queue,
        "review_item_count": len(queue),
        "review_required": True,
        "blocking_reasons": blockers,
        "decision": "HOLD",
        "owner_approval_granted_by_this_tool": False,
        "raw_paths_references_or_contents_returned": False,
        "operator_claims_independently_verified": False,
        "registered_expert_invocation_verified": False,
        "real_nas_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def _read_bounded_json(path: Path) -> Any:
    # Avoid accidental reads through symlinked parents, including on Windows.
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise IntakeRefused("Symlinked local input is unsupported")
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
        raise IntakeRefused("Unsupported local review input")
    with path.open("rb") as file:
        raw = file.read(MAX_FILE_BYTES + 1)
    if not 0 < len(raw) <= MAX_FILE_BYTES:
        raise IntakeRefused("Unsupported review input size")
    return json.loads(
        raw.decode("utf-8"), object_pairs_hook=_strict_object,
        parse_constant=_nonfinite,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="G88 redacted review of untrusted read-only claims; NOT NAS")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        review = build_review(_read_bounded_json(args.input))
        print(json.dumps(review, ensure_ascii=False, sort_keys=True))
        return 2 if review["consistency"] == "CONFLICT" else 0
    except (IntakeRefused, OSError, ValueError, UnicodeError, RecursionError):
        print(json.dumps({
            "status": "G88_REVIEW_REFUSED", "release_gate": "HOLD",
            "real_nas_verified": False,
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
