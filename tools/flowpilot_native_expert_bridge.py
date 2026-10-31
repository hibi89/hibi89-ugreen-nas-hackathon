"""G120: safe NL -> pinned Uliya catalog -> normalized file-agent review.

No vendor network calls, registered Expert invocation, native API payloads,
or real NAS proof. The official catalog is interface metadata, not a runtime
contract; operator-normalized reports are untrusted and never release a run.
"""
from __future__ import annotations

import argparse
import json

from flowpilot_task_compiler import compile_goal
from flowpilot_uliya_contract_preflight import (
    SCHEMA as TRIAL_SCHEMA, preflight_trial, TrialPreflightRefused,
)
from flowpilot_multi_read_intake import (
    evaluate_multi_read, IntakeRefused, SCHEMA as RECEIPTS_SCHEMA,
)
from sdk_semantic_index import EXPECTED_SHA256
from inspect_official_sdk import UnsafePackage, download_public_official_zip

BRIDGE_SCHEMA = "flowpilot-g120-expert-route-v1"
FILE_TEMPLATE = "required_file_metadata_v1"
FILE_ACTION = "ug-filesystem find"
READ_ACTIONS = frozenset(("ug-filesystem ls", "ug-filesystem find", "ug-filesystem stat"))


def _base() -> dict:
    return {
        "schema": BRIDGE_SCHEMA, "release_gate": "HOLD",
        "external_call_performed": False,
        "native_command_generated": False,
        "registered_expert_invocation_verified": False,
        "effective_permissions_verified": False,
        "native_response_schema_verified": False,
        "nas_verified": False,
        "production_applied": False,
        "devpost_submitted": False,
    }


