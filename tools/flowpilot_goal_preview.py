"""G68: bounded conversational goal -> inspectable, consent-gated LOCAL workflow.

Development-only; not inside UGREEN contest Skill ZIP. No generic NLU claims.
No root directory access before all required inputs and explicit metadata approval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from flowpilot_local_workflow import run_workflow, WorkflowRefused
from flowpilot_owner_local_audit import _valid_relative, OwnerAuditError

MAX_GOAL_LENGTH = 512
INTENTS = {
    "인계 자료 점검": "check handoff deliverables",
    "인계 확인": "check handoff deliverables",
    "납품 확인": "check handoff deliverables",
    "handoff audit": "check handoff deliverables",
    "check handoff": "check handoff deliverables",
    "파일 누락 확인": "check required files",
    "필수 파일 확인": "check required files",
    "파일 확인": "check required files",
    "check files": "check required files",
    "check required files": "check required files",
    "버전 비교": "compare versions",
    "최종본 비교": "compare versions",
    "compare versions": "compare versions",
    "review versions": "compare versions",
}
# Full-clause recognition is intentional. Never silently ignore other verbs.
SEPARATOR = re.compile(r"\s*(?:;|,|그리고|하고|\band\b)\s*", re.IGNORECASE)
TAIL = ("해주세요", "해줘", "해라", "해")

def parse_goal(goal: str) -> list[str]:
    if (not isinstance(goal, str) or not 0 < len(goal.strip()) <= MAX_GOAL_LENGTH
        or goal != goal.strip()
        or re.search(r"[\x00-\x1f\x7f\u200b-\u200f\u202a-\u202e]", goal)):
        raise WorkflowRefused("Invalid bounded goal")
    parts = SEPARATOR.split(goal)
    if not 1 <= len(parts) <= 3 or any(not s.strip() for s in parts):
        raise WorkflowRefused("Ambiguous or excessive steps")
    goals = []
    for idx, part in enumerate(parts):
        word = " ".join(part.split()).casefold()
        if idx == len(parts)-1:
            for suffix in TAIL:
                if word.endswith(suffix):
                    word = word[:-len(suffix)].strip()
                    break
        intent = INTENTS.get(word)
        if intent is None or intent in goals:
            raise WorkflowRefused("Unknown, duplicate or unsafe operation")
        goals.append(intent)
    return goals


def process_goal(goal: str, *, root: Path | None = None,
                 required: list[str] | None = None,
                 candidates: dict[str, list[str]] | None = None,
                 metadata_consent: bool = False) -> dict:
    """Ask for missing slots, otherwise preview or execute preflighted steps.

    Neither a missing slot nor an unapproved plan inspects any owner directory.
    Paths never appear in returned JSON; only approved exact local metadata can
    be checked and no source file content is read.
    """
    if type(metadata_consent) is not bool:
        raise WorkflowRefused("Invalid consent type")
    goals = parse_goal(goal)
    missing = []
    if root is None:
        missing.append("local_root")
    else:
        raw_root = str(root)
        if not Path(root).is_absolute() or raw_root.startswith(("\\\\", "//")):
            raise WorkflowRefused("Absolute non-UNC LOCAL root required")
    if required is None or required == []:
        missing.append("required_relative_paths")
        items = []
    else:
        if not isinstance(required, list) or len(required) > 100:
            raise WorkflowRefused("Invalid checklist")
        try:
            items = [_valid_relative(x) for x in required]
        except (OwnerAuditError, TypeError, ValueError) as exc:
            raise WorkflowRefused("Unsafe checklist") from exc
        if len(items) != len(set(items)):
            raise WorkflowRefused("Duplicate checklist")
    need_versions = "compare versions" in goals
    if candidates is None:
        mapping = {}
    elif not isinstance(candidates, dict):
        raise WorkflowRefused("Invalid candidate mapping")
    else:
        try:
            mapping = {_valid_relative(k): [_valid_relative(x) for x in v]
                       for k,v in candidates.items()
                       if isinstance(v, list)}
        except (OwnerAuditError, TypeError, ValueError) as exc:
            raise WorkflowRefused("Unsafe candidate mapping") from exc
        if len(mapping) != len(candidates) or set(mapping) - set(items):
            raise WorkflowRefused("Invalid bound candidate")
    if need_versions and not mapping:
        missing.append("version_candidate_mapping")

    public = {
        "mode": "BOUNDED_GOAL_TO_LOCAL_PLAN_NOT_NAS",
        "status": "WAITING_USER" if missing else "WAITING_APPROVAL",
        "plan": [{"index": i+1, "read_only_action": name}
                 for i,name in enumerate(goals)],
        "missing_inputs": missing,
        "planned_steps": len(goals),
        "executed_steps": 0,
        "owner_folder_metadata_accessed": False,
        "raw_paths_returned": False,
        "file_contents_opened": False,
        "registered_uliya_expert_invoked": False,
        "nas_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }
    if missing:
        return public
    steps = []
    for name in goals:
        step = {"goal": name, "required": items}
        if name == "compare versions":
            step["candidates"] = mapping
        steps.append(step)
    recipe = {"schema": "flowpilot-local-readonly-v1", "steps": steps}
    # Existing G63 engine preflights all stages *before* metadata access.
    result = run_workflow(Path(root), recipe, metadata_consent=metadata_consent)
    public["status"] = result["status"]
    public["executed_steps"] = result["executed_steps"]
    public["owner_folder_metadata_accessed"] = any(
        s["inspected_local_metadata"] for s in result["steps"])
    public["observed"] = result["steps"]
    return public



def _guided_paths(text: str, *, separator: str = ",") -> list[str]:
    """Parse only exact, bounded user supplied relative file names."""
    if len(text) > 4096 or not text.strip():
        raise WorkflowRefused("Provide bounded exact local relative file names")
    parts = [part.strip() for part in text.split(separator)]
    if not 1 <= len(parts) <= 100 or any(not p for p in parts):
        raise WorkflowRefused("Invalid path list")
    return parts


def _guided_versions(text: str) -> dict[str, list[str]]:
    """Semicolon-separated required=candidate assignments, no dynamic lookup."""
    if len(text) > 4096 or not text.strip():
        raise WorkflowRefused("Version candidates required")
    entries = _guided_paths(text, separator=";")
    versions: dict[str, list[str]] = {}
    for entry in entries:
        if entry.count("=") != 1:
            raise WorkflowRefused("Version mapping needs exactly one =")
        required, candidate = (x.strip() for x in entry.split("=", 1))
        if not required or not candidate:
            raise WorkflowRefused("Empty version mapping")
        versions.setdefault(required, []).append(candidate)
    return versions


def run_guided_session(goal: str, *, root: Path | None = None,
                       required: list[str] | None = None,
                       candidates: dict[str, list[str]] | None = None,
                       ask=None, emit=None) -> dict:
    """One CLI session: questions -> redacted plan -> APPROVE -> local metadata.

    No implicit consent: even if the caller supplies all required arguments,
    the exact string 'APPROVE' must be entered interactively. Never echo
    selected root or file names in displayed previews/results.
    """
    if ask is None:
        ask = input
    if emit is None:
        emit = print
    intents = parse_goal(goal)  # Disallowed goals rejected before prompts.
    if root is None:
        answer = ask("LOCAL_ROOT (absolute local directory, not NAS): ").strip()
        if not answer or len(answer) > 4096:
            raise WorkflowRefused("Missing or excessive local root")
        root = Path(answer)
    if not required:
        required = _guided_paths(ask("REQUIRED (exact relative files, comma-separated): "))
    if "compare versions" in intents and not candidates:
        candidates = _guided_versions(ask(
            "VERSIONS (required=candidate; multiple separated by semicolons): "))
    preview = process_goal(goal, root=root, required=required,
                           candidates=candidates, metadata_consent=False)
    if preview["status"] != "WAITING_APPROVAL":
        raise WorkflowRefused("Incomplete or unsafe guided plan")
    emit("FLOWPILOT_PREVIEW=" + json.dumps(preview, ensure_ascii=False))
    consent = ask("Type APPROVE to inspect only local file metadata; anything else declines: ")
    if consent != "APPROVE":
        declined = dict(preview, status="DECLINED", executed_steps=0)
        emit("FLOWPILOT_RESULT=" + json.dumps(declined, ensure_ascii=False))
        return declined
    result = process_goal(goal, root=root, required=required,
                          candidates=candidates, metadata_consent=True)
    emit("FLOWPILOT_RESULT=" + json.dumps(result, ensure_ascii=False))
    return result



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded natural-goal preview and approved LOCAL metadata run; NOT NAS")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--required", action="append")
    parser.add_argument("--candidate", action="append",
                        help="Exact required=candidate file name; repeatable")
    parser.add_argument("--interactive", action="store_true",
                        help="Ask for missing slots, show plan and obtain explicit APPROVE")
    parser.add_argument("--approve-local-metadata", action="store_true")
    args = parser.parse_args(argv)
    try:
        versions = None
        if args.candidate:
            versions = {}
            for item in args.candidate:
                if item.count("=") != 1:
                    raise WorkflowRefused("Invalid candidate pair")
                key, val = item.split("=", 1)
                versions.setdefault(key, []).append(val)
        if args.interactive:
            if args.approve_local_metadata:
                raise WorkflowRefused("Interactive consent may not be supplied as a flag")
            outcome = run_guided_session(args.goal, root=args.root,
                                         required=args.required, candidates=versions)
            return 1 if outcome["status"] == "BLOCKED" else 0
        outcome = process_goal(args.goal, root=args.root,
                               required=args.required, candidates=versions,
                               metadata_consent=args.approve_local_metadata)
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
        return 1 if outcome["status"] == "BLOCKED" else 0
    except (WorkflowRefused, OSError, ValueError, TypeError, EOFError, KeyboardInterrupt):
        print(json.dumps({"status": "GOAL_REFUSED", "release_gate": "HOLD"}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
