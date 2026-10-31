"""G115: exact-intent task compiler and two disposable fixture rehearsals.

NOT a general-purpose NLU model, Uliya SDK, real NAS executor, or scheduler.
The generated specification is executable only by this allowlisted local test
harness; it must not grant rights to a customer filesystem.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from flowpilot_builder_rehearsal import rehearse as csv_rehearsal
from flowpilot_csv_goal_bridge import SUPPORTED_GOALS
from flowpilot_owner_local_audit import inspect_owner_folder

SCHEMA = "flowpilot-typed-workflow-v1"
_CSV_GOALS = frozenset(x.casefold() for x in SUPPORTED_GOALS)
_FILE_GOALS = frozenset((
    "필수 파일 확인해줘",
    "누락 파일 확인해줘",
    "check required files",
    "check for missing files",
))
_CSV_NODES = (
    ("read", "csv_read", "local_fixture", "READ"),
    ("aggregate", "decimal_group_sum", "local_fixture", "COMPUTE"),
    ("output", "csv_write_new", "local_fixture", "WRITE_NEW"),
    ("audit", "sqlite_audit", "local_fixture", "WRITE_NEW"),
)
_FILE_NODES = (
    ("inventory", "file_metadata_lstat", "local_fixture", "READ"),
    ("evaluate", "required_file_check", "local_fixture", "COMPUTE"),
    ("review", "evidence_review", "local_fixture", "COMPUTE"),
)


def compile_goal(goal: str) -> dict:
    """Require an entire known goal, not substring matching or LLM inference."""
    if (type(goal) is not str or not goal or len(goal) > 200
            or goal != goal.strip() or any(ord(c) < 32 or ord(c) == 127 for c in goal)):
        return _unsupported()
    folded = goal.casefold()
    if folded in _CSV_GOALS:
        template, nodes = "csv_customer_revenue_v1", _CSV_NODES
    elif folded in _FILE_GOALS:
        template, nodes = "required_file_metadata_v1", _FILE_NODES
    else:
        return _unsupported()
    steps = [
        {"id": sid, "operation": op, "runtime": runtime,
         "access": access, "requires_owner_consent_on_real_data": access in ("READ", "WRITE_NEW")}
        for sid, op, runtime, access in nodes
    ]
    return {
        "schema": SCHEMA, "status": "READY_FOR_SYNTHETIC_TEST",
        "goal": goal, "template": template,
        "steps": steps,
        "edges": [{"from": a[0], "to": b[0]} for a, b in zip(nodes, nodes[1:])],
        "requires_real_nas_adapter": True,
        "real_nas_capability_verified": False,
        "production_approval_granted": False,
        "executed": False,
        "release_gate": "HOLD",
    }


def _unsupported() -> dict:
    return {
        "schema": SCHEMA, "status": "WAITING_USER_UNSUPPORTED_WORKFLOW",
        "supported_templates": ["csv_customer_revenue_v1", "required_file_metadata_v1"],
        "executed": False, "real_nas_capability_verified": False,
        "release_gate": "HOLD",
    }


def _file_fixture_rehearsal() -> dict:
    """Actual OS lstat over code-created files; no customer folder touched."""
    with tempfile.TemporaryDirectory(prefix="flowpilot-g115-") as tmp:
        root = Path(tmp)
        (root / "release").mkdir()
        readme = root / "README.md"
        readme.write_bytes(b"FLOWPILOT SYNTHETIC README - NO CUSTOMER DATA\n")
        expected_content = readme.read_bytes()
        required = ["README.md", "release/final.pdf"]
        denied = inspect_owner_folder(
            root, required, goal="check required files", metadata_consent=False
        )
        if denied["status"] != "WAITING_APPROVAL" or denied["inspected_local_metadata"]:
            raise AssertionError("Approval preflight accessed a local folder")
        missing = inspect_owner_folder(
            root, required, goal="check required files", metadata_consent=True
        )
        if ([r["state"] for r in missing["items"]] != ["PRESENT", "MISSING"]
                or missing["status"] != "BLOCKED"
                or missing["file_contents_opened"]):
            raise AssertionError("Missing-file fixture did not fail closed")
        # Repair ONLY this fixture's deliberately missing test file.
        (root / "release" / "final.pdf").write_bytes(b"%PDF synthetic placeholder only\n")
        restored = inspect_owner_folder(
            root, required, goal="check required files", metadata_consent=True
        )
        if ([r["state"] for r in restored["items"]] != ["PRESENT", "PRESENT"]
                or not restored["inspected_local_metadata"]
                or restored["file_contents_opened"]
                or readme.read_bytes() != expected_content):
            raise AssertionError("Synthetic metadata repair failed")
        return {
            "status": "SYNTHETIC_LOCAL_REHEARSAL_PASS",
            "template": "required_file_metadata_v1",
            "tests": [
                {"id": "approval_before_read", "status": "PASS"},
                {"id": "missing_required_file_detected", "status": "PASS"},
                {"id": "repair_disposable_test_fixture", "status": "PASS"},
                {"id": "two_required_files_present", "status": "PASS"},
                {"id": "original_test_source_unchanged", "status": "PASS"},
                {"id": "only_metadata_read_no_content_access", "status": "PASS"},
            ],
            "evidence": {
                "initial_states": ["PRESENT", "MISSING"],
                "repaired_states": ["PRESENT", "PRESENT"],
                "source_fixture_preserved": True,
                "local_os_metadata_inspected": True,
                "file_contents_opened_by_adapter": False,
            },
            "operator_runbook_markdown": (
                "# FlowPilot required-file check — LOCAL ONLY\n\n"
                "1. Choose a disposable local folder, not an NAS mount; do not use real customer files in a test.\n"
                "2. In that folder place README.md and release/final.pdf as agreed mandatory files.\n"
                "3. Preview the scoped inspection without permission:\n"
                '   python tools/flowpilot_owner_local_audit.py --root "<LOCAL_TEST_DIR>"'
                " --required README.md --required release/final.pdf\n"
                "4. If the exact read-only metadata scope is accepted, manually approve:\n"
                '   python tools/flowpilot_owner_local_audit.py --root "<LOCAL_TEST_DIR>"'
                " --required README.md --required release/final.pdf --approve-local-metadata\n"
                "5. Check the indexed PRESENT/MISSING/NOT_CHECKED states. Missing blocks release;"
                " missing permission or untrusted evidence is NOT_CHECKED.\n"
                "6. Add any missing file only after review, then repeat. Never overwrite source data.\n"
                "7. No Uliya Expert, NAS integration or permissions are verified."
                " A separate vendor adapter and owner authorization are required before NAS use.\n"
            ),
        }


def run_compiled(goal: str) -> dict:
    spec = compile_goal(goal)
    if spec["status"] != "READY_FOR_SYNTHETIC_TEST":
        return spec
    if spec["template"] == "csv_customer_revenue_v1":
        receipt = csv_rehearsal(goal)
        if receipt["status"] != "SYNTHETIC_LOCAL_REHEARSAL_PASS":
            raise AssertionError("CSV local test did not pass")
        summary = {
            "status": receipt["status"],
            "template": spec["template"],
            "tests": [{"id": name, "status": "PASS"} for name in receipt["verified_steps"]],
            "evidence": receipt["test_evidence"],
            "operator_runbook_markdown": receipt["operator_runbook_markdown"],
        }
    else:
        summary = _file_fixture_rehearsal()
    return {
        "status": summary["status"], "schema": SCHEMA,
        "compiled_workflow": spec, "template": summary["template"],
        "test_results": summary["tests"], "test_evidence": summary["evidence"],
        "operator_runbook_markdown": summary["operator_runbook_markdown"],
        "synthetic_test_executed": True, "owner_files_opened": False,
        "actual_nas_verified": False, "uliya_expert_invoked": False,
        "schedule_installed": False, "external_api_invoked": False,
        "devpost_submitted": False, "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G115 allowlisted goal compiler & local test (NOT NAS)")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--compile-only", action="store_true",
                        help="Return typed plan only, without even a temporary fixture")
    args = parser.parse_args(argv)
    try:
        result = compile_goal(args.goal) if args.compile_only else run_compiled(args.goal)
    except (AssertionError, OSError, ValueError, TypeError):
        print(json.dumps({"status": "SYNTHETIC_REHEARSAL_FAILED", "release_gate": "HOLD"}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] in ("READY_FOR_SYNTHETIC_TEST", "SYNTHETIC_LOCAL_REHEARSAL_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
