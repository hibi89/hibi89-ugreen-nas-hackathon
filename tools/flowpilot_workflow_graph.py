"""FlowPilot 3.0 deterministic workflow graph for review.

This is a LOCAL, bounded graph representation. It does NOT call Lightning
Azent, n8n, HAE, Uliya or NAS. Its purpose is to make the existing CSV
preview inspectable before explicit execution approval.
"""
from __future__ import annotations

from flowpilot_csv_report import ReportRefused

NODE_TYPES = ("csv_read", "decimal_group_sum", "csv_write_new", "sqlite_audit")


def build_graph(plan: dict) -> dict:
    if not isinstance(plan, dict) or plan.get("schema") != "flowpilot-local-csv-v1":
        raise ReportRefused("Unsupported workflow plan")
    if plan.get("status") != "WAITING_EXECUTION_APPROVAL":
        raise ReportRefused("Workflow not awaiting approval")
    sources = plan.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 20:
        raise ReportRefused("Invalid source list")
    if plan.get("operations") != ["read_csv", "group_sum_decimal", "write_new_csv"]:
        raise ReportRefused("Unsupported operations")
    nodes = []
    for index, source in enumerate(sources):
        nodes.append({"id": f"read_{index + 1}", "type": "csv_read",
                      "label": f"Read CSV {index + 1}", "source": source})
    nodes.extend([
        {"id": "aggregate", "type": "decimal_group_sum",
         "label": "Group and sum", "group": plan.get("group"), "amount": plan.get("amount")},
        {"id": "write", "type": "csv_write_new",
         "label": "Write new CSV", "output": plan.get("output")},
        {"id": "audit", "type": "sqlite_audit", "label": "Record local run"},
    ])
    edges = [{"from": f"read_{i+1}", "to": "aggregate"} for i in range(len(sources))]
    edges.extend([{"from": "aggregate", "to": "write"},
                  {"from": "write", "to": "audit"}])
    return {"schema": "flowpilot-local-workflow-graph-v1",
            "nodes": nodes, "edges": edges,
            "approval_required": True, "execution_performed": False,
            "generator": "FLOWPILOT_DETERMINISTIC_LOCAL",
            "actual_la_engine_used": False, "n8n_executable": False,
            "nas_verified": False}
