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


def preflight_la(request: Mapping[str, Any], plan: object, la_api: object | None) -> dict[str, Any]:
    """Only side-effect-free plan metadata may cross this boundary."""
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
    return {
        "allowed": True, "state": "PLAN_PREFLIGHT_ONLY",
        "preview": {
            "source_version": result["source_version"],
            "trigger_type": trigger,
            "step_count": count,
            "requires_write_approval": result.get("requires_write_approval") is True,
            "requires_input_root": result.get("requires_input_root") is True,
        },
    }


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
