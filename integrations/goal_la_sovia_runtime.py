"""One continuous, disposable *synthetic* FlowPilot -> LA -> SOVIA run.

Unlike separate preflight and LA unit smokes, this exact fixed-fixture path
checks UGREEN's real natural-goal preview, an injected trusted LA preflight,
an injected SOVIA advisory, then the SAME LA plan's execution and redacted
receipts in a temporary local SQLite database.

This is NOT arbitrary goal-to-LA plan generation: one literal Korean goal
maps to one audited synthetic fixture. It never accesses owner file metadata,
real UGREEN NAS, Uliya Experts, network APIs, or customer content.
"""
from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

from integrations.flowpilot_la_coordinator import compose_previews
from integrations.la_bridge import read_la_audit
from tools.flowpilot_ecosystem_showcase import POLICY, WRITE_PLAN, process_goal

FIXTURE_GOAL = "필수 파일 확인"
FIXTURE_REQUIRED = ["README.md"]
FIXTURE_RUN_ID = "flowpilot_la_sovia_synthetic"
FIXTURE_WRITE_STEP_ID = "store"


class SyntheticChainRefused(ValueError):
    """A preview, consent or receipt does not satisfy the synthetic gate."""


def _result(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "chain": "REAL_UGREEN_GOAL_TO_INJECTED_LA_AND_SOVIA_SYNTHETIC_LOCAL",
        "goal_to_plan": "ONE_HARDCODED_SYNTHETIC_FIXTURE_NOT_GENERAL_COMPILER",
        "approval_scope": "EXPLICIT_SYNTHETIC_SQLITE_ONLY",
        "la_execution_verified": False,
        "sovia_advisory_reviewed": False,
        "synthetic_write_rows": 0,
        "approval_receipts": 0,
        "replay_duplicate_writes": 0,
        "owner_folder_metadata_accessed": False,
        "customer_data_used": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def run_connected_synthetic(
    la_executor_type: object,
    sovia_assess: object,
    *,
    goal: str = FIXTURE_GOAL,
    approve_synthetic_write: bool = False,
) -> dict[str, Any]:
    """Require exact goal, source-injected preflight and separate write approval.

    A false approval returns a nonexecuting preview, not a failed test.
    All execution artefacts are disposable and generated only from constants.
    """
    if goal != FIXTURE_GOAL:
        raise SyntheticChainRefused("UNSUPPORTED_SYNTHETIC_GOAL")
    if type(approve_synthetic_write) is not bool:
        raise SyntheticChainRefused("INVALID_APPROVAL_TYPE")
    if not callable(la_executor_type) or not callable(sovia_assess):
        raise SyntheticChainRefused("MISSING_LA_OR_SOVIA_INTERFACE")
    with tempfile.TemporaryDirectory(prefix="flowpilot-connected-synthetic-") as temporary:
        root = Path(temporary)
        owner_request = {
            "intent": "CHECK_REQUIRED",
            "folder": str(root),
            "required_paths": list(FIXTURE_REQUIRED),
            "owner_approved_metadata": True,
            "runtime_permissions_verified": True,
            "processing_location_accepted": True,
        }
        try:
            preflight = compose_previews(
                goal, root=root, required=list(FIXTURE_REQUIRED),
                candidates=None, la_plan=WRITE_PLAN, owner_request=owner_request,
                flowpilot_preview=process_goal, la_api=la_executor_type,
                sovia_assess=sovia_assess, sovia_policy=POLICY,
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            raise SyntheticChainRefused("CONNECTED_PREFLIGHT_REFUSED") from exc
        la = preflight.get("la", {})
        advisory = la.get("sovia", {})
        if (preflight.get("status") != "WAITING_APPROVAL"
                or preflight.get("flowpilot", {}).get("planned_steps") != 1
                or preflight.get("owner_folder_metadata_accessed") is not False
                or preflight.get("la_workflow_executed") is not False
                or la.get("state") != "PLAN_PREFLIGHT_ONLY"
                or la.get("preview", {}).get("step_count") != 2
                or la.get("preview", {}).get("requires_write_approval") is not True
                or la.get("preview", {}).get("trigger_type") != "manual"
                or advisory.get("state") != "ADVISORY_ONLY"
                or advisory.get("finding_count") != 1
                or advisory.get("execution_authorized") is not False):
            raise SyntheticChainRefused("CONNECTED_PREFLIGHT_NOT_PROVEN")
        if (root / "runtime.sqlite").exists() or (root / "business.sqlite").exists():
            raise SyntheticChainRefused("PREVIEW_CREATED_DATABASE")
        result = _result("WAITING_EXPLICIT_SYNTHETIC_WRITE_APPROVAL")
        result["sovia_advisory_reviewed"] = True
        if not approve_synthetic_write:
            # No executor constructed, no SQLite created, no write attempted.
            return result

        executor = la_executor_type(root / "runtime.sqlite", root / "business.sqlite")
        executor.execute(WRITE_PLAN, FIXTURE_RUN_ID, approve_writes=True)
        if executor.status(FIXTURE_RUN_ID).get("status") != "completed":
            raise SyntheticChainRefused("LA_NOT_COMPLETED")
        audit = read_la_audit(owner_request, FIXTURE_RUN_ID, executor)
        if (audit.get("state") != "METADATA_ONLY"
                or audit.get("audit", {}).get("approval_count") != 1
                or type(audit.get("audit", {}).get("event_count")) is not int
                or audit["audit"]["event_count"] < 1):
            raise SyntheticChainRefused("APPROVAL_AUDIT_NOT_PROVEN")
        verify = getattr(executor, "verify_receipts", None)
        if not callable(verify):
            raise SyntheticChainRefused("RECEIPT_INTEGRITY_CHECK_UNAVAILABLE")
        receipt = verify(WRITE_PLAN, FIXTURE_RUN_ID)
        if (type(receipt) is not dict or receipt.get("verified") is not True
                or receipt.get("run_id") != FIXTURE_RUN_ID):
            raise SyntheticChainRefused("RECEIPT_INTEGRITY_CHECK_FAILED")
        ledger = root / "business.sqlite"
        if not ledger.is_file():
            raise SyntheticChainRefused("SYNTHETIC_LEDGER_MISSING")

        def count_rows() -> int:
            # Read-only URI: do not silently initialize a missing file.
            with closing(sqlite3.connect(ledger.as_uri() + "?mode=ro", uri=True)) as con:
                if con.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
                    raise SyntheticChainRefused("SYNTHETIC_LEDGER_CORRUPT")
                return con.execute(
                    "SELECT COUNT(*) FROM records WHERE run_id=? AND step_id=?",
                    (FIXTURE_RUN_ID, FIXTURE_WRITE_STEP_ID)
                ).fetchone()[0]

        before_replay = count_rows()
        if before_replay != 1:
            raise SyntheticChainRefused("APPROVED_WRITE_NOT_EXACTLY_ONE")
        executor.execute(WRITE_PLAN, FIXTURE_RUN_ID, approve_writes=True)
        after_replay = count_rows()
        repeat_audit = read_la_audit(owner_request, FIXTURE_RUN_ID, executor)
        if (after_replay != 1
                or repeat_audit.get("audit", {}).get("approval_count") != 1
                or executor.status(FIXTURE_RUN_ID).get("status") != "completed"
                or executor.verify_receipts(WRITE_PLAN, FIXTURE_RUN_ID).get("verified") is not True):
            raise SyntheticChainRefused("REPLAY_NOT_IDEMPOTENT")
        result.update({
            "status": "PASS",
            "la_execution_verified": True,
            "synthetic_write_rows": after_replay,
            "approval_receipts": 1,
            "replay_duplicate_writes": after_replay - before_replay,
        })
        return result
