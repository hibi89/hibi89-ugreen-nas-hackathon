"""G58: single-command, minimal runnable FlowPilot intent-to-evidence demo.

All observations are invented, committed synthetic fixtures. This program does
NOT read user NAS, discover files, invoke Uliya, run Creator or submit to Devpost.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from flowpilot.pipeline import evaluate_offline
from flowpilot.evidence import ObservationBatch, Observed
from flowpilot_offline_demo import CASES

DEMO_ROOT = "/volume1/projects/synthetic-flowpilot-demo"
DEFAULT_REQUESTS = {
    "complete_synthetic_handoff": "check handoff deliverables",
    "missing_required_synthetic": "check required files",
    "conflicting_versions_synthetic": "compare versions",
    "truncated_or_denied_synthetic": "check required files",
    "symlink_unknown_synthetic": "check required files",
}


def run_mvp(scenario: str, request: str | None = None) -> dict:
    """Plan and evaluate a known synthetic dataset without any NAS connection."""
    if scenario not in CASES:
        raise ValueError("Unknown offline-only scenario")
    fixture = CASES[scenario]
    goal = DEFAULT_REQUESTS[scenario] if request is None else request
    if not isinstance(goal, str) or len(goal) > 2048:
        raise ValueError("Request is not a bounded text input")
    observations = tuple(Observed(**row) for row in fixture["observations"])
    # Flags below are synthetic scenario claims, not real user permission or
    # an actual registered NAS expert. The response is always non-READY.
    batch = ObservationBatch(
        authorized_root=DEMO_ROOT,
        observations=observations,
        permission_confirmed=fixture["permission_confirmed"],
        registered_adapter_confirmed=fixture["registered_adapter_confirmed"],
        scan_complete=fixture["scan_complete"],
        pagination_complete=fixture["pagination_complete"],
        failed=fixture.get("failed", False),
    )
    outcome = evaluate_offline(
        request=goal,
        root=DEMO_ROOT,
        required_paths=fixture["required_paths"],
        metadata_approved=True,
        unknown_processing_accepted=True,
        batch=batch,
        version_candidates=fixture.get("version_candidates"),
    )
    return {
        "mode": "SYNTHETIC_OFFLINE_MVP_ONLY",
        "scenario": scenario,
        "goal_type": outcome.plan.intent.value if outcome.plan.intent else None,
        "status": outcome.status,
        "plan_state": outcome.plan.state.value,
        "planned_expert_steps_not_executed": [
            {"step": step.id, "expert": step.expert}
            for step in outcome.plan.steps
        ],
        "required_items": [
            {"path": item.relative_path, "state": item.state.value,
             "synthetic_references": list(item.evidence)}
            for item in outcome.report.items
        ] if outcome.report else [],
        "questions": list(outcome.plan.questions),
        "limitations": list(outcome.limitations),
        "fixture_claims_only": True,
        "actual_nas_verified": False,
        "official_creator_execution_verified": False,
        "registered_agent_invoked": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="G58 synthetic CLI MVP: goal → plan → evidence, no real NAS access")
    parser.add_argument("--scenario", choices=tuple(CASES),
                        default="complete_synthetic_handoff")
    parser.add_argument("--request", help="Override the synthetic demo's task wording")
    args = parser.parse_args(argv)
    result = run_mvp(args.scenario, args.request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
