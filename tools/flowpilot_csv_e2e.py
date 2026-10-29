"""FlowPilot 3.0 single local E2E entrypoint.

This module composes bounded goal/slot filling, preview, separate approval,
CSV report execution and read-only SQLite audit view. NOT a NAS/Uliya runtime
or actual HAE/LA/SOVIA/DBVORA integration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flowpilot_csv_goal_bridge import plan_request, run_approved_request
from flowpilot_audit_view import recent_runs
from flowpilot_workflow_graph import build_graph
from flowpilot_la_capabilities import assess_la_compatibility
from flowpilot_csv_report import ReportRefused


def run_session(goal: str, *, root: Path | None = None,
                sources: list[str] | None = None, output: str | None = None,
                group: str | None = None, amount: str | None = None,
                approval: str | None = None, audit_db: Path | None = None) -> dict:
    request = plan_request(goal, root=root, sources=sources, output=output,
                           group=group, amount=amount)
    if request["status"] == "WAITING_USER":
        return {"status": "WAITING_USER", "request": request, "executed": False}
    if approval is None:
        graph = build_graph(request["plan"])
        return {"status": "WAITING_EXECUTION_APPROVAL", "request": request,
                "workflow_graph": graph, "la_compatibility": assess_la_compatibility(graph),
                "executed": False}
    if approval != "APPROVE_EXECUTION":
        return {"status": "DECLINED", "request": request, "executed": False}
    if audit_db is None:
        raise ReportRefused("Explicit audit database path required")
    result = run_approved_request(request, root=root, approval=approval,
                                  audit_db=audit_db)
    history = recent_runs(audit_db, limit=1)
    graph = build_graph(request["plan"])
    return {"status": result["status"], "request": request, "execution": result,
            "audit": history, "workflow_graph": graph,
            "la_compatibility": assess_la_compatibility(graph),
            "executed": True, "nas_verified": False,
            "actual_la_integrated": False, "actual_sovia_integrated": False,
            "actual_dbvora_integrated": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FlowPilot local CSV E2E demo, NOT NAS")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--output")
    parser.add_argument("--group")
    parser.add_argument("--amount")
    parser.add_argument("--approval", help="APPROVE_EXECUTION to run; omit for preview")
    parser.add_argument("--audit-db", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_session(args.goal, root=args.root, sources=args.sources,
                             output=args.output, group=args.group,
                             amount=args.amount, approval=args.approval,
                             audit_db=args.audit_db)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ReportRefused, OSError, ValueError, TypeError):
        print(json.dumps({"status": "REFUSED", "executed": False,
                          "mode": "LOCAL_DEVELOPMENT_ONLY_NOT_NAS"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
