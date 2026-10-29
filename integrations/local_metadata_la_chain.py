"""Consented LOCAL lstat observations -> FlowPilot -> LA/SOVIA -> synthetic receipts.

This bridge reuses FlowPilot's existing exact-relative-path metadata inspector.
No directory enumeration, content reads, NAS, Uliya Agent or external network.
The optional LA execution stores only per-intent state COUNTS, never source
paths/names, file bytes or document answers, in disposable local SQLite.

Metadata access requires distinct explicit consent. SQLite requires a second
exact fingerprint approval. Missing/unverified observations block LA writes.
These fingerprints bind values, NOT participant identity or file immutability.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from pathlib import Path
from typing import Any

from .approval_scope import INTENT_LABELS
from .bounded_goal_compiler import canonical_hash
from .flowpilot_la_coordinator import compose_previews
from .la_bridge import read_la_audit
from tools.flowpilot_ecosystem_showcase import process_goal

STATES = ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
RUN_ID = "flowpilot_local_metadata_proof"
POLICY = {
    "schema_version": "1.0",
    "policy": {
        "allowed_tools": ["la_literal", "la_sqlite_put"],
        "approved_destinations": [],
        "sensitive_targets": [],
    },
}


class LocalObservationRefused(ValueError):
    """An unsupported or insufficiently verified local-only workflow."""


def _base(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "mode": "OWNER_CONSENTED_LOCAL_LSTAT_TO_SYNTHETIC_LA_NOT_NAS",
        "local_state_counts": {state: 0 for state in STATES},
        "local_inspection_performed": False,
        "la_execution_verified": False,
        "approval_receipts": 0,
        "synthetic_write_rows": 0,
        "replay_duplicate_writes": 0,
        "file_contents_opened": False,
        "raw_paths_or_names_returned": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "customer_data_used": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def _checked_observations(observed: dict, expected_items: int) -> tuple[list[dict], dict, list[list[str]]]:
    """Verify complete redacted metadata receipts before any LA plan is built."""
    if (type(observed) is not dict
            or observed.get("status") not in ("NEEDS_REVIEW", "BLOCKED")
            or observed.get("owner_folder_metadata_accessed") is not True
            or observed.get("file_contents_opened") is not False
            or observed.get("raw_paths_returned") is not False
            or observed.get("nas_verified") is not False
            or observed.get("registered_uliya_expert_invoked") is not False):
        raise LocalObservationRefused("UNVERIFIED_LOCAL_METADATA")
    planned = observed.get("planned_steps")
    completed = observed.get("executed_steps")
    steps = observed.get("observed")
    if (type(planned) is not int or not 1 <= planned <= 3
            or type(completed) is not int or not 1 <= completed <= planned
            or type(steps) is not list or len(steps) != completed):
        raise LocalObservationRefused("INCOMPLETE_LOCAL_STEP_RECEIPTS")
    values: list[dict] = []
    ordered_states: list[list[str]] = []
    totals: Counter[str] = Counter()
    for index, step in enumerate(steps, 1):
        if (type(step) is not dict or step.get("index") != index
                or step.get("inspected_local_metadata") is not True
                or step.get("status") not in ("NEEDS_REVIEW", "BLOCKED")):
            raise LocalObservationRefused("UNTRUSTED_LOCAL_STEP")
        items = step.get("items")
        if type(items) is not list or len(items) != expected_items:
            raise LocalObservationRefused("INVALID_LOCAL_ITEM_COUNT")
        counts: Counter[str] = Counter()
        step_states: list[str] = []
        for item_index, item in enumerate(items, 1):
            if (type(item) is not dict
                    or set(item) != {"index", "state", "local_reference_count"}
                    or type(item["index"]) is not int
                    or item["index"] != item_index
                    or item["state"] not in STATES
                    or type(item["local_reference_count"]) is not int
                    or item["local_reference_count"] not in (0, 1)):
                raise LocalObservationRefused("UNTRUSTED_LOCAL_ITEM")
            if ((item["state"] == "PRESENT") != (item["local_reference_count"] == 1)):
                raise LocalObservationRefused("INCONSISTENT_LOCAL_REFERENCE")
            counts[item["state"]] += 1
            totals[item["state"]] += 1
            step_states.append(item["state"])
        ordered_states.append(step_states)
        values.append({state: counts[state] for state in STATES})
    return values, {state: totals[state] for state in STATES}, ordered_states


def _read_rows(business: Path) -> list[tuple[str, str]]:
    if not business.is_file():
        raise LocalObservationRefused("MISSING_SYNTHETIC_LEDGER")
    with closing(sqlite3.connect(business.as_uri() + "?mode=ro", uri=True)) as con:
        if con.execute("PRAGMA quick_check(1)").fetchone() != ("ok",):
            raise LocalObservationRefused("SYNTHETIC_LEDGER_CORRUPTED")
        return con.execute(
            "SELECT step_id, payload_json FROM records WHERE run_id=? ORDER BY step_id",
            (RUN_ID,),
        ).fetchall()


def run_local_observation_chain(
    goal: str,
    root: Path,
    required: list[str],
    la_executor_type: object,
    sovia_assess: object,
    *,
    candidates: dict[str, list[str]] | None = None,
    approve_local_metadata: bool = False,
    approve_plan_sha256: str | None = None,
) -> dict[str, Any]:
    """Preview, inspect (with consent), then optionally persist redacted states.

    Re-reading observed metadata for SHA-approval makes changed states fail
    closed. This is NOT an atomic snapshot or NAS permission guarantee.
    """
    if type(approve_local_metadata) is not bool:
        raise LocalObservationRefused("INVALID_LOCAL_METADATA_CONSENT")
    if (approve_plan_sha256 is not None and
            (type(approve_plan_sha256) is not str
             or len(approve_plan_sha256) != 64
             or any(c not in "0123456789abcdef" for c in approve_plan_sha256))):
        raise LocalObservationRefused("INVALID_PLAN_APPROVAL_HASH")
    if approve_plan_sha256 is not None and not approve_local_metadata:
        raise LocalObservationRefused("METADATA_CONSENT_REQUIRED_BEFORE_PLAN_APPROVAL")
    if not callable(la_executor_type) or not callable(sovia_assess):
        raise LocalObservationRefused("INJECTED_LOCAL_ENGINES_REQUIRED")
    if type(required) is not list or not 1 <= len(required) <= 12:
        raise LocalObservationRefused("BOUNDED_REQUIRED_ITEMS_ONLY")
    try:
        path = Path(root)
        preview = process_goal(
            goal, root=path, required=required, candidates=candidates,
            metadata_consent=False,
        )
    except (ValueError, TypeError, OSError) as exc:
        raise LocalObservationRefused("FLOWPILOT_LOCAL_PREVIEW_REFUSED") from exc
    output = _base("WAITING_LOCAL_METADATA_APPROVAL")
    if preview.get("status") == "WAITING_USER":
        output["status"] = "WAITING_USER"
        output["missing_slots"] = preview.get("missing_inputs", [])
        return output
    if (preview.get("status") != "WAITING_APPROVAL"
            or preview.get("executed_steps") != 0
            or preview.get("owner_folder_metadata_accessed") is not False
            or preview.get("file_contents_opened") is not False
            or preview.get("registered_uliya_expert_invoked") is not False
            or preview.get("nas_verified") is not False):
        raise LocalObservationRefused("UNSAFE_FLOWPILOT_LOCAL_PREVIEW")
    steps = preview.get("plan")
    if type(steps) is not list or not 1 <= len(steps) <= 3:
        raise LocalObservationRefused("INVALID_PREVIEW_INTENT_COUNT")
    intents = []
    for index, entry in enumerate(steps, 1):
        if (type(entry) is not dict or set(entry) != {"index", "read_only_action"}
                or type(entry["index"]) is not int or entry["index"] != index):
            raise LocalObservationRefused("INVALID_PREVIEW_INTENT")
        action = INTENT_LABELS.get(entry["read_only_action"])
        if action is None or action in intents:
            raise LocalObservationRefused("INVALID_OR_DUPLICATE_PREVIEW_INTENT")
        intents.append(action)
    output["intent_count"] = len(intents)
    output["required_item_count"] = len(required)
    if not approve_local_metadata:
        return output

    # The only local metadata access is here, after explicit user consent.
    try:
        inspected = process_goal(
            goal, root=path, required=required, candidates=candidates,
            metadata_consent=True,
        )
    except (ValueError, TypeError, OSError) as exc:
        raise LocalObservationRefused("CONSENTED_LOCAL_INSPECTION_REFUSED") from exc
    per_intent, total, ordered_states = _checked_observations(inspected, len(required))
    output["local_inspection_performed"] = True
    output["local_state_counts"] = total
    if (inspected["status"] != "NEEDS_REVIEW"
            or len(per_intent) != len(intents)
            or total["MISSING"] or total["NOT_CHECKED"]):
        output["status"] = "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED"
        return output

    # Generate a bounded synthetic LA plan containing ONLY state tallies.
    # No owner filenames/paths, references, contents, prompts or raw receipts.
    safe_values = []
    ir_steps: list[dict[str, Any]] = []
    for index, (intent, counts) in enumerate(zip(intents, per_intent), 1):
        value = {"intent": intent, "state_counts": counts,
                 "scope": "LOCAL_LSTAT_SUMMARY_NOT_NAS"}
        safe_values.append(value)
        source = "state" + str(index)
        ir_steps.append({"id": source, "op": "literal", "value": value})
        ir_steps.append({"id": "store" + str(index), "op": "sqlite_put", "from": source})
    plan = {"version": "azent.ir.v0", "trigger": {"type": "manual"},
            "steps": ir_steps}
    # Scope fingerprint contains exact local path and observed per-intent
    # states but only the digest is returned. The path itself is never logged.
    scope_hash = canonical_hash({
        "schema": "ugreen-local-lstat-plan-approval.v1",
        "goal": goal, "root": str(path), "required": required,
        "candidates": candidates or {}, "ordered_states": ordered_states,
        "plan": plan,
    })
    request = {
        "intent": intents[0],
        "authorized_intents": intents if len(intents) > 1 else None,
        "folder": str(path), "required_paths": required,
        "owner_approved_metadata": True,
        "runtime_permissions_verified": True,
        "processing_location_accepted": True,
    }
    if candidates is not None:
        request["version_candidates"] = candidates
    try:
        summary = compose_previews(
            goal, root=path, required=required, candidates=candidates,
            la_plan=plan, owner_request=request, flowpilot_preview=process_goal,
            la_api=la_executor_type, sovia_assess=sovia_assess,
            sovia_policy=POLICY,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise LocalObservationRefused("LOCAL_LA_SOVIA_PREFLIGHT_REFUSED") from exc
    la, sovia = summary.get("la", {}), summary.get("la", {}).get("sovia", {})
    if (summary.get("status") != "WAITING_APPROVAL"
            or summary.get("owner_folder_metadata_accessed") is not False
            or summary.get("la_workflow_executed") is not False
            or la.get("state") != "PLAN_PREFLIGHT_ONLY"
            or la.get("preview", {}).get("step_count") != len(ir_steps)
            or la.get("preview", {}).get("requires_write_approval") is not True
            or la.get("preview", {}).get("requires_input_root") is not False
            or sovia.get("state") != "ADVISORY_ONLY"
            or sovia.get("finding_count") != len(intents)
            or sovia.get("execution_authorized") is not False):
        raise LocalObservationRefused("LOCAL_LA_SOVIA_ADVISORY_NOT_PROVEN")
    output.update({
        "status": "WAITING_EXACT_LOCAL_PLAN_APPROVAL",
        "plan_sha256": canonical_hash(plan),
        "approve_plan_sha256": scope_hash,
        "sovia_advisory": "REVIEW_ONLY",
        "sovia_finding_count": len(intents),
        "la_step_count": len(ir_steps),
    })
    if approve_plan_sha256 is None:
        return output
    if approve_plan_sha256 != scope_hash:
        raise LocalObservationRefused("LOCAL_PLAN_APPROVAL_HASH_MISMATCH")

    # Writes exclusively to private throwaway SQLite created after approval.
    with tempfile.TemporaryDirectory(prefix="ugreen-local-lstat-la-") as tmp:
        state = Path(tmp) / "runtime.sqlite"
        business = Path(tmp) / "business.sqlite"
        executor = la_executor_type(state, business)
        executor.execute(plan, RUN_ID, approve_writes=True)
        if executor.status(RUN_ID).get("status") != "completed":
            raise LocalObservationRefused("LOCAL_LA_EXECUTION_INCOMPLETE")
        checker = getattr(executor, "verify_receipts", None)
        if not callable(checker) or checker(plan, RUN_ID) != {
            "run_id": RUN_ID, "verified": True,
        }:
            raise LocalObservationRefused("LOCAL_LA_RECEIPTS_UNVERIFIED")
        audit = read_la_audit(request, RUN_ID, executor)
        if (audit.get("state") != "METADATA_ONLY"
                or audit.get("audit", {}).get("approval_count") != 1):
            raise LocalObservationRefused("LOCAL_LA_AUDIT_UNVERIFIED")
        original = _read_rows(business)
        if len(original) != len(safe_values):
            raise LocalObservationRefused("LOCAL_SYNTHETIC_ROW_COUNT_MISMATCH")
        for i, (step_id, payload) in enumerate(original, 1):
            if step_id != "store" + str(i) or json.loads(payload) != safe_values[i - 1]:
                raise LocalObservationRefused("LOCAL_SYNTHETIC_PAYLOAD_MISMATCH")
        executor.execute(plan, RUN_ID, approve_writes=True)
        if (executor.status(RUN_ID).get("status") != "completed"
                or _read_rows(business) != original
                or checker(plan, RUN_ID) != {"run_id": RUN_ID, "verified": True}
                or read_la_audit(request, RUN_ID, executor).get(
                    "audit", {}).get("approval_count") != 1):
            raise LocalObservationRefused("LOCAL_LA_REPLAY_NOT_IDEMPOTENT")
    output.update({
        "status": "PASS",
        "la_execution_verified": True,
        "approval_receipts": 1,
        "synthetic_write_rows": len(safe_values),
        "replay_duplicate_writes": 0,
        "ephemeral_sqlite_deleted_after_run": True,
    })
    return output
