"""Bounded HAE-style CSV request to FlowPilot local CSV plan.

Development-only: no external HAE/LA process, NAS or Uliya invocation.
"""
from __future__ import annotations

from pathlib import Path

from flowpilot_csv_report import preview, execute, ReportRefused

SUPPORTED_GOALS = {
    "고객별 매출 보고서 만들어줘",
    "매출 CSV를 고객별로 집계해줘",
    "combine sales csv by customer",
    "create customer revenue summary",
}


def plan_request(goal: str, *, root: Path | None = None,
                 sources: list[str] | None = None, output: str | None = None,
                 group: str | None = None, amount: str | None = None) -> dict:
    if not isinstance(goal, str) or goal.strip().casefold() not in SUPPORTED_GOALS:
        raise ReportRefused("Unsupported or ambiguous goal")
    missing = []
    if root is None:
        missing.append("local_root")
    if not sources:
        missing.append("source_csv_files")
    if not output:
        missing.append("output_csv")
    if not group:
        missing.append("group_column")
    if not amount:
        missing.append("amount_column")
    if missing:
        return {"status": "WAITING_USER", "missing_inputs": missing,
                "next_action": "PROVIDE_MISSING_INPUTS", "executed": False,
                "mode": "BOUNDED_LOCAL_CSV_NOT_NAS"}
    p = preview(root, sources, output, group=group, amount=amount)
    return {"status": "WAITING_EXECUTION_APPROVAL", "missing_inputs": [],
            "next_action": "APPROVE_EXECUTION_OR_REJECT", "executed": False,
            "mode": "BOUNDED_LOCAL_CSV_NOT_NAS", "plan": p}


def run_approved_request(request: dict, *, root: Path, approval: str,
                         audit_db: Path) -> dict:
    if not isinstance(request, dict) or request.get("status") != "WAITING_EXECUTION_APPROVAL":
        raise ReportRefused("No approved-ready plan")
    if approval != "APPROVE_EXECUTION":
        return {"status": "DECLINED", "executed": False, "mode": "BOUNDED_LOCAL_CSV_NOT_NAS"}
    result = execute(root, request["plan"], approval=approval, audit_db=audit_db)
    return {"status": "LOCAL_REPORT_CREATED_NOT_NAS", "executed": True,
            "mode": "BOUNDED_LOCAL_CSV_NOT_NAS", "result": result}