def route_native_review(
    archive: bytes, *, goal: str, authorized_root: str,
    required_paths: list[str], metadata_approved: bool = False,
    unknown_processing_accepted: bool = False,
    normalized_receipts: dict | None = None,
    expected_sha: str = EXPECTED_SHA256,
) -> dict:
    """Bridge one read-only goal without inventing a native SDK signature.

    Pinned official kit bytes are validated by existing G95 code. Custom SHA
    overrides are only test-fixture evidence and NEVER establish official kit
    provenance or live agent availability.
    """
    out = _base()
    plan = compile_goal(goal)
    if plan.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return {**out, "status": "BLOCKED_UNSUPPORTED_NATURAL_LANGUAGE_GOAL"}
    if plan["template"] != FILE_TEMPLATE:
        return {**out, "status": "BLOCKED_NO_VERIFIED_NATIVE_CSV_EXECUTION",
                "local_template": plan["template"],
                "fallback": "G115_G119_LOCAL_SYNTHETIC_FIXTURE_ONLY"}
    if type(metadata_approved) is not bool or type(unknown_processing_accepted) is not bool:
        raise TrialPreflightRefused("Invalid metadata consent")
    # Deliberately map the bounded G115 synonymous phrase to the G95 planner
    # canonical read-only goal, not a guessed native Uliya instruction.
    request = {
        "schema": TRIAL_SCHEMA,
        "operation": FILE_ACTION,
        "goal": "check required files",
        "authorized_root": authorized_root,
        "required_paths": required_paths,
        "metadata_approved": metadata_approved,
        "unknown_processing_accepted": unknown_processing_accepted,
    }
    pre = preflight_trial(archive, request, expected_sha=expected_sha)
    result = {
        **out, "status": pre["status"],
        "source": ("PINNED_PUBLIC_KIT_METADATA_ONLY" if expected_sha == EXPECTED_SHA256
                   else "SYNTHETIC_CATALOG_TEST_ONLY"),
        "catalog_sha256": pre["catalog_archive_sha256"],
        "local_template": FILE_TEMPLATE, "chosen_action_label": FILE_ACTION,
        "declared_parameter_identifiers_only": pre["catalog_parameter_identifiers_only"],
        "owner_checklist_count": pre["owner_checklist_count"],
        "steps": [
            {"index": 1, "task": "CONFIRM_EXACT_OWNER_METADATA_SCOPE",
             "requires_consent": True},
            {"index": 2, "task": "CHECK_REGISTERED_FILE_EXPERT_SIGNATURE_AND_PERMISSION",
             "known_catalog_action": FILE_ACTION,
             "runtime_signature_confirmed": False},
            {"index": 3, "task": "ONLY_IF_AUTHORIZED_COLLECT_COMPLETE_FILE_ENUMERATION",
             "native_execution_performed": False},
            {"index": 4, "task": "RECONCILE_NORMALIZED_RECEIPTS_NO_RAW_PATH_OUTPUT",
             "proof_level": "UNTRUSTED_OPERATOR_CLAIMS_ONLY"},
            {"index": 5, "task": "USER_REVIEW_AND_SEPARATE_LIVE_APPROVAL",
             "production_applied": False},
        ],
        "pending_requirements": [
            "REGISTERED_EXPERT_RUNTIME_ATTESTATION",
            "NATIVE_ARGUMENT_BINDING",
            "NATIVE_RESPONSE_SCHEMA",
            "EFFECTIVE_NAS_PERMISSION",
            "REDACTED_LIVE_NAS_READBACK",
        ],
    }
    if normalized_receipts is None:
        return result
    if pre["status"] != "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA":
        return {**result, "receipt_status": "RECEIPTS_NOT_EVALUATED_NO_APPROVAL"}
    if (type(normalized_receipts) is not dict
            or set(normalized_receipts) != {"schema", "receipts"}
            or normalized_receipts.get("schema") != RECEIPTS_SCHEMA
            or not isinstance(normalized_receipts.get("receipts"), list)
            or not 1 <= len(normalized_receipts["receipts"]) <= 8):
        raise IntakeRefused("Unexpected normalized receipt bundle")
    for index, row in enumerate(normalized_receipts["receipts"]):
        if (type(row) is not dict or row.get("schema") != "flowpilot-agent-observation-v1"
                or row.get("goal") != request["goal"]
                or row.get("authorized_root") != authorized_root
                or row.get("required_paths") != required_paths
                or row.get("metadata_approved") is not True
                or row.get("unknown_processing_accepted") is not True
                or row.get("version_candidates") not in (None, {})):
            raise IntakeRefused("Different authorized receipt context")
        agent = row.get("file_agent_report")
        if (type(agent) is not dict
                or agent.get("operation") not in READ_ACTIONS
                or (index == 0 and agent.get("operation") != FILE_ACTION)):
            raise IntakeRefused("Unsupported or reordered registered action")
    review = evaluate_multi_read(normalized_receipts)
    # Existing G87 review already rejects forged references, incomplete scans,
    # conflicting stats and unapproved scope. Never upgrade its proof tier.
    result.update({
        "receipt_status": "REVIEW_PREPARED_UNVERIFIED",
        "claimed_consistency": review["consistency"],
        "claimed_workflow_status": review["status"],
        "receipts_reviewed": review["receipts_reviewed"],
        "item_results": review["item_results"],
        "operator_claims_independently_verified": False,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="G120 Uliya no-execute metadata bridge")
    p.add_argument("--official-url", required=True,
                   help="Public pinned official kit URL; no owner data is sent")
    p.add_argument("--goal", required=True)
    p.add_argument("--authorized-root", required=True)
    p.add_argument("--required", action="append", required=True)
    p.add_argument("--approve-local-metadata", action="store_true")
    p.add_argument("--accept-unknown-processing", action="store_true")
    args = p.parse_args(argv)
    try:
        binary = download_public_official_zip(args.official_url)
        result = route_native_review(
            binary, goal=args.goal, authorized_root=args.authorized_root,
            required_paths=args.required,
            metadata_approved=args.approve_local_metadata,
            unknown_processing_accepted=args.accept_unknown_processing,
        )
    except (UnsafePackage, TrialPreflightRefused, IntakeRefused,
            ValueError, TypeError, OSError, KeyError):
        result = {**_base(), "status": "OFFLINE_EXPERT_BRIDGE_REFUSED"}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] in ("WAITING_APPROVAL",
                                     "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA") else 2


if __name__ == "__main__":
    raise SystemExit(main())
