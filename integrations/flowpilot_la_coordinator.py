"""Safe UGREEN goal preview + LA v0 plan preflight composition.

Only combines existing preview-only interfaces. Never accesses owner folders,
executes LA, dispatches NAS agents or turns a synthetic plan into NAS evidence.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .la_bridge import preflight_la


class FlowPilotPreviewError(RuntimeError):
    """Preview contract is missing or unsafe."""


def compose_previews(
    goal: str,
    *,
    root: Path | None,
    required: list[str] | None,
    candidates: dict[str, list[str]] | None,
    la_plan: object,
    owner_request: Mapping[str, Any],
    flowpilot_preview: Callable[..., dict[str, Any]],
    la_api: object | None,
) -> dict[str, Any]:
    """Return a bounded decision summary with zero filesystem operations.

    The caller injects the existing `tools.flowpilot_goal_preview.process_goal`
    and an authorized external LAExecutor class; no HAE source is imported.
    """
    if not callable(flowpilot_preview):
        raise FlowPilotPreviewError("FlowPilot preview provider unavailable")
    preview = flowpilot_preview(
        goal,
        root=root,
        required=required,
        candidates=candidates,
        metadata_consent=False,
    )
    if not isinstance(preview, dict):
        raise FlowPilotPreviewError("invalid FlowPilot preview response")
    if preview.get("status") not in ("WAITING_USER", "WAITING_APPROVAL"):
        raise FlowPilotPreviewError("FlowPilot preview unexpectedly executed")
    if preview.get("executed_steps") != 0:
        raise FlowPilotPreviewError("FlowPilot preview reports execution")
    for key in ("owner_folder_metadata_accessed", "file_contents_opened", "registered_uliya_expert_invoked", "nas_verified"):
        if preview.get(key) is not False:
            raise FlowPilotPreviewError("FlowPilot preview unsafe or incomplete")
    step_count = preview.get("planned_steps")
    if type(step_count) is not int or not 1 <= step_count <= 3:
        raise FlowPilotPreviewError("invalid FlowPilot plan size")
    missing = preview.get("missing_inputs")
    if not isinstance(missing, list) or not all(isinstance(x, str) for x in missing):
        raise FlowPilotPreviewError("invalid missing-input summary")
    # Only expose known slot labels; do not echo folder names or file paths.
    allowed_slots = {"local_root", "required_relative_paths", "version_candidate_mapping"}
    if any(x not in allowed_slots for x in missing):
        raise FlowPilotPreviewError("unknown or potentially sensitive input label")
    result: dict[str, Any] = {
        "status": preview["status"],
        "flowpilot": {"planned_steps": step_count, "missing_inputs": list(missing)},
        "la": {"state": "NOT_CHECKED"},
        "nas_state": "NOT_CHECKED",
        "owner_folder_metadata_accessed": False,
        "la_workflow_executed": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }
    if preview["status"] == "WAITING_USER":
        return result
    # LA's preflight is metadata-only and must reject unsupported versions;
    # local write execution is deliberately not invoked.
    result["la"] = preflight_la(owner_request, la_plan, la_api)
    return result
