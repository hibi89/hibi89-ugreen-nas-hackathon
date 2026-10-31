"""G114: bounded natural-language -> tested local workflow -> operator runbook.

Runs on temporary, code-owned synthetic data only; it never opens a user's
folder, runs a NAS/Uliya Expert, installs a Skill, or schedules a job.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path

from flowpilot_csv_e2e import run_session
from flowpilot_csv_goal_bridge import SUPPORTED_GOALS
from flowpilot_csv_report import ReportRefused

_GOALS = frozenset(goal.casefold() for goal in SUPPORTED_GOALS)
_EXPECTED = [["customer", "total_revenue"], ["alice", "4.00"], ["bob", "3.00"]]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def _guide(goal: str) -> str:
    # Use only an allowlisted goal; never interpolate raw arbitrary shell text.
    return ("# FlowPilot local CSV workflow — operator guide\n\n"
            f"Requested goal: {goal}\n\n"
            "1. Create a separate, authorized test folder on a computer with Python 3.11. "
            "Do NOT point the local test at an NAS mount or customer folder.\n"
            "2. Add `sales.csv` with headers `customer,revenue` and sample rows. "
            "Never include passwords or personal customer records in a rehearsal.\n"
            "3. From the UGREEN repository root, preview the graph with:\n"
            '   `python tools/flowpilot_csv_e2e.py --goal "create customer revenue summary" '
            '--root "<LOCAL_TEST_DIR>" --source sales.csv --output summary.csv '
            '--group customer --amount revenue`\n'
            "4. Review the source, output, and graph. Only on an authorized LOCAL "
            "folder, deliberately approve:\n"
            '   `python tools/flowpilot_csv_e2e.py --goal "create customer revenue summary" '
            '--root "<LOCAL_TEST_DIR>" --source sales.csv --output summary.csv '
            '--group customer --amount revenue --approval APPROVE_EXECUTION '
            '--audit-db "<LOCAL_TEST_DIR>/audit.sqlite"`\n'
            "5. Confirm `summary.csv` has `customer,total_revenue` and inspect the "
            "local SQLite audit record. To rerun, choose a NEW output filename; "
            "existing outputs are not overwritten.\n"
            "6. To stop/recover, keep original source files and audit evidence, "
            "inspect the error, and retry only with a new output.\n"
            "7. NAS installation, scheduler integration, registered Uliya Expert "
            "permissions, and document processing are NOT validated here. "
            "Confirm a supported platform contract and obtain separate owner consent "
            "before any NAS access, writes, transfers, or recurring execution.\n")


def rehearse(goal: str) -> dict:
    """Test a single supported scenario; never treat it as real NAS evidence."""
    if (not isinstance(goal, str) or goal != goal.strip() or
            len(goal) > 200 or goal.casefold() not in _GOALS):
        return {"status": "WAITING_USER_UNSUPPORTED_WORKFLOW", "executed": False,
                "supported_example": "고객별 매출 보고서 만들어줘",
                "reason": "Only the bounded customer revenue CSV example is implemented",
                "actual_nas_verified": False}
    with tempfile.TemporaryDirectory(prefix="flowpilot-g114-") as scratch:
        root = Path(scratch)
        source, output, audit = root / "sales.csv", root / "summary.csv", root / "audit.sqlite"
        params = {"goal": goal, "root": root, "sources": ["sales.csv"],
                  "output": "summary.csv", "group": "customer", "amount": "revenue"}
        # Demonstrate a real, safe failure on invalid disposable input.
        _write_csv(source, [["customer", "revenue"], ["alice", "invalid_number"]])
        invalid_refused = False
        try:
            run_session(**params, approval="APPROVE_EXECUTION", audit_db=audit)
        except ReportRefused:
            invalid_refused = not output.exists() and not audit.exists()
        if not invalid_refused:
            raise AssertionError("Malformed fixture did not fail closed")
        source.unlink()  # only code-created disposable fixture, never user input
        _write_csv(source, [["customer", "revenue"], ["alice", "1.25"],
                            ["alice", "2.75"], ["bob", "3.00"]])
        original_sha = _digest(source)
        preview = run_session(**params)
        if (preview["status"] != "WAITING_EXECUTION_APPROVAL" or
                preview["executed"] or output.exists()):
            raise AssertionError("Preview unexpectedly executed")
        result = run_session(**params, approval="APPROVE_EXECUTION", audit_db=audit)
        if result["status"] != "LOCAL_REPORT_CREATED_NOT_NAS" or not result["executed"]:
            raise AssertionError("Approved synthetic report was not created")
        with output.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if rows != _EXPECTED or _digest(source) != original_sha:
            raise AssertionError("CSV output or source integrity mismatch")
        if result["audit"]["count"] != 1:
            raise AssertionError("Expected exactly one SQLite audit record")
        out_sha = _digest(output)
        duplicate_refused = False
        try:
            run_session(**params, approval="APPROVE_EXECUTION", audit_db=audit)
        except ReportRefused:
            duplicate_refused = True
        if (not duplicate_refused or _digest(output) != out_sha or
                result["execution"]["result"]["report_sha256"] != out_sha):
            raise AssertionError("Duplicate protection or report digest failed")
        return {
            "status": "SYNTHETIC_LOCAL_REHEARSAL_PASS",
            "mode": "TEMPORARY_LOCAL_FIXTURE_ONLY",
            "requested_goal": goal,
            "workflow_graph": preview["workflow_graph"],
            "verified_steps": ["reject_invalid_csv_without_output",
                               "repair_disposable_fixture", "preview_without_write",
                               "approved_local_execution", "verify_expected_csv_and_sqlite",
                               "reject_duplicate_output"],
            "test_evidence": {"expected_rows": _EXPECTED, "observed_rows": rows,
                              "source_sha256": original_sha, "report_sha256": out_sha,
                              "sqlite_audit_rows": result["audit"]["count"],
                              "invalid_input_refused": invalid_refused,
                              "duplicate_output_refused": duplicate_refused},
            "operator_runbook_markdown": _guide(goal),
            "actual_nas_verified": False, "uliya_expert_invoked": False,
            "hae_or_la_executed": False, "schedule_installed": False,
            "owner_files_opened": False, "devpost_submitted": False,
            "release_gate": "HOLD",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic FlowPilot build/test/guide, NOT NAS")
    parser.add_argument("--goal", required=True)
    args = parser.parse_args(argv)
    try:
        result = rehearse(args.goal)
    except (AssertionError, ReportRefused, OSError, ValueError, TypeError):
        print(json.dumps({"status": "LOCAL_REHEARSAL_FAILED", "release_gate": "HOLD"}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "SYNTHETIC_LOCAL_REHEARSAL_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
