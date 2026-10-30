"""G81 optional UGREEN FlowPilot -> existing HAE -> real LA local HTTP bridge.

Development-only synthetic fixtures; never included in the official Uliya Skill
ZIP and never calls a remote NAS, SaaS, or public URL. No HAE server is started
or modified by this adapter. The operator must already have an explicitly
configured local synthetic HAE server with the Lightning Azent backend.

The HAE server owns preview validity, approved CSV snapshot and SQLite writes.
This bridge deliberately never retries POST /api/run: a dropped response after
a write makes the outcome UNKNOWN, not a safe automatic replay.
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
from typing import Any
from urllib.parse import urlencode

MAX_TASK_CHARS = 512
MAX_RESPONSE_BYTES = 32768
MAX_REQUEST_BYTES = 8192
APPROVAL = "APPROVE_HAE_LA_SYNTHETIC_WRITE"
_PREVIEW = re.compile(r"^[0-9a-f]{32}$")
_RUN_ID = re.compile(r"^Gui[0-9a-fA-F]{12}$")
_CSV = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,126}\.csv$", re.I)


class BridgeRefused(ValueError):
    """Invalid or unsafe owner-supplied bridge contract."""


class BridgeUnavailable(RuntimeError):
    """HAE service, response or expected capability was not established."""


class WriteOutcomeUnknown(RuntimeError):
    """Run may have committed; do NOT automatically retry."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate response key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> None:
    raise ValueError("nonfinite JSON number")


