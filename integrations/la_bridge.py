"""UGREEN bridge to an explicitly supplied, separately installed LA interface.

This adapter does not execute workflows, read NAS files, or vendor HAE code.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .ecosystem_contract import preflight_request

_RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


class LABridgeUnavailable(RuntimeError):
    """The LA interface is missing or incompatible."""


def _block_if_unapproved(request: Mapping[str, Any]) -> dict[str, Any] | None:
    decision = preflight_request(request)
    if not decision.allowed:
        return {"allowed": False, "state": decision.state, "reason": decision.reason}
    return None


def preflight_la(request: Mapping[str, Any], plan: object, la_api: object | None, *,
                 sovia_assess: object | None = None,
                 sovia_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run one LA preflight; optionally review its redacted metadata with SOVIA."""
    blocked = _block_if_unapproved(request)
    if blocked is not None:
        return blocked
    method = getattr(la_api, "preflight", None)
    if not callable(method):
        raise LABridgeUnavailable("LA preflight unavailable")
    result = method(plan)
    if not isinstance(result, dict):
        raise LABridgeUnavailable("unexpected LA preflight result")
    if result.get("scope") != "synthetic-local-only" or result.get("executes_workflow") is not False:
        raise LABridgeUnavailable("unsupported LA scope")
    if result.get("source_version") not in ("azent.ir.v0", "axflow.ir.v0"):
        raise LABridgeUnavailable("unsupported LA plan version")
    count = result.get("step_count")
    if type(count) is not int or not 0 <= count <= 32:
        raise LABridgeUnavailable("invalid LA step count")
    trigger = result.get("trigger_type")
    if trigger not in ("manual", "interval"):
        raise LABridgeUnavailable("unsupported LA trigger")
    response = {
        "allowed": True, "state": "PLAN_PREFLIGHT_ONLY",
        "preview": {
            "source_version": result["source_version"],
            "trigger_type": trigger,
            "step_count": count,
            "requires_write_approval": result.get("requires_write_approval") is True,
            "requires_input_root": result.get("requires_input_root") is True,
        },
    }
    if sovia_assess is not None or sovia_policy is not None:
        from .sovia_bridge import assess_la_preview
        response["sovia"] = assess_la_preview(
            request, result, sovia_policy, sovia_assess
        )
    return response


def read_la_audit(request: Mapping[str, Any], run_id: str, la_api: object | None) -> dict[str, Any]:
    """Return audit counts only, never event contents or approval details."""
    blocked = _block_if_unapproved(request)
    if blocked is not None:
        return blocked
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        raise ValueError("invalid run identifier")
    method = getattr(la_api, "audit", None)
    if not callable(method):
        raise LABridgeUnavailable("LA audit unavailable")
    result = method(run_id)
    if not isinstance(result, dict) or result.get("run_id") != run_id:
        raise LABridgeUnavailable("unexpected LA audit result")
    events, approvals = result.get("events"), result.get("approval_receipts")
    if not isinstance(events, list) or not isinstance(approvals, list):
        raise LABridgeUnavailable("LA audit contract mismatch")
    return {
        "allowed": True, "state": "METADATA_ONLY",
        "audit": {"run_id": run_id, "event_count": len(events), "approval_count": len(approvals)},
    }


def inspect_la_capabilities(
    request: Mapping[str, Any], la_api: object | None
) -> dict[str, Any]:
    """Fail closed when a local LA engine is mistaken for a NAS Expert.

    An approved local synthetic plan preview does not imply that LA can
    access UGREEN NAS files or that a Uliya Expert is registered.
    """
    blocked = _block_if_unapproved(request)
    if blocked is not None:
        return blocked
    method = getattr(la_api, "capabilities", None)
    if not callable(method):
        raise LABridgeUnavailable("LA capabilities unavailable")
    result = method()
    if not isinstance(result, dict):
        raise LABridgeUnavailable("invalid LA capabilities")
    if result.get("api_version") != "azent.api.v0":
        raise LABridgeUnavailable("unsupported LA interface version")
    if result.get("scope") != "synthetic-local-only":
        raise LABridgeUnavailable("unsupported LA execution scope")
    if result.get("external_connectors") != []:
        raise LABridgeUnavailable("external connector state requires separate review")
    operations = result.get("implemented_operations")
    if not isinstance(operations, list) or not all(isinstance(op, str) for op in operations):
        raise LABridgeUnavailable("unverifiable LA operations")
    return {
        "allowed": True,
        "state": "LOCAL_PLAN_ONLY",
        "api_version": "azent.api.v0",
        "can_preflight_local_plan": True,
        "can_read_nas": False,
        "can_delegate_uliya_experts": False,
        "nas_state": "NOT_CHECKED",
    }
