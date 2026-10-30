"""G94: direct LOCAL metadata audit -> redacted owner review, not Uliya/NAS.

The existing G62 local lstat reader is not an official Expert; NEVER forge
a G61/G87 receipt labelled file-agent from its observations. Use its honest
local-only result and map index/state to an owner-facing review contract.
No file contents, network, external agent or output files are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from flowpilot_owner_local_audit import (
    OwnerAuditError, _versions, inspect_owner_folder,
)

SCHEMA = "flowpilot-local-owner-review-v1"
REASONS = {
    "PRESENT": "LOCAL_METADATA_PRESENT_REQUIRES_OWNER_REVIEW",
    "MISSING": "LOCAL_REQUIRED_FILE_MISSING",
    "VERSION_REVIEW": "LOCAL_VERSION_CANDIDATE_REVIEW",
    "NOT_CHECKED": "LOCAL_METADATA_UNCHECKED",
}
ALLOWED_STATUSES = {
    "NEEDS_REVIEW", "BLOCKED", "NOT_CHECKED",
    "WAITING_APPROVAL", "WAITING_USER",
}


def build_local_review(
    root: Path,
    required: Sequence[str],
    *,
    version_candidates: dict[str, Sequence[str]] | None = None,
    goal: str = "check required files",
    metadata_consent: bool = False,
) -> dict[str, Any]:
    """Read exact owner-selected LOCAL lstat metadata only after consent.

    All input validation and the read-only planner live in G62. G94 never
    accepts raw SDK output or falsely creates registered-Agent receipts.
    No owner path or filename is included in the returned mapping.
    """
    if type(metadata_consent) is not bool:
        raise OwnerAuditError("Invalid explicit local metadata consent")
    audit = inspect_owner_folder(
        root, required, version_candidates=version_candidates,
        goal=goal, metadata_consent=metadata_consent,
    )
    status = audit["status"]
    if status not in ALLOWED_STATUSES:
        raise OwnerAuditError("Unexpected local audit state")
    rows = audit["items"]
    if not isinstance(rows, list) or len(rows) > 100:
        raise OwnerAuditError("Unexpected local audit size")
    queue: list[dict] = []
    for expected_index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != {
            "index", "state", "local_reference_count",
        }:
            raise OwnerAuditError("Unexpected local audit row")
        state = row["state"]
        if (type(row["index"]) is not int or row["index"] != expected_index
                or state not in REASONS
                or type(row["local_reference_count"]) is not int
                or not 0 <= row["local_reference_count"] <= 20):
            raise OwnerAuditError("Unexpected local audit item")
        queue.append({
            "requirement_index": expected_index,
            "observed_state": state,
            "reason_code": REASONS[state],
            "owner_review_required": True,
        })
    if not audit["inspected_local_metadata"] and queue:
        raise OwnerAuditError("Uninspected local rows cannot become findings")
    if audit["inspected_local_metadata"] and len(queue) != audit["item_count"]:
        raise OwnerAuditError("Incomplete local audit report")
    return {
        "schema": SCHEMA,
        "mode": "OWNER_CONSENTED_LOCAL_LSTAT_REVIEW_NOT_NAS",
        "source_status": status,
        "metadata_inspection_executed": audit["inspected_local_metadata"],
        "review_queue": queue,
        "review_item_count": len(queue),
        "finding_counts": {
            state: sum(row["observed_state"] == state for row in queue)
            for state in REASONS
        },
        "review_required": True,
        "blocking_reasons": (
            ["OWNER_APPROVAL_REQUIRED"] if status == "WAITING_APPROVAL"
            else ["OWNER_INPUT_REQUIRED"] if status == "WAITING_USER"
            else ["LOCAL_AUDIT_BLOCKED"] if status == "BLOCKED"
            else ["LOCAL_METADATA_UNCHECKED"] if status == "NOT_CHECKED"
            else ["LOCAL_EVIDENCE_REQUIRES_OWNER_REVIEW"]
        ),
        "decision": "HOLD",
        "file_contents_opened": False,
        "raw_paths_references_or_contents_returned": False,
        "registered_expert_invocation_verified": False,
        "real_nas_verified": False,
        "official_creator_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="G94 consented LOCAL metadata-to-review bridge; NOT NAS."
    )
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--required", required=True, action="append")
    ap.add_argument("--candidate", action="append", default=[])
    ap.add_argument("--goal", default="check required files")
    ap.add_argument("--approve-local-metadata", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = build_local_review(
            args.root, args.required,
            version_candidates=_versions(args.candidate),
            goal=args.goal, metadata_consent=args.approve_local_metadata,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if result["source_status"] in {"BLOCKED", "NOT_CHECKED"} else 0
    except (OwnerAuditError, OSError, ValueError, TypeError):
        print(json.dumps({
            "status": "G94_LOCAL_REVIEW_REFUSED",
            "real_nas_verified": False,
            "release_gate": "HOLD",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