def _request(port: int, method: str, route: str, payload: dict | None = None,
             *, may_write: bool = False) -> tuple[int, dict]:
    """Only literal-IP loopback, exact fixed endpoints, JSON, bounded replies."""
    if (method, route.split("?", 1)[0]) not in {
        ("GET", "/api/health"), ("POST", "/api/preview"), ("POST", "/api/run"),
        ("GET", "/api/status"), ("GET", "/api/la-audit"),
    }:
        raise BridgeRefused("Unsupported HAE API route")
    raw = None if payload is None else json.dumps(
        payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    if raw is not None and len(raw) > MAX_REQUEST_BYTES:
        raise BridgeRefused("Request exceeds HAE limit")
    origin = f"http://127.0.0.1:{port}"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        headers = {"Host": f"127.0.0.1:{port}", "Accept": "application/json"}
        if raw is not None:
            headers.update({"Content-Type": "application/json", "Origin": origin})
        conn.request(method, route, body=raw, headers=headers)
        response = conn.getresponse()
        if response.status in {301, 302, 303, 307, 308}:
            raise BridgeUnavailable("HAE redirect refused")
        if not response.getheader("Content-Type", "").lower().startswith("application/json"):
            raise BridgeUnavailable("HAE did not return JSON")
        data = response.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES:
            raise BridgeUnavailable("HAE response exceeds limit")
        try:
            result = json.loads(
                data.decode("utf-8"), object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except (UnicodeError, ValueError, RecursionError) as exc:
            raise BridgeUnavailable("Invalid HAE JSON response") from exc
        if not isinstance(result, dict):
            raise BridgeUnavailable("HAE response must be a JSON object")
        return response.status, result
    except BridgeUnavailable as exc:
        # A committed write might have been followed by a redirect, wrong
        # content-type, malformed/duplicate JSON or an oversized reply.
        # These are NOT permission to retry the POST /api/run.
        if may_write:
            raise WriteOutcomeUnknown("Run reply invalid after possible write") from exc
        raise
    except (OSError, http.client.HTTPException, TimeoutError) as exc:
        if may_write:
            raise WriteOutcomeUnknown("Run outcome unknown after loopback transport failure") from exc
        raise BridgeUnavailable("HAE loopback request unavailable") from exc
    finally:
        conn.close()


def _validate_inputs(task: str, csv_path: str, port: int,
                     approval: str | None, preview_id: str | None,
                     confirm_synthetic: bool, pending_run_id: str | None = None) -> None:
    if confirm_synthetic is not True:
        raise BridgeRefused("Explicit synthetic-only fixture confirmation required")
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise BridgeRefused("Explicit HAE high loopback port required")
    if (not isinstance(task, str) or not task.strip()
            or len(task) > MAX_TASK_CHARS or any(ord(c) < 32 for c in task)):
        raise BridgeRefused("Unsupported HAE task")
    if (not isinstance(csv_path, str) or not _CSV.fullmatch(csv_path)
            or ".." in csv_path or "/" in csv_path or "\\" in csv_path):
        raise BridgeRefused("A simple synthetic CSV basename is required")
    if pending_run_id is not None and (
        not isinstance(pending_run_id, str) or not _RUN_ID.fullmatch(pending_run_id)
    ):
        raise BridgeRefused("Invalid HAE-issued pending run ID")
    if approval is None:
        if preview_id is not None or pending_run_id is not None:
            raise BridgeRefused("Execution tokens require separate approval")
    elif approval == APPROVAL:
        if not isinstance(preview_id, str) or not _PREVIEW.fullmatch(preview_id):
            raise BridgeRefused("Run requires a valid HAE-issued preview token")
    else:
        if preview_id is not None and (not isinstance(preview_id, str)
                                       or not _PREVIEW.fullmatch(preview_id)):
            raise BridgeRefused("Invalid preview token")



def reconcile_run(port: int, run_id: str, *, confirm_synthetic: bool = False) -> dict:
    """Read-only HAE status + LA audit: NEVER a write or a synthetic E2E claim.

    The evidence is only what the local HAE service reports. It does not
    inspect business SQLite or certify a native Uliya/NAS execution.
    """
    if (confirm_synthetic is not True or isinstance(port, bool)
            or not isinstance(port, int) or not 1024 <= port <= 65535
            or not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id)):
        raise BridgeRefused("Read-only recovery requires synthetic approval, port and run ID")
    unknown = {"status": "EXECUTION_OUTCOME_UNKNOWN", "run_id": run_id,
               "executed": False, "do_not_retry_automatically": True,
               "actual_la_execution_verified": False, "real_nas_verified": False}
    try:
        code, health = _request(port, "GET", "/api/health")
        backend = health.get("engine_backend")
        if (code != 200 or health.get("service") != "HAE"
                or health.get("ready") is not True or not isinstance(backend, dict)
                or backend.get("name") != "Lightning Azent"
                or backend.get("api_version") != "azent.api.v0"):
            return unknown
        status_code, status = _request(
            port, "GET", "/api/status?" + urlencode({"run_id": run_id}))
        audit_code, audit = _request(
            port, "GET", "/api/la-audit?" + urlencode({"run_id": run_id}))
    except BridgeUnavailable:
        return unknown
    if (status_code != 200 or status.get("run_id") != run_id
            or status.get("status") != "completed"
            or audit_code != 200 or audit.get("run_id") != run_id
            or type(audit.get("approval_count")) is not int
            or audit["approval_count"] < 1
            or type(audit.get("total_events")) is not int
            or audit["total_events"] < 2):
        return unknown
    return {
        "status": "HAE_LA_AUDIT_RECONCILED",
        "run_id": run_id, "executed": True,
        "do_not_retry_automatically": True,
        "hae_http_connected": True,
        "hae_reported_completed": True,
        "audit_events": audit["total_events"],
        "approval_receipts": audit["approval_count"],
        "actual_la_execution_verified": False,
        "verification_scope": "READ_ONLY_HAE_REPORTED_STATUS_AND_LA_AUDIT",
        "real_nas_verified": False,
        "actual_uliya_agent_invoked": False,
    }


def _uncertain_after_write(port: int, pending_run_id: str | None) -> dict:
    """One read-only recovery attempt if HAE issued an exact run ID.

    Missing/old HAE binary => unknown. Do not discover/replay a write.
    """
    if pending_run_id is not None:
        return reconcile_run(port, pending_run_id, confirm_synthetic=True)
    return {
        "status": "EXECUTION_OUTCOME_UNKNOWN", "executed": False,
        "do_not_retry_automatically": True,
        "recovery": "REQUIRES_HAE_PREVIEW_RUN_ID",
        "actual_la_execution_verified": False, "real_nas_verified": False,
    }


def run_bridge(task: str, *, csv_path: str, port: int,
               approval: str | None = None, preview_id: str | None = None,
               confirm_synthetic: bool = False,
               pending_run_id: str | None = None) -> dict:
    """Run one *separately approved* HAE localhost synthetic CSV->LA->SQLite task.

    First call without approval produces a preview only. The caller must
    consciously supply the exact token + explicit APPROVAL on a second call.
    The bridge reports audit and readback from the live server; it never
    masquerades as native Uliya/NAS or independently inspects HAE's database.
    """
    _validate_inputs(task, csv_path, port, approval, preview_id,
                     confirm_synthetic, pending_run_id)
    if approval not in (None, APPROVAL):
        return {
            "status": "DECLINED", "executed": False, "hae_http_connected": False,
            "actual_la_execution_verified": False, "real_nas_verified": False,
        }
    try:
        code, health = _request(port, "GET", "/api/health")
        backend = health.get("engine_backend")
        if (code != 200 or health.get("service") != "HAE"
                or health.get("ready") is not True
                or not isinstance(backend, dict)
                or backend.get("name") != "Lightning Azent"
                or backend.get("api_version") != "azent.api.v0"):
            return {
                "status": "BLOCKED_HAE_LA_BACKEND_NOT_READY", "executed": False,
                "hae_http_connected": code == 200,
                "actual_la_execution_verified": False, "real_nas_verified": False,
            }
        if approval is None:
            code, data = _request(port, "POST", "/api/preview",
                                  {"task": task, "csv_path": csv_path})
            token = data.get("preview_id")
            proposed_run_id = data.get("pending_run_id")  # optional on older HAE .pyz
            info = data.get("input")
            engine = data.get("engine_backend")
            if (code != 200 or data.get("validated") is not True
                    or data.get("requires_approval") is not True
                    or not isinstance(token, str) or not _PREVIEW.fullmatch(token)
                    or not isinstance(engine, dict)
                    or engine.get("name") != "Lightning Azent"
                    or not isinstance(info, dict)
                    or (proposed_run_id is not None
                        and (not isinstance(proposed_run_id, str)
                             or not _RUN_ID.fullmatch(proposed_run_id)))):
                return {
                    "status": "BLOCKED_HAE_PREVIEW_REJECTED", "executed": False,
                    "hae_http_connected": True, "actual_la_execution_verified": False,
                    "real_nas_verified": False,
                }
            return {
                "status": "WAITING_HAE_WRITE_APPROVAL", "executed": False,
                "hae_http_connected": True,
                "preview_id": token, "workflow": data.get("workflow"),
                "pending_run_id": proposed_run_id,
                "input": {k: info[k] for k in ("row_count", "column_count", "size_bytes")
                          if isinstance(info.get(k), int) and not isinstance(info[k], bool)},
                "backend": "Lightning Azent",
                "approval_phrase": APPROVAL,
                "actual_la_execution_verified": False, "real_nas_verified": False,
            }
        # Exactly one write request. NEVER automatically retry if it may have committed.
        code, data = _request(
            port, "POST", "/api/run",
            {"task": task, "csv_path": csv_path, "preview_id": preview_id,
             "approve_writes": True,
             **({"pending_run_id": pending_run_id} if pending_run_id is not None else {})},
            may_write=True,
        )
        if code != 200:
            # Only a specific, known HAE rejection happens before any write.
            # Other HTTP 4xx/5xx can follow a committed business SQLite write.
            if (code == 409 and data.get("error") in {
                    "preview expired or no longer matches the request",
                    "pending run ID differs from approved preview",
            }):
                return {
                    "status": "BLOCKED_HAE_EXECUTION_REJECTED", "executed": False,
                    "hae_http_connected": True, "http_status": code,
                    "do_not_retry_automatically": True,
                    "actual_la_execution_verified": False, "real_nas_verified": False,
                }
            return _uncertain_after_write(port, pending_run_id)
        run_id, outcome, result, engine = (
            data.get("run_id"), data.get("status"), data.get("result"),
            data.get("backend"),
        )
        if (not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id)
                or (pending_run_id is not None and run_id != pending_run_id)):
            return _uncertain_after_write(port, pending_run_id)
        if (not isinstance(outcome, dict) or outcome.get("status") != "completed"
                or not isinstance(result, dict)
                or type(result.get("imported_rows")) is not int
                or result["imported_rows"] < 0 or not isinstance(engine, dict)
                or engine.get("name") != "Lightning Azent"):
            return {
                "status": "EXECUTION_NOT_CONFIRMED", "run_id": run_id,
                "executed": False, "do_not_retry_automatically": True,
                "actual_la_execution_verified": False, "real_nas_verified": False,
            }
        # After a confirmed write, *read-only* status/audit fetch may fail. This
        # does NOT mean the write failed and MUST NEVER trigger a write retry.
        try:
            status_code, saved = _request(
                port, "GET", "/api/status?" + urlencode({"run_id": run_id}))
            audit_code, audit = _request(
                port, "GET", "/api/la-audit?" + urlencode({"run_id": run_id}))
        except BridgeUnavailable:
            return {
                "status": "EXECUTED_AUDIT_NOT_VERIFIED", "run_id": run_id,
                "executed": True, "do_not_retry_automatically": True,
                "actual_la_execution_verified": False, "real_nas_verified": False,
            }
        if (status_code != 200 or saved.get("run_id") != run_id
                or saved.get("status") != "completed"
                or audit_code != 200 or audit.get("run_id") != run_id
                or type(audit.get("approval_count")) is not int
                or audit["approval_count"] < 1
                or type(audit.get("total_events")) is not int
                or audit["total_events"] < 2):
            return {
                "status": "EXECUTED_AUDIT_NOT_VERIFIED", "run_id": run_id,
                "executed": True, "do_not_retry_automatically": True,
                "actual_la_execution_verified": False, "real_nas_verified": False,
            }
        return {
            "status": "HAE_LA_SQLITE_AUDIT_CONFIRMED",
            "run_id": run_id, "executed": True,
            "imported_rows": result["imported_rows"],
            "audit_events": audit["total_events"],
            "approval_receipts": audit["approval_count"],
            "hae_http_connected": True,
            "hae_http_audit_verified": True,
            "hae_reported_la_execution": True,
            "actual_la_execution_verified": False,
            "verification_scope": "HAE_REPORTED_HTTP_AND_AUDIT_ONLY_NO_INDEPENDENT_SQLITE",
            "real_nas_verified": False,
            "actual_uliya_agent_invoked": False,
            "third_party_services_verified": False,
        }
    except WriteOutcomeUnknown:
        return _uncertain_after_write(port, pending_run_id)
    except BridgeUnavailable:
        return {
            "status": "BLOCKED_HAE_UNAVAILABLE", "executed": False,
            "actual_la_execution_verified": False, "real_nas_verified": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FlowPilot local HAE+LA bridge; synthetic-only")
    parser.add_argument("--task")
    parser.add_argument("--csv")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--confirm-synthetic", action="store_true")
    parser.add_argument("--approval")
    parser.add_argument("--preview-id")
    parser.add_argument("--pending-run-id", help="HAE run ID returned with preview, if supported")
    parser.add_argument("--reconcile-run-id", help="Read-only audit recovery (no POST)")
    args = parser.parse_args(argv)
    try:
        if args.reconcile_run_id is not None:
            if any(v is not None for v in (
                args.task, args.csv, args.approval, args.preview_id, args.pending_run_id
            )):
                raise BridgeRefused("Reconcile-only mode cannot request execution")
            result = reconcile_run(
                args.port, args.reconcile_run_id,
                confirm_synthetic=args.confirm_synthetic)
        else:
            if args.task is None or args.csv is None:
                raise BridgeRefused("Task and synthetic CSV required for preview/run")
            result = run_bridge(
                args.task, csv_path=args.csv, port=args.port,
                approval=args.approval, preview_id=args.preview_id,
                confirm_synthetic=args.confirm_synthetic,
                pending_run_id=args.pending_run_id,
            )
    except (BridgeRefused, ValueError, TypeError):
        result = {"status": "BRIDGE_REFUSED", "executed": False,
                  "real_nas_verified": False}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result["status"].startswith(("BRIDGE_", "BLOCKED_", "EXECUTION_")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
