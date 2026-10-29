"""Executable synthetic FlowPilot -> LA preflight -> SOVIA review showcase.

This showcases an actual UGREEN natural-goal planner and an opt-in, installed
SOVIA assessor. Real HAE LA may be supplied for plan *preflight only*; no
execute, local customer metadata, NAS, Uliya Expert or network access is used.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from flowpilot_goal_preview import process_goal
from integrations.flowpilot_la_coordinator import compose_previews

READ_PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "synthetic", "op": "literal", "value": {"sample": True}},
]}
WRITE_PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "synthetic", "op": "literal", "value": {"sample": True}},
    {"id": "store", "op": "sqlite_put", "from": "synthetic"},
]}
POLICY = {"schema_version": "1.0", "policy": {
    "allowed_tools": ["la_literal", "la_sqlite_put"],
    "approved_destinations": [], "sensitive_targets": [],
}}


class SimulatedLA:
    """A plan-only stand-in. Never misidentify it as actual HAE LA."""

    @staticmethod
    def preflight(plan):
        steps = [{"id": s["id"], "op": s["op"]} for s in plan["steps"]]
        return {
            "source_version": "azent.ir.v0",
            "trigger_type": "manual",
            "step_count": len(steps),
            "steps": steps,
            "requires_write_approval": any(s["op"] == "sqlite_put" for s in steps),
            "requires_input_root": False,
            "executes_workflow": False,
            "scope": "synthetic-local-only",
        }


def showcase(scenario, sovia_assess, *, la_api=SimulatedLA,
             la_real_source=False):
    if scenario not in ("read_only", "write_review", "missing_input", "declined"):
        raise ValueError("unsupported synthetic scenario")
    plan = WRITE_PLAN if scenario == "write_review" else READ_PLAN
    with tempfile.TemporaryDirectory(prefix="ugreen-showcase-") as tmp:
        selected = None if scenario == "missing_input" else Path(tmp)
        request = {
            "intent": "CHECK_REQUIRED", "folder": str(Path(tmp)),
            "required_paths": ["README.md"],
            "owner_approved_metadata": scenario != "declined",
            "runtime_permissions_verified": True,
            "processing_location_accepted": True,
        }
        result = compose_previews(
            "필수 파일 확인", root=selected, required=["README.md"],
            candidates=None, la_plan=plan, owner_request=request,
            flowpilot_preview=process_goal, la_api=la_api,
            sovia_assess=sovia_assess, sovia_policy=POLICY,
        )
    return {
        "mode": "SYNTHETIC_PLAN_PREVIEW_AND_ADVISORY_ONLY",
        "scenario": scenario,
        "flowpilot": result["status"],
        "planned_steps": result["flowpilot"]["planned_steps"],
        "la": result["la"]["state"],
        "la_preflight_source": ("OWNER_PROVIDED_HAE_LA_PREFLIGHT"
                                if la_real_source else "SIMULATED_LA_PREFLIGHT"),
        "sovia": result["la"].get("sovia", {}).get("state", "NOT_CHECKED"),
        "advisory_finding_count": result["la"].get("sovia", {}).get("finding_count"),
        "execution_authorized": False,
        "la_workflow_executed": False,
        "owner_folder_metadata_accessed": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Synthetic UGREEN/LA/SOVIA showcase, NO execution or NAS")
    parser.add_argument("--sovia-root", type=Path, required=True,
                        help="Owner-approved source folder containing sovia_la_plan_preflight.py")
    parser.add_argument("--la-package-root", type=Path,
                        help="Optional owner-approved HAE packages/lightning-azent source")
    parser.add_argument("--scenario", choices=("read_only", "write_review",
                        "missing_input", "declined"), default="write_review")
    args = parser.parse_args(argv)
    try:
        sovia_root = args.sovia_root.resolve(strict=True)
        if not (sovia_root / "sovia_la_plan_preflight.py").is_file():
            raise ValueError("SOVIA source missing")
        sys.path.insert(0, str(sovia_root))
        from sovia_la_plan_preflight import assess
        la_api, real = SimulatedLA, False
        if args.la_package_root is not None:
            la_root = args.la_package_root.resolve(strict=True)
            if not (la_root / "lightning_azent" / "runtime.py").is_file():
                raise ValueError("LA package source missing")
            sys.path.insert(0, str(la_root))
            from lightning_azent import LAExecutor
            la_api, real = LAExecutor, True
        print(json.dumps(showcase(args.scenario, assess, la_api=la_api,
                                  la_real_source=real), ensure_ascii=False,
                         sort_keys=True))
    except (OSError, ImportError, ValueError, RuntimeError, TypeError) as error:
        print(json.dumps({"result": "FAIL", "error_type": type(error).__name__,
                          "actual_nas_verified": False, "release_gate": "HOLD"}),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
