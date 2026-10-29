"""Fail-closed Lightning Azent capability boundary for FlowPilot 3.0.

This adapter does not call, import, deploy, or modify Lightning Azent.
It checks whether a declared engine supports every operation in the
FlowPilot local CSV graph; the verified 2026-10-29 HAE compatibility source
lacks aggregation and CSV-output nodes. An unverified declaration cannot
be used as evidence of engine integration.
"""
from __future__ import annotations

from collections import Counter

# Provenance: hibi89/HAE feature/axflow-mvp
# apps/ax-flow/axflow/engine.py (GitHub content blob, not an executable test).
HAE_ENGINE_BLOB_SHA = "c7a4fb0593bf49c5e54cb3ca4ddc1b03608e791a"
HAE_COMPATIBILITY_IR = "axflow.ir.v0"

# Operations present in the inspected HAE compatibility engine.
# The names are not evidence of an independently packaged LA runtime.
HAE_LEGACY_OPS = frozenset({
    "literal", "map", "condition", "branch", "csv_read", "csv_filter",
    "sqlite_import_csv", "sqlite_put", "sqlite_get",
})

# Exact operations represented by the UGREEN local workflow graph.
FLOWPILOT_LOCAL_TYPES = frozenset({
    "csv_read", "decimal_group_sum", "csv_write_new", "sqlite_audit",
})


def assess_la_compatibility(graph: dict, *, declared_ops: frozenset[str] | None = None) -> dict:
    """Evaluate exact graph node capabilities without executing or reading files.

    Throws ValueError on malformed graphs. No partial plan is returned if
    required operations are missing; never silently skip the aggregation.
    """
    if not isinstance(graph, dict) or graph.get("schema") != "flowpilot-local-workflow-graph-v1":
        raise ValueError("Unexpected graph schema")
    if graph.get("approval_required") is not True or graph.get("execution_performed") is not False:
        raise ValueError("Approval or execution boundary invalid")
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not 4 <= len(nodes) <= 23:
        raise ValueError("Invalid node count")
    if not isinstance(edges, list) or not 3 <= len(edges) <= 22:
        raise ValueError("Invalid edge count")
    ids = [node.get("id") for node in nodes if isinstance(node, dict)]
    if len(ids) != len(nodes) or len(set(ids)) != len(ids) or any(
        not isinstance(node_id, str) or not node_id for node_id in ids
    ):
        raise ValueError("Missing or duplicate node identifiers")
    types = [node.get("type") for node in nodes]
    if any(t not in FLOWPILOT_LOCAL_TYPES for t in types):
        raise ValueError("Unsupported local node type")
    counts = Counter(types)
    if (counts["csv_read"] < 1 or counts["decimal_group_sum"] != 1
            or counts["csv_write_new"] != 1 or counts["sqlite_audit"] != 1):
        raise ValueError("Incorrect CSV aggregation graph")
    expected = {(node_id, "aggregate") for node_id, t in zip(ids, types) if t == "csv_read"}
    expected.update({("aggregate", "write"), ("write", "audit")})
    actual = set()
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"from", "to"}:
            raise ValueError("Invalid edge")
        if edge["from"] not in ids or edge["to"] not in ids:
            raise ValueError("Unknown node reference")
        actual.add((edge["from"], edge["to"]))
    if actual != expected or len(edges) != len(expected):
        raise ValueError("Unexpected node topology")

    if declared_ops is None:
        available = HAE_LEGACY_OPS
        capability_source = "HAE_COMPATIBILITY_SOURCE_INSPECTED"
    elif isinstance(declared_ops, frozenset) and all(isinstance(x, str) for x in declared_ops):
        available = declared_ops
        capability_source = "CALLER_DECLARED_UNVERIFIED"
    else:
        raise ValueError("Invalid capability declaration")

    missing = sorted(set(types) - available)
    return {
        "schema": "flowpilot-la-capability-assessment-v1",
        "status": "BLOCKED_MISSING_CAPABILITIES" if missing else "DECLARED_COMPATIBLE_UNVERIFIED",
        "source": capability_source,
        "hae_compatibility_ir": HAE_COMPATIBILITY_IR,
        "hae_source_blob_sha": HAE_ENGINE_BLOB_SHA,
        "required_operations": sorted(set(types)),
        "missing_operations": missing,
        "actual_la_engine_invoked": False,
        "actual_la_integration_verified": False,
        "execution_allowed": False,
        "fallback": "EXISTING_BOUNDED_LOCAL_CSV_RUNNER_ONLY",
    }
