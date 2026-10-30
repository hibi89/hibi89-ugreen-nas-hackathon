"""Consented owner-selected LOCAL folder checklist, not NAS/Uliya.

Never reads file contents, enumerates directories, or returns raw owner paths.
Explicit preview then single-use approval permits read-only lstat metadata.
"""
from __future__ import annotations

from pathlib import Path
import secrets
import sys
from threading import Lock

HERE = Path(__file__).resolve().parents[1]
for folder in (HERE, HERE / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from flowpilot_goal_preview import process_goal
from flowpilot_local_workflow import WorkflowRefused

CONSENT = "APPROVE_LOCAL_METADATA_LSTAT"
COUNT_KEYS = ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
SAFE_ACTIONS = frozenset({
    "check required files", "check handoff deliverables", "compare versions",
})
SAFE_STAGE_STATES = frozenset({"NEEDS_REVIEW", "BLOCKED", "NOT_CHECKED"})
SAFE_ITEM_STATES = frozenset(COUNT_KEYS)


def _safe_stage_results(raw: object, executed: int) -> list[dict]:
    """Emit only bounded step/item indexes and states; no path-like strings."""
    if type(raw) is not list or len(raw) != executed:
        raise OwnerWorkbenchRefused("INVALID_LOCAL_STAGE_EVIDENCE")
    stages = []
    for i, row in enumerate(raw, 1):
        if (type(row) is not dict or type(row.get("index")) is not int
                or row["index"] != i
                or row.get("status") not in SAFE_STAGE_STATES
                or type(row.get("inspected_local_metadata")) is not bool
                or type(row.get("items")) is not list
                or len(row["items"]) > 30):
            raise OwnerWorkbenchRefused("INVALID_LOCAL_STAGE_EVIDENCE")
        items = []
        for k, item in enumerate(row["items"], 1):
            if (type(item) is not dict or type(item.get("index")) is not int
                    or item["index"] != k or item.get("state") not in SAFE_ITEM_STATES
                    or type(item.get("local_reference_count")) is not int
                    or not 0 <= item["local_reference_count"] <= 100):
                raise OwnerWorkbenchRefused("INVALID_LOCAL_STAGE_EVIDENCE")
            items.append({"item_index": k, "state": item["state"]})
        stages.append({
            "step_index": i, "status": row["status"],
            "metadata_inspected": row["inspected_local_metadata"],
            "items": items,
        })
    return stages



class OwnerWorkbenchRefused(ValueError):
    """Deliberately opaque; never embed user inputs or errors."""


def _input_scope(data: object) -> tuple[str, Path, list[str], dict[str, list[str]] | None]:
    if type(data) is not dict or set(data) != {
        "goal", "root", "required", "candidates", "confirm_local_only"
    } or data["confirm_local_only"] is not True:
        raise OwnerWorkbenchRefused("LOCAL_SCOPE_CONFIRMATION_REQUIRED")
    goal, root, required, candidates = (
        data["goal"], data["root"], data["required"], data["candidates"]
    )
    if (type(goal) is not str or not 0 < len(goal) <= 512
            or type(root) is not str or not 0 < len(root) <= 2048
            or root != root.strip()
            or type(required) is not list or not 1 <= len(required) <= 30
            or any(type(x) is not str or not 0 < len(x) <= 180 for x in required)):
        raise OwnerWorkbenchRefused("INVALID_BOUNDED_LOCAL_SCOPE")
    if candidates is not None and (
        type(candidates) is not dict or len(candidates) > 30 or
        any(type(k) is not str or type(v) is not list or
            not 1 <= len(v) <= 12 or
            any(type(x) is not str or len(x) > 180 for x in v)
            for k, v in candidates.items())
    ):
        raise OwnerWorkbenchRefused("INVALID_VERSION_CANDIDATES")
    # No Path.stat/lstat/resolve here. The existing FlowPilot preflight
    # checks absolute non-UNC roots and validates restricted relative names.
    return goal, Path(root), list(required), (
        {k: list(v) for k, v in candidates.items()} if candidates is not None else None
    )


class OwnerWorkbench:
    def __init__(self):
        self._lock = Lock()
        self._pending: tuple[str, Path, list[str], dict | None, str, tuple[str, ...]] | None = None
        self._reading = False

    def preview(self, request: object) -> dict:
        goal, root, required, candidates = _input_scope(request)
        with self._lock:
            if self._reading:
                raise OwnerWorkbenchRefused("LOCAL_CHECK_ALREADY_RUNNING")
            self._pending = None
            try:
                result = process_goal(goal, root=root, required=required,
                                      candidates=candidates, metadata_consent=False)
            except (WorkflowRefused, ValueError, TypeError, OSError):
                raise OwnerWorkbenchRefused("LOCAL_PREVIEW_REFUSED") from None
            if (result.get("status") != "WAITING_APPROVAL"
                    or type(result.get("planned_steps")) is not int
                    or not 1 <= result["planned_steps"] <= 3
                    or result.get("executed_steps") != 0
                    or result.get("owner_folder_metadata_accessed") is not False
                    or result.get("file_contents_opened") is not False
                    or result.get("raw_paths_returned") is not False
                    or result.get("nas_verified") is not False
                    or result.get("release_gate") != "HOLD"):
                raise OwnerWorkbenchRefused("UNSAFE_LOCAL_PREVIEW")
            planned = result.get("plan")
            if (type(planned) is not list or len(planned) != result["planned_steps"]
                    or any(type(p) is not dict
                           or type(p.get("index")) is not int
                           or p["index"] != i
                           or p.get("read_only_action") not in SAFE_ACTIONS
                           for i, p in enumerate(planned, 1))):
                raise OwnerWorkbenchRefused("UNVERIFIED_LOCAL_PLAN")
            token = secrets.token_hex(24)
            self._pending = (
                goal, root, required, candidates, token,
                tuple(p["read_only_action"] for p in planned),
            )
            return {
                "status": "WAITING_EXPLICIT_LOCAL_METADATA_APPROVAL",
                "approval_token": token,
                "planned_steps": result["planned_steps"],
                "planned_actions": [
                    {"step_index": p["index"], "action": p["read_only_action"]}
                    for p in planned
                ],
                "required_file_count": len(required),
                "version_candidate_count": sum(len(v) for v in (candidates or {}).values()),
                "metadata_accessed": False, "file_contents_opened": False,
                "actual_nas_verified": False, "release_gate": "HOLD",
            }

    def execute(self, token: object, consent: object) -> dict:
        with self._lock:
            if self._reading or self._pending is None:
                raise OwnerWorkbenchRefused("NO_PENDING_LOCAL_APPROVAL")
            goal, root, required, candidates, expected, actions = self._pending
            if (type(token) is not str or type(consent) is not str
                    or not secrets.compare_digest(token, expected)
                    or consent != CONSENT):
                raise OwnerWorkbenchRefused("LOCAL_APPROVAL_REFUSED")
            self._pending = None
            self._reading = True
        try:
            result = process_goal(goal, root=root, required=required,
                                  candidates=candidates, metadata_consent=True)
            counts = result.get("finding_counts")
            if (result.get("status") not in ("NEEDS_REVIEW", "BLOCKED")
                    or type(result.get("executed_steps")) is not int
                    or not 1 <= result["executed_steps"] <= 3
                    or type(counts) is not dict
                    or any(type(counts.get(k)) is not int
                           or not 0 <= counts[k] <= 300 for k in COUNT_KEYS)
                    or result.get("file_contents_opened") is not False
                    or result.get("raw_paths_returned") is not False
                    or result.get("nas_verified") is not False
                    or result.get("registered_uliya_expert_invoked") is not False
                    or result.get("release_gate") != "HOLD"):
                raise OwnerWorkbenchRefused("LOCAL_METADATA_RESULT_UNVERIFIED")
            stage_results = _safe_stage_results(
                result.get("observed"), result["executed_steps"]
            )
            if (len(actions) != result["planned_steps"]
                    or any(action not in SAFE_ACTIONS for action in actions)):
                raise OwnerWorkbenchRefused("INVALID_APPROVED_ACTIONS")
            for i, stage in enumerate(stage_results):
                stage["action"] = actions[i]
            if (type(result.get("review_item_count")) is not int
                    or not 0 <= result["review_item_count"] <= 300):
                raise OwnerWorkbenchRefused("INVALID_LOCAL_REVIEW_EVIDENCE")
            return {
                "status": result["status"],
                "mode": "EXPLICITLY_CONSENTED_LOCAL_LSTAT_ONLY",
                "planned_steps": result["planned_steps"],
                "executed_steps": result["executed_steps"],
                "finding_counts": {k: counts[k] for k in COUNT_KEYS},
                "stage_results": stage_results,
                "review_item_count": result["review_item_count"],
                "file_contents_opened": False, "raw_paths_returned": False,
                "actual_nas_verified": False,
                "registered_uliya_expert_invoked": False,
                "release_gate": "HOLD",
            }
        except (WorkflowRefused, ValueError, TypeError, OSError):
            raise OwnerWorkbenchRefused("LOCAL_METADATA_INSPECTION_REFUSED") from None
        finally:
            with self._lock:
                self._reading = False
