"""G63: sequential owner-consented LOCAL metadata flow. Not NAS or Uliya."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from flowpilot_owner_local_audit import inspect_owner_folder, OwnerAuditError

MAX_STEPS = 8
MAX_TOTAL_FILES = 100
MAX_RECIPE_BYTES = 16384

class WorkflowRefused(ValueError):
    """Do not echo private filenames or paths."""

def run_workflow(root: Path, recipe: Any, *, metadata_consent: bool = False) -> dict:
    if type(metadata_consent) is not bool:
        raise WorkflowRefused("Invalid consent")
    if not isinstance(recipe, dict) or set(recipe) != {"schema", "steps"}:
        raise WorkflowRefused("Invalid recipe")
    if recipe["schema"] != "flowpilot-local-readonly-v1":
        raise WorkflowRefused("Invalid schema")
    steps = recipe["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise WorkflowRefused("Invalid number of steps")
    prepared = []
    total = set()
    # Preflight all steps before ANY owner-folder access, even when approved.
    for s in steps:
        if not isinstance(s, dict) or set(s) not in (
                {"goal", "required"}, {"goal", "required", "candidates"}):
            raise WorkflowRefused("Unexpected fields")
        required = s["required"]
        candidates = s.get("candidates", {})
        if not isinstance(required, list) or not isinstance(candidates, dict):
            raise WorkflowRefused("Invalid checklist")
        try:
            check = inspect_owner_folder(root, required,
                version_candidates=candidates, goal=s["goal"], metadata_consent=False)
        except (OwnerAuditError, TypeError, ValueError) as exc:
            raise WorkflowRefused("Unsafe checklist") from exc
        if check["status"] != "WAITING_APPROVAL":
            raise WorkflowRefused("Not an approved read-only goal")
        total.update(required)
        for items in candidates.values():
            total.update(items)
        if len(total) > MAX_TOTAL_FILES:
            raise WorkflowRefused("Too many files")
        prepared.append((s["goal"], required, candidates))
    answer = {
        "mode": "CONSENTED_LOCAL_MULTI_STEP_NOT_NAS",
        "status": "NEEDS_REVIEW" if metadata_consent else "WAITING_APPROVAL",
        "planned_steps": len(prepared), "executed_steps": 0, "steps": [],
        "owner_folder_contents_opened": False, "raw_paths_returned": False,
        "nas_verified": False, "uliya_agent_invoked": False,
        "creator_invoked": False, "devpost_submitted": False,
        "release_gate": "HOLD"
    }
    if not metadata_consent:
        return answer
    for index, (goal, required, candidates) in enumerate(prepared, 1):
        try:
            row = inspect_owner_folder(root, required,
                version_candidates=candidates, goal=goal, metadata_consent=True)
            step = {"index": index, "status": row["status"], "items": row["items"],
                    "inspected_local_metadata": row["inspected_local_metadata"]}
        except (OwnerAuditError, OSError, ValueError, TypeError):
            step = {"index": index, "status": "NOT_CHECKED", "items": [],
                    "inspected_local_metadata": False}
        answer["steps"].append(step)
        answer["executed_steps"] = index
        if step["status"] in {"BLOCKED", "NOT_CHECKED", "WAITING_USER", "WAITING_APPROVAL"}:
            answer["status"] = "BLOCKED"
            break
        # Subsequent steps may depend on the previous evidence. The G64 recipe
        # does not encode independent dependency edges, so fail closed rather
        # than read later owner files after an unresolved version or unsafe item.
        # All PRESENT observations remain allowed to advance the local workflow.
        item_states = {item.get("state") for item in step["items"]
                       if isinstance(item, dict)}
        if item_states & {"VERSION_REVIEW", "NOT_CHECKED"}:
            answer["status"] = "NEEDS_REVIEW"
            break
    return answer

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LOCAL read-only checks; NOT UGREEN NAS")
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--recipe", required=True, type=Path)
    ap.add_argument("--approve-local-metadata", action="store_true")
    args = ap.parse_args(argv)
    try:
        path = args.recipe
        if (path.is_symlink() or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_RECIPE_BYTES):
            raise WorkflowRefused("Unsafe recipe file")
        spec = json.loads(path.read_text(encoding="utf-8"))
        result = run_workflow(args.root, spec, metadata_consent=args.approve_local_metadata)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["status"] == "BLOCKED" else 0
    except (WorkflowRefused, OSError, UnicodeError, TypeError, ValueError):
        print(json.dumps({"status": "WORKFLOW_REFUSED", "release_gate": "HOLD"}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
