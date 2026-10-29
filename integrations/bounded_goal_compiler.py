"""Compile bounded FlowPilot goal previews to local-only synthetic LA IR.

This is NOT a general natural-language executor and does not implement NAS
file operations. It deterministically maps up to three recognized intentions
to synthetic literal evidence placeholders and opt-in local SQLite receipts.
User paths, prompts and file names never enter the LA plan.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .approval_scope import INTENT_LABELS, require_exact_approval_scope

VERSION = "azent.ir.v0"
MAX_INTENTS = 3
MAX_REQUIRED = 100


class CompilationRefused(ValueError):
    """Invalid goal, source preview, consent or bounded synthetic plan."""


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def compile_synthetic_goal_plan(
    goal: str,
    preview: Mapping[str, Any],
    *,
    root: Path,
    required: list[str],
    candidates: dict[str, list[str]] | None,
    owner_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind all approved intent/scope slots to an immutable synthetic LA plan.

    An explicit SHA256 approval can later be checked against the returned
    approval_hash. This hash is a consistency fingerprint, not authentication.
    It excludes ephemeral local root (only a disposable temp dir is ever used).
    """
    if (type(goal) is not str or not goal.strip()
            or type(preview) is not dict
            or preview.get("status") != "WAITING_APPROVAL"
            or preview.get("executed_steps") != 0
            or preview.get("owner_folder_metadata_accessed") is not False
            or preview.get("file_contents_opened") is not False
            or preview.get("registered_uliya_expert_invoked") is not False
            or preview.get("nas_verified") is not False):
        raise CompilationRefused("UNSAFE_OR_INCOMPLETE_FLOWPILOT_PREVIEW")
    steps = preview.get("plan")
    if (type(steps) is not list or not 1 <= len(steps) <= MAX_INTENTS
            or type(preview.get("planned_steps")) is not int
            or preview["planned_steps"] != len(steps)):
        raise CompilationRefused("INVALID_PREVIEW_STEP_COUNT")
    if (type(required) is not list or not 1 <= len(required) <= MAX_REQUIRED
            or any(type(p) is not str for p in required)
            or type(owner_request) is not dict
            or owner_request.get("owner_approved_metadata") is not True
            or owner_request.get("runtime_permissions_verified") is not True
            or owner_request.get("processing_location_accepted") is not True):
        raise CompilationRefused("INCOMPLETE_SYNTHETIC_SCOPE")
    try:
        require_exact_approval_scope(
            owner_request, root=root, required=required,
            candidates=candidates, preview=preview,
        )
    except (ValueError, TypeError) as exc:
        raise CompilationRefused("EXACT_SCOPE_REFUSED") from exc
    intents = []
    for position, step in enumerate(steps, start=1):
        if (type(step) is not dict or set(step) != {"index", "read_only_action"}
                or type(step["index"]) is not int
                or step["index"] != position
                or type(step["read_only_action"]) is not str):
            raise CompilationRefused("INVALID_PREVIEW_STEP")
        code = INTENT_LABELS.get(step["read_only_action"])
        if code is None or code in intents:
            raise CompilationRefused("UNKNOWN_OR_DUPLICATE_INTENT")
        intents.append(code)

    # Only the fixed non-sensitive intent label and NOT_CHECKED marker are
    # persisted. This is never a claim that owner files were actually checked.
    ir_steps: list[dict[str, Any]] = []
    for index, code in enumerate(intents, 1):
        source = "intent" + str(index)
        ir_steps.append({
            "id": source, "op": "literal",
            "value": {"intent": code, "state": "NOT_CHECKED",
                      "scope": "SYNTHETIC_ONLY"},
        })
        ir_steps.append({
            "id": "store" + str(index), "op": "sqlite_put", "from": source,
        })
    plan: dict[str, Any] = {
        "version": VERSION, "trigger": {"type": "manual"}, "steps": ir_steps,
    }
    # Scope is bound without exposing paths or user goal. No path or goal is
    # stored in runtime SQLite; only safe placeholders appear in LA IR.
    approval_hash = canonical_hash({
        "schema": "flowpilot-synthetic-goal-approval.v1",
        "goal": goal, "required": required,
        "candidates": candidates or {},
        "intents": intents, "plan": plan,
    })
    return {
        "plan": plan,
        "intent_codes": intents,
        "approval_sha256": approval_hash,
        "plan_sha256": canonical_hash(plan),
        "planned_steps": len(ir_steps),
        "planned_synthetic_writes": len(intents),
        "required_item_count": len(required),
        "candidate_count": sum(len(v) for v in (candidates or {}).values()),
        "actual_nas_verified": False,
        "release_gate": "HOLD",
    }
