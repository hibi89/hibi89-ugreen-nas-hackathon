"""G96: offline G95 pinned catalog -> G87/G88 normalized evidence review.
This does not invoke Uliya, NAS, SDK commands, or create native payloads.
Operator-normalized receipts are untrusted even if marked approved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inspect_official_sdk import UnsafePackage, download_public_official_zip
from sdk_semantic_index import EXPECTED_SHA256
from flowpilot_uliya_contract_preflight import preflight_trial, TrialPreflightRefused
from flowpilot_multi_read_review import build_review, _read_bounded_json
from flowpilot_multi_read_intake import IntakeRefused, SCHEMA as MULTI_SCHEMA

SCHEMA = "flowpilot-trial-rehearsal-v1"


class RehearsalRefused(ValueError):
    """Never attach owner paths or raw source values to exceptions."""


def rehearse(archive: bytes, payload: object, *, expected_sha: str = EXPECTED_SHA256) -> dict:
    if (not isinstance(payload, dict)
            or set(payload) != {"schema", "request", "normalized_receipts"}
            or payload["schema"] != SCHEMA):
        raise RehearsalRefused("Invalid rehearsal envelope")
    request, bundle = payload["request"], payload["normalized_receipts"]
    if (not isinstance(bundle, dict)
            or set(bundle) != {"schema", "receipts"}
            or bundle["schema"] != MULTI_SCHEMA
            or not isinstance(bundle["receipts"], list)
            or len(bundle["receipts"]) > 8):
        raise RehearsalRefused("Invalid bounded receipt set")

    preflight = preflight_trial(archive, request, expected_sha=expected_sha)
    answer = {
        "schema": SCHEMA, "mode": "OFFLINE_REHEARSAL_NOT_NAS",
        "status": preflight["status"],
        "catalog_sha256": preflight["catalog_archive_sha256"],
        "selected_operation": preflight["selected_catalog_action"],
        "review_queue": [], "review_item_count": 0, "receipt_count": 0,
        "consistency": "NOT_EVALUATED",
        "blocking_reasons": ["NO_REGISTERED_RUNTIME_PROOF"],
        "decision": "HOLD", "release_gate": "HOLD",
        "operator_claims_independently_verified": False,
        "owner_approval_granted_by_tool": False,
        "registered_expert_invocation_verified": False,
        "native_result_schema_verified": False,
        "real_nas_verified": False,
        "external_call_performed": False,
        "execution_payload_generated": False,
        "raw_paths_returned": False,
        "official_creator_verified": False,
        "devpost_submitted": False,
    }
    if preflight["status"] != "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA":
        return answer

    records = bundle["receipts"]
    if not records:
        answer["status"] = "WAITING_NORMALIZED_RECEIPTS"
        return answer
    if (not isinstance(request, dict)
            or not isinstance(records[0], dict)
            or not isinstance(records[0].get("file_agent_report"), dict)
            or records[0]["file_agent_report"].get("operation") != request["operation"]):
        raise RehearsalRefused("Requested first read operation mismatch")
    for record in records:
        if not isinstance(record, dict) or record.get("version_candidates"):
            raise RehearsalRefused("Unsupported scope expansion")
        for field in ("goal", "authorized_root", "required_paths",
                      "metadata_approved", "unknown_processing_accepted"):
            if record.get(field) != request[field]:
                raise RehearsalRefused("Owner context mismatch")

    review = build_review(bundle)
    review_status = (
        "OFFLINE_CONFLICT_HOLD" if review["consistency"] == "CONFLICT"
        else "OFFLINE_INCOMPLETE_HOLD" if review["consistency"] == "INCOMPLETE"
        else "OFFLINE_BLOCKED_HOLD" if review["source_status"] == "BLOCKED"
        else "REVIEW_PREPARED_UNVERIFIED"
    )
    answer.update({
        "status": review_status, "source_status": review["source_status"],
        "consistency": review["consistency"],
        "review_queue": review["review_queue"],
        "review_item_count": review["review_item_count"],
        "finding_counts": review["finding_counts"],
        "receipt_count": review["receipt_count"],
        "blocking_reasons": review["blocking_reasons"],
    })
    return answer


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline trial rehearsal, NOT NAS")
    parser.add_argument("--official-url", required=True)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        data = _read_bounded_json(args.input)
        public_zip = download_public_official_zip(args.official_url)
        result = rehearse(public_zip, data)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2 if result["consistency"] == "CONFLICT" else 0
    except (UnsafePackage, TrialPreflightRefused, RehearsalRefused,
            IntakeRefused, OSError, UnicodeError, ValueError,
            TypeError, KeyError, RecursionError):
        print(json.dumps({"status": "G96_REHEARSAL_REFUSED",
                          "real_nas_verified": False,
                          "release_gate": "HOLD"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
