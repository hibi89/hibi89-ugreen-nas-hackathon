"""One command acceptance of FOUR real offline FlowPilot local capabilities.

Works only with programmatically generated, disposable fixtures. Does not
inspect the operator's home/files/NAS and does not invoke private repositories.
Report fields are bounded states and digests, never fixture paths or CSV rows.
"""
from __future__ import annotations

import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tools.flowpilot_real_os_demo import run_real_local_demo
from tools.flowpilot_synthetic_csv_panel import CSVPanel
from tools.flowpilot_owner_workbench import OwnerWorkbench, CONSENT as LSTAT_CONSENT
from tools.flowpilot_owner_csv import OwnerCSV, CONSENT as CSV_CONSENT


class AcceptanceRefused(ValueError):
    """Stable reason with no disclosure of local paths."""


def _assert(condition: bool, reason: str):
    if not condition:
        raise AcceptanceRefused(reason)


def run_acceptance() -> dict:
    summary = []

    # 1: Real OS lstat and bounded 1/2/3-intent workflows on disposable folders.
    os_result = run_real_local_demo()
    _assert(os_result.get("status") == "PASS_REAL_OS_LSTAT_SYNTHETIC_DEMO"
            and os_result.get("scenario_count") == 5
            and os_result.get("all_test_fixtures_disposed") is True
            and os_result.get("actual_nas_verified") is False,
            "OS_METADATA_FIXTURE_CHECK_FAILED")
    summary.append({"stage": "REAL_OS_LSTAT_1_TO_3_INTENTS",
                    "status": "PASS_SYNTHETIC", "scenario_count": 5})

    # 2: Actual generated-only CSV aggregation, SQLite audit and report digest.
    generated = CSVPanel()
    try:
        p = generated.configure({"output": "summary.csv"})
        _assert(p.get("workflow_preview_ready") is True
                and p.get("csv_created") is False,
                "GENERATED_CSV_PREVIEW_FAILED")
        row = generated.action("approve")
        content = generated.report()
        actual = list(csv.DictReader(StringIO(content.decode("utf-8"))))
        _assert(row.get("audit_recorded") is True
                and row.get("report_sha256") == hashlib.sha256(content).hexdigest()
                and actual == [
                    {"customer": "alice", "total_revenue": "5.00"},
                    {"customer": "bob", "total_revenue": "6.00"},
                ], "GENERATED_CSV_REPORT_FAILED")
        summary.append({"stage": "GENERATED_CSV_AGGREGATION_AND_SQLITE",
                        "status": "PASS_SYNTHETIC",
                        "output_sha256": row["report_sha256"]})
    finally:
        generated.close()

    # 3 and 4: Independent user-facing controllers with generated temporary
    # directory (no actual owner files, no data export or remote services).
    with TemporaryDirectory(prefix="flowpilot-four-stage-acceptance-") as tmp:
        base = Path(tmp)
        (base / "README.md").write_text("acceptance temporary test only", encoding="utf-8")
        workbench = OwnerWorkbench()
        lstat_scope = {
            "goal": "파일 누락 확인",
            "root": str(base), "required": ["README.md"],
            "candidates": None, "confirm_local_only": True,
        }
        first = workbench.preview(lstat_scope)
        _assert(first.get("metadata_accessed") is False,
                "OWNER_LSTAT_PREVIEW_ACCESSED_FILES")
        check = workbench.execute(first["approval_token"], LSTAT_CONSENT)
        _assert(check.get("status") == "NEEDS_REVIEW"
                and check.get("finding_counts", {}).get("PRESENT") == 1
                and check.get("executed_steps") == 1
                and check.get("raw_paths_returned") is False,
                "OWNER_LSTAT_EXECUTION_FAILED")
        summary.append({"stage": "OWNER_METADATA_CONSENT_AND_LSTAT",
                        "status": "PASS_SYNTHETIC", "present_count": 1})

        for name, amount in (("month-a.csv", "2.25"),
                             ("month-b.csv", "3.75")):
            (base / name).write_text(
                "customer,revenue\nalice," + amount + "\n", encoding="utf-8"
            )
        owner = OwnerCSV()
        try:
            selection = {
                "root": str(base),
                "sources": ["month-a.csv", "month-b.csv"],
                "output": "grouped-new.csv",
                "group": "customer", "amount": "revenue",
                "local_metadata_ack": True,
            }
            plan = owner.preview(selection)
            _assert(plan.get("source_contents_read") is False
                    and plan.get("created_output") is False,
                    "OWNER_CSV_PREVIEW_ACCESSED_CONTENTS")
            receipt = owner.execute(plan["approval_token"], CSV_CONSENT)
            data = owner.download()
            rows = list(csv.DictReader(StringIO(data.decode("utf-8"))))
            _assert(receipt.get("status") == "LOCAL_CSV_CREATED_WITH_SQLITE_AUDIT"
                    and receipt.get("audit_recorded") is True
                    and receipt.get("rows_read") == 2
                    and rows == [{"customer": "alice", "total_revenue": "6.00"}]
                    and hashlib.sha256(data).hexdigest() == receipt["report_sha256"]
                    and receipt.get("actual_nas_verified") is False,
                    "OWNER_CSV_EXECUTION_FAILED")
            with sqlite3.connect(owner._audit_db) as db:
                count = db.execute("SELECT COUNT(*) FROM flowpilot_runs").fetchone()[0]
                audit_record = json.loads(db.execute(
                    "SELECT record_json FROM flowpilot_runs LIMIT 1"
                ).fetchone()[0])
            _assert(count == 1
                    and audit_record.get("report_sha256") == receipt["report_sha256"],
                    "OWNER_CSV_AUDIT_PROOF_MISSING")
            summary.append({"stage": "OWNER_CSV_CONTENT_CONSENT_SQLITE_REPORT",
                            "status": "PASS_SYNTHETIC",
                            "output_sha256": receipt["report_sha256"],
                            "audit_row_count": 1})
        finally:
            owner.close()

    _assert(len(summary) == 4, "INCOMPLETE_LOCAL_ACCEPTANCE")
    return {
        "status": "PASS_FOUR_LOCAL_CAPABILITY_CHECKS",
        "checks": summary,
        "passed": len(summary),
        "failed": 0,
        "generated_disposable_test_data_only": True,
        "user_files_read": False,
        "source_contents_opened_in_owner_csv_synthetic_check": True,
        "actual_private_hae_la_executed": False,
        "actual_public_sovia_executed": False,
        "actual_private_dbvora_executed": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "official_creator_verified": False,
        "release_gate": "HOLD",
    }


def main() -> int:
    try:
        result = run_acceptance()
    except Exception:
        result = {
            "status": "FAIL_LOCAL_ACCEPTANCE", "passed": None,
            "failed": None, "actual_nas_verified": False, "release_gate": "HOLD",
        }
        print(json.dumps(result, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
