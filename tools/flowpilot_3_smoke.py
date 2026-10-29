"""Single-command synthetic, LOCAL FlowPilot 3.0 E2E verification.

Invokes only bounded local code in a disposable temporary directory. No NAS,
Uliya, HAE, LA, SOVIA, DBVORA, external services or user files are accessed.
Fails nonzero on unsafe approval behavior, wrong Decimal output, source changes,
missing SQLite audit, or dashboard rendering mismatch.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from flowpilot_csv_e2e import run_session
from flowpilot_command_center import render_dashboard


def run_smoke() -> dict:
    with TemporaryDirectory(prefix="flowpilot-3-local-smoke-") as tmp:
        root = Path(tmp)
        files = {
            "sales_jan.csv": [("alice", "1.25"), ("bob", "2.00")],
            "sales_feb.csv": [("alice", "3.75"), ("bob", "4.00")],
        }
        for name, records in files.items():
            with (root / name).open("x", encoding="utf-8", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["customer", "revenue"])
                writer.writerows(records)
        hashes = {name: sha256((root / name).read_bytes()).hexdigest() for name in files}
        request = dict(goal="고객별 매출 보고서 만들어줘", root=root,
                       sources=list(files), output="report.csv",
                       group="customer", amount="revenue")
        missing = run_session("고객별 매출 보고서 만들어줘")
        assert missing["status"] == "WAITING_USER"
        assert not missing["executed"]
        preview = run_session(**request)
        assert preview["status"] == "WAITING_EXECUTION_APPROVAL"
        assert preview["la_compatibility"]["status"] == "BLOCKED_MISSING_CAPABILITIES"
        assert not preview["la_compatibility"]["execution_allowed"]
        assert not (root / "report.csv").exists()
        decline = run_session(**request, approval="REJECT")
        assert decline["status"] == "DECLINED"
        assert not (root / "report.csv").exists()
        approved = run_session(**request, approval="APPROVE_EXECUTION",
                               audit_db=root / "audit.sqlite")
        assert approved["status"] == "LOCAL_REPORT_CREATED_NOT_NAS"
        assert approved["executed"] is True
        assert approved["audit"]["count"] == 1
        assert approved["nas_verified"] is False
        assert approved["la_compatibility"]["actual_la_engine_invoked"] is False
        with (root / "report.csv").open("r", encoding="utf-8", newline="") as source:
            rows = list(csv.reader(source))
        assert rows == [["customer", "total_revenue"], ["alice", "5.00"], ["bob", "6.00"]]
        assert all(sha256((root / name).read_bytes()).hexdigest() == digest
                   for name, digest in hashes.items())
        html = render_dashboard(approved)
        assert "Local report created" in html and "NAS UNVERIFIED" in html
        return {"status": "PASS", "scope": "SYNTHETIC_LOCAL_ONLY",
                "source_files": len(files), "input_rows": 4,
                "output_groups": 2, "audit_records": 1,
                "approval_and_decline_checked": True,
                "source_hashes_unchanged": True,
                "html_rendered": True,
                "actual_la_engine_invoked": False, "nas_verified": False,
                "devpost_submitted": False}


def main() -> int:
    try:
        result = run_smoke()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "scope": "SYNTHETIC_LOCAL_ONLY",
                          "error_class": type(exc).__name__}))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
