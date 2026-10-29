"""Bounded multi-intent FlowPilot goal -> genuine LA/SOVIA synthetic execution.

The goal interpreter is the existing allowlist-only UGREEN parser. It does NOT
read owner folders, call Uliya or NAS, implement file-agent operations, or
create a general natural-language-to-workflow compiler. The only persisted
values are fixed synthetic per-intent NOT_CHECKED markers.

An operator must first receive the preflight SHA, then provide that exact SHA
to opt into disposable SQLite writes. SOVIA is advisory, never authorization.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

from .approval_scope import INTENT_LABELS
from .bounded_goal_compiler import compile_synthetic_goal_plan
from .flowpilot_la_coordinator import compose_previews
from .la_bridge import read_la_audit
from tools.flowpilot_ecosystem_showcase import process_goal

RUN_ID = "flowpilot_compiled_synthetic"
POLICY = {
    "schema_version": "1.0",
    "policy": {
        "allowed_tools": ["la_literal", "la_sqlite_put"],
        "approved_destinations": [],
        "sensitive_targets": [],
    },
}


class BoundedGoalExecutionRefused(ValueError):
    """Opaque, non-disclosing refusal of unsafe or unsupported synthetic flow."""


def run_bounded_compiled_goal(
    goal: str,
    la_executor_type: object,
    sovia_assess: object,
    *,
    required: list[str],
    candidates: dict[str, list[str]] | None = None,
    approve_plan_sha256: str | None = None,
) -> dict[str, Any]:
    """Preview 1-3 allowlisted intents or run one exact SHA-approved synthetic plan.

    All generated SQLite ledgers are created inside a disposable temp root.
    The caller's requested paths may influence the approval SHA but are never
    read or persisted; reports contain only safe counters and digest values.
    """
    if not callable(la_executor_type) or not callable(sovia_assess):
        raise BoundedGoalExecutionRefused("INJECTED_ENGINES_REQUIRED")
    if (approve_plan_sha256 is not None
            and (type(approve_plan_sha256) is not str
                 or len(approve_plan_sha256) != 64
                 or any(c not in "0123456789abcdef" for c in approve_plan_sha256))):
        raise BoundedGoalExecutionRefused("INVALID_APPROVAL_SHA256")

    with tempfile.TemporaryDirectory(prefix="flowpilot-compiled-") as temporary:
        root = Path(temporary)
        try:
            preview = process_goal(
                goal, root=root, required=required, candidates=candidates,
                metadata_consent=False,
            )
        except (ValueError, TypeError) as exc:
            raise BoundedGoalExecutionRefused("FLOWPILOT_GOAL_REFUSED") from exc
        steps = preview.get("plan")
        if type(steps) is not list or not 1 <= len(steps) <= 3:
            raise BoundedGoalExecutionRefused("FLOWPILOT_PREVIEW_MISSING_STEPS")
        # The requester can opt into reviewing only a synthetic preview.
        # Consent flags are scoped to a fake, empty temp folder; they are
        # NEVER forwarded as user approval to access actual owner directories.
        intents = [
            INTENT_LABELS.get(step.get("read_only_action"))
            if type(step) is dict else None
            for step in steps
        ]
        if not all(type(s) is str for s in intents):
            raise BoundedGoalExecutionRefused("UNSUPPORTED_INTENT")
        request = {
            "intent": intents[0],
            "authorized_intents": intents if len(intents) > 1 else None,
            "folder": str(root),
            "required_paths": required,
            "owner_approved_metadata": True,
            "runtime_permissions_verified": True,
            "processing_location_accepted": True,
        }
        if candidates is not None:
            request["version_candidates"] = candidates

        try:
            compiled = compile_synthetic_goal_plan(
                goal, preview, root=root, required=required, candidates=candidates,
                owner_request=request,
            )
        except (ValueError, TypeError) as exc:
            raise BoundedGoalExecutionRefused("FLOWPILOT_APPROVAL_SCOPE_REFUSED") from exc
        plan = compiled["plan"]
        try:
            coordinated = compose_previews(
                goal, root=root, required=required, candidates=candidates,
                la_plan=plan, owner_request=request,
                flowpilot_preview=process_goal, la_api=la_executor_type,
                sovia_assess=sovia_assess, sovia_policy=POLICY,
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            raise BoundedGoalExecutionRefused("LA_SOVIA_PREFLIGHT_REFUSED") from exc
        la = coordinated.get("la", {})
        advisory = la.get("sovia", {})
        expected = len(compiled["intent_codes"])
        if (coordinated.get("status") != "WAITING_APPROVAL"
                or coordinated.get("owner_folder_metadata_accessed") is not False
                or coordinated.get("la_workflow_executed") is not False
                or la.get("state") != "PLAN_PREFLIGHT_ONLY"
                or la.get("preview", {}).get("source_version") != "azent.ir.v0"
                or la.get("preview", {}).get("step_count") != len(plan["steps"])
                or la.get("preview", {}).get("requires_write_approval") is not True
                or la.get("preview", {}).get("requires_input_root") is not False
                or advisory.get("state") != "ADVISORY_ONLY"
                or advisory.get("finding_count") != expected
                or advisory.get("execution_authorized") is not False):
            raise BoundedGoalExecutionRefused("LA_SOVIA_SYNTHETIC_PREFLIGHT_NOT_PROVEN")

        runtime_path, business_path = root / "runtime.sqlite", root / "business.sqlite"
        if runtime_path.exists() or business_path.exists():
            raise BoundedGoalExecutionRefused("PREFLIGHT_CREATED_DATABASE")
        outcome = {
            "status": "WAITING_PLAN_SHA256_APPROVAL",
            "mode": "BOUNDED_MULTI_INTENT_SYNTHETIC_LOCAL_SQLITE",
            "intents": list(compiled["intent_codes"]),
            "intent_count": expected,
            "la_step_count": compiled["planned_steps"],
            "planned_synthetic_writes": compiled["planned_synthetic_writes"],
            "required_item_count": compiled["required_item_count"],
            "version_candidate_count": compiled["candidate_count"],
            "plan_sha256": compiled["plan_sha256"],
            "approve_plan_sha256": compiled["approval_sha256"],
            "synthetic_write_rows": 0,
            "approval_receipts": 0,
            "duplicate_replay_writes": 0,
            "sovia_advisory": "REVIEW_ONLY",
            "sovia_finding_count": expected,
            "la_execution_verified": False,
            "owner_folder_metadata_accessed": False,
            "registered_uliya_expert_invoked": False,
            "customer_data_used": False,
            "actual_nas_verified": False,
            "devpost_submitted": False,
            "release_gate": "HOLD",
        }
        if approve_plan_sha256 is None:
            return outcome
        if approve_plan_sha256 != compiled["approval_sha256"]:
            raise BoundedGoalExecutionRefused("APPROVAL_SCOPE_SHA256_MISMATCH")

        executor = la_executor_type(runtime_path, business_path)
        executor.execute(plan, RUN_ID, approve_writes=True)
        if executor.status(RUN_ID).get("status") != "completed":
            raise BoundedGoalExecutionRefused("LA_RUN_NOT_COMPLETED")
        verify = getattr(executor, "verify_receipts", None)
        if not callable(verify):
            raise BoundedGoalExecutionRefused("RECEIPT_VERIFIER_REQUIRED")
        first_receipt = verify(plan, RUN_ID)
        if (type(first_receipt) is not dict
                or first_receipt.get("run_id") != RUN_ID
                or first_receipt.get("verified") is not True):
            raise BoundedGoalExecutionRefused("RECEIPT_VERIFICATION_FAILED")
        audit = read_la_audit(request, RUN_ID, executor)
        if (audit.get("state") != "METADATA_ONLY"
                or audit.get("audit", {}).get("approval_count") != 1):
            raise BoundedGoalExecutionRefused("SYNTHETIC_APPROVAL_NOT_AUDITED")

        def inspect_rows() -> list[tuple[str, str]]:
            if not business_path.is_file():
                raise BoundedGoalExecutionRefused("SYNTHETIC_BUSINESS_LEDGER_MISSING")
            with closing(sqlite3.connect(
                business_path.as_uri() + "?mode=ro", uri=True,
            )) as con:
                if con.execute("PRAGMA quick_check(1)").fetchone() != ("ok",):
                    raise BoundedGoalExecutionRefused("SYNTHETIC_BUSINESS_LEDGER_CORRUPT")
                return con.execute(
                    "SELECT step_id,payload_json FROM records WHERE run_id=? ORDER BY step_id",
                    (RUN_ID,),
                ).fetchall()

        original_rows = inspect_rows()
        if len(original_rows) != expected:
            raise BoundedGoalExecutionRefused("SYNTHETIC_WRITE_COUNT_MISMATCH")
        for index, (step_id, payload) in enumerate(original_rows, 1):
            if (step_id != "store" + str(index)
                    or json.loads(payload) != {
                        "intent": compiled["intent_codes"][index - 1],
                        "state": "NOT_CHECKED", "scope": "SYNTHETIC_ONLY",
                    }):
                raise BoundedGoalExecutionRefused("SYNTHETIC_RECEIPT_PAYLOAD_MISMATCH")

        executor.execute(plan, RUN_ID, approve_writes=True)
        if (inspect_rows() != original_rows
                or executor.status(RUN_ID).get("status") != "completed"
                or verify(plan, RUN_ID).get("verified") is not True
                or read_la_audit(request, RUN_ID, executor).get("audit", {}).get(
                    "approval_count") != 1):
            raise BoundedGoalExecutionRefused("SYNTHETIC_REPLAY_NOT_IDEMPOTENT")
        outcome.update({
            "status": "PASS",
            "la_execution_verified": True,
            "synthetic_write_rows": expected,
            "approval_receipts": 1,
            "duplicate_replay_writes": 0,
            "ephemeral_sqlite_deleted_after_run": True,
        })
        return outcome
