"""FlowPilot 3.0 single local E2E entrypoint.

This module composes bounded goal/slot filling, preview, separate approval,
CSV report execution and read-only SQLite audit view. A separate opt-in
synthetic-only LA v0 import may call an installed private package, never HAE.
A separate ProjectReady local metadata mode reuses the bounded, consent-gated
owner folder inspector: not a NAS drive or a registered Uliya Expert.
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
                backend: str = "local-csv-report",
                required: list[str] | None = None,
                candidates: dict[str, list[str]] | None = None,
                hae_port: int | None = None,
                hae_csv: str | None = None,
                preview_id: str | None = None,
                hae_pending_run_id: str | None = None,
                confirm_synthetic: bool = False) -> dict:
    if backend not in {"local-csv-report", "la-synthetic-import",
                       "projectready-local-metadata", "hae-la-loopback"}:
        raise ReportRefused("Unsupported backend")
    if backend == "hae-la-loopback":
        # This is the actual existing HAE localhost HTTP service contract, not
        # an in-process fake LA import. HAE decides CSV scope at server startup.
        # No NAS data, external URL, remote service, or caller filesystem path.
        if any(value is not None for value in (
            root, sources, output, group, amount, audit_db, required, candidates,
        )):
            raise ReportRefused("HAE loopback rejects local report or metadata options")
        if hae_port is None or hae_csv is None:
            raise ReportRefused("HAE loopback requires explicit port and synthetic CSV")
        from flowpilot_hae_bridge import run_bridge
        from flowpilot_hae_bridge import BridgeRefused
        try:
            result = run_bridge(
                goal, csv_path=hae_csv, port=hae_port,
                approval=approval, preview_id=preview_id,
                pending_run_id=hae_pending_run_id,
                confirm_synthetic=confirm_synthetic,
            )
        except BridgeRefused as exc:
            raise ReportRefused("HAE loopback request refused") from exc
        return {**result, "backend": "hae-la-loopback",
                "actual_nas_integrated": False}
    if any(value is not None for value in (hae_port, hae_csv, preview_id,
                                           hae_pending_run_id)) or confirm_synthetic:
        raise ReportRefused("HAE-only flags cannot be used with other backends")
    if backend == "projectready-local-metadata":
        # Deliberately distinct from local CSV writes or real NAS access.
        if any(value is not None for value in (sources, output, group, amount, audit_db)):
            raise ReportRefused("Metadata backend rejects CSV and database options")
        from flowpilot_goal_preview import process_goal
        from flowpilot_local_workflow import WorkflowRefused
        preview = process_goal(goal, root=root, required=required,
                               candidates=candidates, metadata_consent=False)
        if approval is None or preview["status"] != "WAITING_APPROVAL":
            result = preview
        elif approval != "APPROVE_LOCAL_METADATA":
            result = dict(preview, status="DECLINED", next_action="NO_ACTION")
        else:
            result = process_goal(goal, root=root, required=required,
                                  candidates=candidates, metadata_consent=True)
        return {
            **result,
            "backend": "projectready-local-metadata",
            "executed": result["owner_folder_metadata_accessed"] is True,
            "actual_la_integrated": False,
            "actual_uliya_nas_integrated": False,
        }
    if required is not None or candidates is not None:
        raise ReportRefused("Metadata checklist options require ProjectReady backend")
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
    parser.add_argument("--backend", choices=("local-csv-report", "la-synthetic-import",
                                               "projectready-local-metadata", "hae-la-loopback"),
                        default="local-csv-report",
                        help="ProjectReady read-only local metadata or synthetic LA; default CSV")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--output")
    parser.add_argument("--group")
    parser.add_argument("--amount")
    parser.add_argument("--required", action="append",
                        help="ProjectReady: exact relative checklist file; repeatable")
    parser.add_argument("--candidate", action="append",
                        help="ProjectReady: required=candidate; repeatable")
    parser.add_argument("--approval", help="APPROVE_EXECUTION (CSV), APPROVE_SYNTHETIC_SQLITE_IMPORT (LA) or APPROVE_LOCAL_METADATA (ProjectReady)")
    parser.add_argument("--audit-db", type=Path)
    parser.add_argument("--hae-port", type=int, help="Existing HAE loopback port, 1024..65535")
    parser.add_argument("--hae-csv", help="HAE server synthetic input-root CSV basename")
    parser.add_argument("--preview-id", help="Token returned by a separate HAE preview")
    parser.add_argument("--hae-pending-run-id",
                        help="Optional run ID from newer HAE preview, for read-only error recovery")
    parser.add_argument("--confirm-synthetic", action="store_true",
                        help="Confirm that the HAE server holds synthetic test data ONLY")
    args = parser.parse_args(argv)
    try:
        candidates = None
        if args.candidate:
            candidates = {}
            for pair in args.candidate:
                if pair.count("=") != 1:
                    raise ReportRefused("Invalid candidate assignment")
                name, variant = pair.split("=", 1)
                candidates.setdefault(name, []).append(variant)
        result = run_session(args.goal, root=args.root, sources=args.sources,
                             output=args.output, group=args.group,
                             amount=args.amount, approval=args.approval,
                             audit_db=args.audit_db, backend=args.backend,
                             required=args.required, candidates=candidates,
                             hae_port=args.hae_port, hae_csv=args.hae_csv,
                             preview_id=args.preview_id,
                             hae_pending_run_id=args.hae_pending_run_id,
                             confirm_synthetic=args.confirm_synthetic)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.backend == "hae-la-loopback":
            return 2 if result["status"].startswith(("BLOCKED_", "EXECUTION_", "BRIDGE_")) else 0
        if args.backend == "la-synthetic-import":
            return 2 if result["status"].startswith(("BLOCKED_", "REFUSED_")) else 0
        if args.backend == "projectready-local-metadata":
            return 1 if result["status"] == "BLOCKED" else 0
        return 0
    except (ReportRefused, OSError, ValueError, TypeError):
        print(json.dumps({"status": "REFUSED", "executed": False,
                          "mode": "LOCAL_DEVELOPMENT_ONLY_NOT_NAS"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
