"""G116 safe review council for bounded FlowPilot temporary-fixture workflows.

This is deterministic role separation, NOT multiple LLMs or a containerized
sandbox. No generic code execution, NAS access, Docker socket, scheduler,
external model/API call, or production apply is implemented.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy

from flowpilot_task_compiler import compile_goal, run_compiled

KNOWN_TEMPLATES = frozenset({"csv_customer_revenue_v1", "required_file_metadata_v1"})
COMPILER_SCHEMA = "flowpilot-typed-workflow-v1"
_ALLOWED_ACCESS = frozenset({"READ", "COMPUTE", "WRITE_NEW"})
_ALLOWED_OPS = frozenset({
    "csv_read", "decimal_group_sum", "csv_write_new", "sqlite_audit",
    "file_metadata_lstat", "required_file_check", "evidence_review",
})


def _review(goal: str, candidate: dict) -> tuple[bool, str]:
    """Re-derive exact allowlisted plan, never trust candidate permissions."""
    canonical = compile_goal(goal)
    if canonical.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return False, "UNSUPPORTED_GOAL"
    if type(candidate) is not dict or candidate.get("schema") != COMPILER_SCHEMA:
        return False, "INVALID_PLAN_SCHEMA"
    steps = candidate.get("steps")
    if not isinstance(steps, list) or len(steps) != len(canonical["steps"]):
        return False, "INVALID_STEP_STRUCTURE"
    for s in steps:
        if (type(s) is not dict or s.get("operation") not in _ALLOWED_OPS
                or s.get("access") not in _ALLOWED_ACCESS
                or s.get("runtime") != "local_fixture"):
            return False, "DISALLOWED_OPERATION_OR_RUNTIME"
    if candidate.get("template") not in KNOWN_TEMPLATES:
        return False, "UNKNOWN_TEMPLATE"
    if candidate != canonical:
        return False, "CANONICAL_PLAN_MISMATCH"
    return True, "EXACT_ALLOWLIST_MATCH"


def _repair_missing_edge(goal: str, candidate: dict) -> dict | None:
    """Only repair one synthetic, code-owned missing graph edge.

    This is controlled regeneration from a trusted fixed template, not an LLM
    editing arbitrary generated source or any user's files.
    """
    canonical = compile_goal(goal)
    if canonical.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return None
    if (type(candidate) is not dict or
            set(candidate) != set(canonical) or
            candidate.get("steps") != canonical["steps"] or
            candidate.get("template") != canonical["template"]):
        return None
    if any(candidate.get(key) != value for key, value in canonical.items()
           if key not in ("edges",)):
        return None
    edges = candidate.get("edges")
    expected = canonical["edges"]
    if not isinstance(edges, list) or len(edges) != len(expected) - 1:
        return None
    if edges != expected[:-1]:
        return None
    return deepcopy(canonical)


def run_council(goal: str, *, inject_test_fault: bool = False,
                max_repairs: int = 1) -> dict:
    """Accept no caller-controlled source; return evidence before any apply."""
    if type(inject_test_fault) is not bool or type(max_repairs) is not int or max_repairs not in (0, 1):
        raise ValueError("Invalid bounded review options")
    proposed = compile_goal(goal)
    base = {
        "schema": "flowpilot-council-review-v1",
        "container_sandbox_executed": False,
        "docker_isolation_verified": False,
        "multi_llm_agents_invoked": False,
        "owner_nas_accessed": False,
        "actual_nas_verified": False,
        "production_applied": False,
        "external_network_called": False,
        "release_gate": "HOLD",
    }
    if proposed.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return {**base, "status": "WAITING_USER_UNSUPPORTED_WORKFLOW",
                "trace": [], "repair_count": 0, "fixture_executed": False}
    plan = deepcopy(proposed)
    if inject_test_fault:
        # Fault solely in a local in-memory copy; cannot alter original source.
        plan["edges"] = plan["edges"][:-1]
    trace = []
    ok, reason = _review(goal, plan)
    trace.append({"role": "Architect", "status": "PASS" if ok else "REJECTED",
                  "reason": reason})
    repairs = 0
    if not ok:
        if not inject_test_fault or not max_repairs:
            return {**base, "status": "REVIEW_BLOCKED", "trace": trace,
                    "repair_count": repairs, "fixture_executed": False}
        repaired = _repair_missing_edge(goal, plan)
        if repaired is None:
            return {**base, "status": "REPAIR_REJECTED", "trace": trace,
                    "repair_count": repairs, "fixture_executed": False}
        plan = repaired
        repairs = 1
        ok, reason = _review(goal, plan)
        trace.append({"role": "Architect", "status": "PASS" if ok else "REJECTED",
                      "reason": reason})
        if not ok:
            return {**base, "status": "REPAIR_REJECTED", "trace": trace,
                    "repair_count": repairs, "fixture_executed": False}
        trace.append({"role": "Repair", "status": "PASS", "reason": "TRUSTED_TEMPLATE_EDGE_RESTORED"})
    # Separate immutable policy stage prevents a plan from conferring privileges.
    if (any(s["access"] == "WRITE_NEW" for s in plan["steps"])
            and plan["template"] != "csv_customer_revenue_v1"):
        trace.append({"role": "Security", "status": "REJECTED",
                      "reason": "UNEXPECTED_WRITE_CAPABILITY"})
        return {**base, "status": "SECURITY_BLOCKED", "trace": trace,
                "repair_count": repairs, "fixture_executed": False}
    trace.append({"role": "Security", "status": "PASS",
                  "reason": "FIXTURE_ONLY_NO_NETWORK_NO_NAS"})
    trace.append({"role": "Builder", "status": "PASS",
                  "reason": "REUSE_EXISTING_BOUNDED_EXECUTOR"})
    receipt = run_compiled(goal)
    test_results = receipt.get("test_results", ())
    if (receipt.get("status") != "SYNTHETIC_LOCAL_REHEARSAL_PASS"
            or not test_results or
            any(t.get("status") != "PASS" for t in test_results)
            or receipt.get("actual_nas_verified") is not False
            or receipt.get("owner_files_opened") is not False
            or receipt.get("uliya_expert_invoked") is not False):
        trace.append({"role": "QA", "status": "REJECTED", "reason": "FIXTURE_RESULT_NOT_TRUSTED"})
        return {**base, "status": "QA_BLOCKED", "trace": trace,
                "repair_count": repairs, "fixture_executed": True}
    trace.append({"role": "QA", "status": "PASS", "reason": "SYNTHETIC_TESTS_ONLY"})
    return {
        **base, "status": "OFFLINE_COUNCIL_REHEARSAL_PASS", "trace": trace,
        "repair_count": repairs, "fixture_executed": True,
        "compiled_template": plan["template"],
        "test_results": test_results,
        "test_evidence": receipt["test_evidence"],
        "operator_runbook_markdown": receipt["operator_runbook_markdown"],
        "next_gate": "G116_DOCKER_RUNTIME_CONTRACT_AND_OFFICIAL_ULIYA_CAPABILITY_NOT_VERIFIED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G116 offline deterministic council, NOT Docker or NAS")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--inject-test-fault", action="store_true",
                        help="Delete one in-memory graph edge for bounded correction demo")
    parser.add_argument("--max-repairs", type=int, choices=(0, 1), default=1)
    args = parser.parse_args(argv)
    try:
        result = run_council(args.goal, inject_test_fault=args.inject_test_fault,
                             max_repairs=args.max_repairs)
    except (AssertionError, OSError, ValueError, TypeError):
        print(json.dumps({"status": "OFFLINE_COUNCIL_FAILED", "release_gate": "HOLD"}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "OFFLINE_COUNCIL_REHEARSAL_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
