"""UGREEN-specific, dependency-free read-only integration contract checks.

No private HAE/DBVORA code is embedded. No live NAS or external calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

ALLOWED_INTENTS = frozenset({"HANDOFF_AUDIT", "CHECK_REQUIRED", "REVIEW_VERSIONS", "SUMMARIZE_SELECTED"})


@dataclass(frozen=True)
class IntegrationDecision:
    allowed: bool
    state: str
    reason: str


def preflight_request(request: Mapping[str, Any]) -> IntegrationDecision:
    """Reject missing consent/scope or unsupported writes before any adapter executes."""
    if request.get("intent") not in ALLOWED_INTENTS:
        return IntegrationDecision(False, "NOT_CHECKED", "unsupported_intent")
    if request.get("write") or request.get("execute"):
        return IntegrationDecision(False, "NOT_CHECKED", "write_or_execution_not_supported")
    folder = request.get("folder")
    if not isinstance(folder, str) or not folder.strip():
        return IntegrationDecision(False, "NOT_CHECKED", "missing_exact_folder")
    required = request.get("required_paths")
    if not isinstance(required, list) or not required or any(not isinstance(p, str) or not p.strip() for p in required):
        return IntegrationDecision(False, "NOT_CHECKED", "missing_exact_checklist")
    if request.get("owner_approved_metadata") is not True:
        return IntegrationDecision(False, "NOT_CHECKED", "owner_approval_required")
    if request.get("runtime_permissions_verified") is not True:
        return IntegrationDecision(False, "NOT_CHECKED", "runtime_permissions_unverified")
    if request.get("processing_location_accepted") is not True:
        return IntegrationDecision(False, "NOT_CHECKED", "processing_location_unaccepted")
    if request.get("intent") == "SUMMARIZE_SELECTED" and request.get("owner_approved_content") is not True:
        return IntegrationDecision(False, "CONTENT_NOT_CHECKED", "separate_content_approval_required")
    return IntegrationDecision(True, "READY_FOR_ADAPTER", "preflight_only_no_runtime_proof")


def normalize_audit_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Retain metadata-only fields, never workflow payloads, secrets or file contents."""
    allowed = ("run_id", "status", "step_count", "completed_steps", "failed_steps", "plan_sha256")
    return {key: receipt[key] for key in allowed if key in receipt and type(receipt[key]) in (str, int)}
