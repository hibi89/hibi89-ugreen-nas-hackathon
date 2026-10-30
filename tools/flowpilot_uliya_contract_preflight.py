"""G95: pinned official catalog identifiers -> NO-EXECUTE Expert trial preflight.

Bounded public-kit catalog inspection only; does not construct guessed SDK
payloads, parse native responses, contact NAS or attest registered Experts.
The privately chosen owner paths and instructions are never returned.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inspect_official_sdk import UnsafePackage, download_public_official_zip
from sdk_parameter_matrix import matrix
from sdk_semantic_index import EXPECTED_SHA256
from flowpilot_multi_read_review import _read_bounded_json
from flowpilot_agent_result_intake import IntakeRefused
from flowpilot.planner import State, draft_plan

SCHEMA = "flowpilot-official-trial-preflight-v1"
CLI = "ug-filesystem"
ACTIONS = ("ls", "find", "stat")
REQUEST_KEYS = {
    "schema", "operation", "goal", "authorized_root", "required_paths",
    "metadata_approved", "unknown_processing_accepted",
}


class TrialPreflightRefused(ValueError):
    """Static refusal without exposing owner source data."""


def pinned_catalog_contract(archive: bytes, *, expected_sha: str = EXPECTED_SHA256) -> dict:
    """Extract strictly selected identifier metadata, not execution signatures."""
    info = matrix(archive, expected_sha)
    rows = [row for row in info["actions"] if row["cli"] == CLI
            and row["action"] in ACTIONS]
    if len(rows) != len(ACTIONS) or {row["action"] for row in rows} != set(ACTIONS):
        raise TrialPreflightRefused("Selected public catalog interface incomplete")
    shaped = []
    for name in ACTIONS:
        row = next(a for a in rows if a["action"] == name)
        parameters = row["parameters"]
        identifiers = [p["name"] for p in parameters]
        if len(identifiers) != len(set(identifiers)):
            raise TrialPreflightRefused("Ambiguous official parameter identifiers")
        shaped.append({
            "operation": CLI + " " + name,
            "catalog_agent_label_not_registration_proof": row["agent_label"],
            "parameter_identifiers_only": [
                {"name": p["name"], "type": p["type"],
                 "required": p["required"], "repeatable": p["repeatable"]}
                for p in parameters
            ],
            "effect_metadata_shape_only": row["effect"],
            "approval_metadata_shape_only": row["approval"],
            "permissions_metadata_shape_only": row["permissions"],
        })
    return {
        "schema": "flowpilot-pinned-catalog-read-contract-v1",
        "source_evidence": "PINNED_FIRST_PARTY_PUBLIC_CATALOG_ONLY",
        "archive_sha256": info["sha256"],
        "operations": shaped,
        "execution_argument_binding_verified": False,
        "native_result_schema_verified": False,
        "registered_expert_verified": False,
        "effective_nas_permissions_verified": False,
        "real_nas_verified": False,
        "public_catalog_contents_republished": False,
        "release_gate": "HOLD",
    }


def preflight_trial(archive: bytes, request: Any,
                    *, expected_sha: str = EXPECTED_SHA256) -> dict:
    """Validate owner scope and catalog; produce no runnable command or payload."""
    if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
        raise TrialPreflightRefused("Unexpected trial request structure")
    if request["schema"] != SCHEMA or request["operation"] not in {
        CLI + " " + a for a in ACTIONS
    }:
        raise TrialPreflightRefused("Unrecognized read-only trial action")
    goal = request["goal"]
    root = request["authorized_root"]
    paths = request["required_paths"]
    if (not isinstance(goal, str) or not 0 < len(goal.strip()) <= 2048
            or not isinstance(root, str) or not 0 < len(root) <= 1024
            or not isinstance(paths, list) or not 1 <= len(paths) <= 100
            or any(not isinstance(p, str) or len(p) > 256 for p in paths)
            or type(request["metadata_approved"]) is not bool
            or type(request["unknown_processing_accepted"]) is not bool):
        raise TrialPreflightRefused("Invalid bounded scope or consent flags")
    # Validate all paths even if the actual goal is blocked or unknown.
    try:
        draft_plan("check required files", root, paths,
                   metadata_approved=False, unknown_processing_accepted=False)
        plan = draft_plan(goal, root, paths,
                          metadata_approved=request["metadata_approved"],
                          unknown_processing_accepted=request["unknown_processing_accepted"])
    except (ValueError, TypeError) as exc:
        raise TrialPreflightRefused("Invalid scope or read-only goal") from exc
    catalog = pinned_catalog_contract(archive, expected_sha=expected_sha)
    row = next((a for a in catalog["operations"]
                if a["operation"] == request["operation"]), None)
    if row is None:
        raise TrialPreflightRefused("Official selected catalog action missing")
    return {
        "schema": SCHEMA,
        "mode": "PINNED_CATALOG_AND_OWNER_SCOPE_OFFLINE_ONLY",
        "catalog_archive_sha256": catalog["archive_sha256"],
        "selected_catalog_action": row["operation"],
        "catalog_parameter_identifiers_only": row["parameter_identifiers_only"],
        "owner_checklist_count": len(paths),
        "planner_status": plan.state.value,
        "status": ("BLOCKED" if plan.state is State.BLOCKED
                   else "WAITING_USER" if plan.state is State.WAITING_USER
                   else "WAITING_APPROVAL" if plan.state is State.WAITING_APPROVAL
                   else "AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA"),
        "execution_argument_binding_verified": False,
        "native_result_schema_verified": False,
        "registered_expert_verified": False,
        "effective_nas_permissions_verified": False,
        "real_nas_verified": False,
        "external_call_performed": False,
        "execution_payload_generated": False,
        "raw_owner_paths_or_contents_returned": False,
        "official_creator_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pinned public Uliya interface preflight; never invoke NAS.")
    parser.add_argument("--official-url", required=True)
    parser.add_argument("--request", type=Path, help="Private local owner-scoped JSON; do not commit")
    args = parser.parse_args(argv)
    try:
        # No owner input is ever sent to the public download URL.
        blob = download_public_official_zip(args.official_url)
        result = (preflight_trial(blob, _read_bounded_json(args.request))
                  if args.request is not None else pinned_catalog_contract(blob))
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0
    except (UnsafePackage, TrialPreflightRefused, IntakeRefused, OSError,
            ValueError, TypeError, UnicodeError, RecursionError, KeyError, StopIteration):
        print(json.dumps({
            "status": "G95_CATALOG_PREFLIGHT_REFUSED",
            "real_nas_verified": False,
            "release_gate": "HOLD",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
