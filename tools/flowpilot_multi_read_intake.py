"""G87: reconcile bounded read-only file-agent receipts across multiple steps.

This consumes the existing G61 OPERATOR-NORMALIZED, UNTRUSTED JSON contract,
never raw Uliya SDK data. It never invokes NAS, experts, HAE, LA, providers,
network, or filesystem outside the input JSON. A claimed complete ls/find
enumeration can support only provisional offline evidence, not live NAS proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from flowpilot_agent_result_intake import (
    IntakeRefused, evaluate_normalized_receipt,
)
from flowpilot.pipeline import evaluate_offline
from flowpilot.evidence import ObservationBatch, Observed

SCHEMA = "flowpilot-multi-read-receipts-v1"
OUTPUT_SCHEMA = "flowpilot-multi-read-assessment-v1"
MAX_RECEIPTS = 8
MAX_FILE_BYTES = 128 * 1024
ENUMERATION_ACTIONS = frozenset(("ug-filesystem ls", "ug-filesystem find"))


def _strict_object(pairs: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise IntakeRefused("Duplicate JSON object key")
        out[key] = value
    return out


def _nonfinite(_: str) -> None:
    raise IntakeRefused("Unsupported nonfinite numeric value")


def _context(receipt: dict) -> tuple:
    return (
        receipt["schema"], receipt["origin"], receipt["goal"],
        receipt["authorized_root"], tuple(receipt["required_paths"]),
        receipt["metadata_approved"], receipt["unknown_processing_accepted"],
        # G61 validates the candidate schema, but not the input ordering.
        tuple(sorted(
            (key, tuple(names))
            for key, names in receipt.get("version_candidates", {}).items()
        )),
    )


def evaluate_multi_read(bundle: Any) -> dict:
    """Cross-check operator claims; never establish real NAS permissions.

    One claimed full ls/find enumeration is required to assert provisional
    missing files. Supplementary stat records may corroborate, but never
    supply absent items or override the authoritative enumeration.
    """
    if (not isinstance(bundle, dict) or set(bundle) != {"schema", "receipts"}
            or bundle["schema"] != SCHEMA):
        raise IntakeRefused("Unexpected multi-read input schema")
    receipts = bundle["receipts"]
    if not isinstance(receipts, list) or not 1 <= len(receipts) <= MAX_RECEIPTS:
        raise IntakeRefused("Unsupported receipt count")

    expected_context: tuple | None = None
    canonical: dict[str, tuple[str, bool, bool | None]] | None = None
    observations: list[dict[str, tuple[str, bool, bool | None]]] = []
    all_source_flags = True
    operations: list[str] = []
    complete_scan_claims = 0
    for receipt in receipts:
        # This validates every G61 receipt, exact nested fields, permissions
        # booleans, owner scope, path restrictions and bounded references.
        evaluate_normalized_receipt(receipt)
        ctx = _context(receipt)
        if expected_context is None:
            expected_context = ctx
        elif ctx != expected_context:
            raise IntakeRefused("Receipts have different owner scope or consent")
        agent = receipt["file_agent_report"]
        op = agent["operation"]
        operations.append(op)
        flags = all((
            agent["permission_confirmed"] is True,
            agent["registered_adapter_confirmed"] is True,
            agent["failed"] is False,
        ))
        all_source_flags = all_source_flags and flags

        row_map: dict[str, tuple[str, bool, bool | None]] = {}
        for row in agent["observations"]:
            if row["relative_path"] in row_map:
                raise IntakeRefused("Multiple incompatible records for one path")
            row_map[row["relative_path"]] = (
                row["reference"], row["is_symlink"], row["contained"]
            )
        observations.append(row_map)
        full = (op in ENUMERATION_ACTIONS and flags
                and agent["scan_complete"] is True
                and agent["pagination_complete"] is True)
        if full:
            complete_scan_claims += 1
            if canonical is None:
                canonical = row_map

    assert expected_context is not None
    first = receipts[0]
    # Conflicting sources are not silently merged or re-labeled as present.
    # A new path reported by supplementary stat contradicts a claimed full
    # enumeration; mismatched refs/symlink flags also invalidate the merge.
    conflict = False
    if canonical is not None:
        for row_map in observations:
            if any(path not in canonical or canonical[path] != value
                   for path, value in row_map.items()):
                conflict = True
                break
        for receipt, row_map in zip(receipts, observations):
            agent = receipt["file_agent_report"]
            if (agent["operation"] in ENUMERATION_ACTIONS
                    and agent["scan_complete"] is True
                    and agent["pagination_complete"] is True
                    and row_map != canonical):
                conflict = True
                break

    claimed_complete = (canonical is not None and all_source_flags and not conflict)
    rows = canonical if claimed_complete else {}
    batch = ObservationBatch(
        authorized_root=first["authorized_root"],
        observations=tuple(
            Observed(path, value[0], is_symlink=value[1], contained=value[2])
            for path, value in rows.items()
        ),
        permission_confirmed=claimed_complete,
        registered_adapter_confirmed=claimed_complete,
        scan_complete=claimed_complete,
        pagination_complete=claimed_complete,
        failed=not claimed_complete,
    )
    result = evaluate_offline(
        first["goal"], first["authorized_root"], first["required_paths"],
        metadata_approved=first["metadata_approved"],
        unknown_processing_accepted=first["unknown_processing_accepted"],
        batch=batch,
        version_candidates=first.get("version_candidates", {}),
    )
    findings = result.report.items if result.report else ()
    # Even a matching self-attested scan is not a proof of a registered agent.
    return {
        "schema": OUTPUT_SCHEMA,
        "mode": "OFFLINE_OPERATOR_NORMALIZED_EVIDENCE_CONSENSUS_ONLY",
        "status": "NEEDS_REVIEW" if conflict else result.status,
        "receipts_reviewed": len(receipts),
        "operation_claims": operations,
        "full_enumeration_claims": complete_scan_claims,
        "consistency": "CONFLICT" if conflict else (
            "CONSISTENT_CLAIM_ONLY" if claimed_complete else "INCOMPLETE"),
        "item_results": [
            {"requirement_index": i, "state": item.state.value,
             "reference_count": len(item.evidence)}
            for i, item in enumerate(findings, 1)
        ] if not conflict else [
            {"requirement_index": i, "state": "NOT_CHECKED", "reference_count": 0}
            for i in range(1, len(first["required_paths"]) + 1)
        ],
        "raw_paths_references_and_contents_returned": False,
        "operator_claims_independently_verified": False,
        "registered_expert_invocation_verified": False,
        "real_nas_verified": False,
        "official_creator_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only G87 normalized multi-read check; NOT real NAS")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = args.input
        if (path.is_symlink() or path.parent.is_symlink()
                or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_FILE_BYTES):
            raise IntakeRefused("Unsupported input file")
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object, parse_constant=_nonfinite,
        )
        report = evaluate_multi_read(data)
        print(json.dumps(report, sort_keys=True, ensure_ascii=False))
        return 0 if report["consistency"] != "CONFLICT" else 2
    except (IntakeRefused, ValueError, OSError, UnicodeError, RecursionError):
        print(json.dumps({
            "status": "G87_MULTI_READ_REFUSED",
            "real_nas_verified": False, "release_gate": "HOLD",
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
