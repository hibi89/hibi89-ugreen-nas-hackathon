"""G64: small deterministic Korean/English text-to-local-readonly workflow adapter.

Not a free-form LLM or an official Uliya, NAS or Agent integration.
No owner-folder access is possible until every parsed step is preflighted and
the operator explicitly approves the one invocation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flowpilot_local_workflow import run_workflow, WorkflowRefused

MAX_INSTRUCTION_CHARS = 4096
LABELS = {
    "check files": "check required files",
    "check required files": "check required files",
    "파일 확인": "check required files",
    "필수 파일 확인": "check required files",
    "누락 확인": "check required files",
    "compare versions": "compare versions",
    "review versions": "compare versions",
    "버전 비교": "compare versions",
    "최종본 비교": "compare versions",
    "check handoff": "check handoff deliverables",
    "handoff audit": "check handoff deliverables",
    "납품 확인": "check handoff deliverables",
    "인계 확인": "check handoff deliverables",
}

def _names(text: str) -> list[str]:
    names = [n.strip() for n in text.split(",")]
    if not 1 <= len(names) <= 100 or any(not n for n in names):
        raise WorkflowRefused("File checklist not explicit or bounded")
    return names

def parse_instructions(instructions: str) -> dict:
    """Fail closed on unknown verbs, ambiguous boundaries and bad DSL input."""
    if (not isinstance(instructions, str) or
            not 0 < len(instructions.strip()) <= MAX_INSTRUCTION_CHARS or
            instructions != instructions.strip() or
            "\r" in instructions or "\x00" in instructions):
        raise WorkflowRefused("Invalid bounded instruction")
    # Only whole, explicitly delimited stages. No silent partial parsing.
    clauses = instructions.replace("\n", ";").split(";")
    if not 1 <= len(clauses) <= 8 or any(not c.strip() for c in clauses):
        raise WorkflowRefused("Invalid step delimiter or count")
    stages = []
    for clause in clauses:
        if clause.count(":") != 1:
            raise WorkflowRefused("Each stage needs one action and colon")
        raw_label, raw_targets = clause.split(":", 1)
        label = " ".join(raw_label.split()).casefold()
        goal = LABELS.get(label)
        if goal is None:
            raise WorkflowRefused("Unknown or unsafe operation")
        if goal == "compare versions":
            if raw_targets.count("=>") != 1:
                raise WorkflowRefused("Explicit base => candidate required")
            base, candidates = raw_targets.split("=>", 1)
            basenames = _names(base)
            alternatives = _names(candidates)
            if len(basenames) != 1:
                raise WorkflowRefused("One base file per version stage")
            stages.append({
                "goal": goal,
                "required": basenames,
                "candidates": {basenames[0]: alternatives},
            })
        else:
            if "=>" in raw_targets:
                raise WorkflowRefused("Version syntax not valid for this action")
            stages.append({"goal": goal, "required": _names(raw_targets)})
    return {"schema": "flowpilot-local-readonly-v1", "steps": stages}

def run_text_workflow(root: Path, instructions: str,
                      *, metadata_consent: bool = False) -> dict:
    # Parsing and existing G63 preflight both complete before owner-root reads.
    recipe = parse_instructions(instructions)
    row = run_workflow(root, recipe, metadata_consent=metadata_consent)
    row["mode"] = "G64_EXPLICIT_TEXT_LOCAL_ONLY_NOT_NAS"
    row["parsed_actions_count"] = len(recipe["steps"])
    row["freeform_ai_interpretation_used"] = False
    return row

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Explicit Korean/English text to local read-only workflow; NOT NAS.")
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--instructions", required=True,
        help="e.g. '파일 확인: README.md; 버전 비교: final.pdf => final_v2.pdf'")
    ap.add_argument("--approve-local-metadata", action="store_true")
    args = ap.parse_args(argv)
    try:
        row = run_text_workflow(args.root, args.instructions,
                                metadata_consent=args.approve_local_metadata)
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 1 if row["status"] == "BLOCKED" else 0
    except (WorkflowRefused, ValueError, TypeError, OSError):
        print(json.dumps({"status": "TEXT_WORKFLOW_REFUSED", "release_gate": "HOLD"}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
