"""FlowPilot 3.0 single local E2E entrypoint.

This module composes bounded goal/slot filling, preview, separate approval,
CSV report execution and read-only SQLite audit view. A separate opt-in
synthetic-only LA v0 import may call an installed private package, never HAE.
NOT a NAS/Uliya/SOVIA/DBVORA integration or complete LA CSV reporting graph.
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

LA_SYNTHETIC_GOALS = frozenset({
    "import synthetic sales csv to local sqlite",
    "합성 매출 csv를 sqlite로 가져와줘",
})


def run_session(goal: str, *, root: Path | None = None,
                sources: list[str] | None = None, output: str | None = None,
                group: str | None = None, amount: str | None = None,
                approval: str | None = None, audit_db: Path | None = None,
                backend: str = "local-csv-report") -> dict:
    if backend not in {"local-csv-report", "la-synthetic-import"}:
        raise ReportRefused("Unsupported backend")
    if backend == "la-synthetic-import":
        # This backend is fixed to code-owned test data, not owner/customer files.
        # Refuse caller paths rather than silently ignoring them.
        if any(value is not None for value in
               (root, sources, output, group, amount, audit_db)):
            raise ReportRefused("LA synthetic adapter never accepts customer paths or fields")
        if not isinstance(goal, str) or goal.strip().casefold() not in LA_SYNTHETIC_GOALS:
            raise ReportRefused("Unsupported LA synthetic goal")
        from flowpilot_la_synthetic_import import run_demo
        result = run_demo(approval=approval)
        return {
            **result,
            "backend": "la-synthetic-import",
            "executed": result["la_execution_verified"] is True,
            "nas_verified": False,
            "actual_la_full_graph_integrated": False,
        }
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
    parser.add_argument("--backend", choices=("local-csv-report", "la-synthetic-import"),
                        default="local-csv-report",
                        help="Separate opt-in synthetic LA import; default stays local report")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--output")
    parser.add_argument("--group")
    parser.add_argument("--amount")
    parser.add_argument("--approval", help="APPROVE_EXECUTION (local report) or APPROVE_SYNTHETIC_SQLITE_IMPORT (LA)")
    parser.add_argument("--audit-db", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_session(args.goal, root=args.root, sources=args.sources,
                             output=args.output, group=args.group,
                             amount=args.amount, approval=args.approval,
                             audit_db=args.audit_db, backend=args.backend)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.backend == "la-synthetic-import":
            return 2 if result["status"].startswith(("BLOCKED_", "REFUSED_")) else 0
        return 0
    except (ReportRefused, OSError, ValueError, TypeError):
        print(json.dumps({"status": "REFUSED", "executed": False,
                          "mode": "LOCAL_DEVELOPMENT_ONLY_NOT_NAS"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
