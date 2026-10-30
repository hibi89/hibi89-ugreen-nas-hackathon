"""Generated-only CSV automation adapter; genuine CSV writer and SQLite audit.

No customer paths, private repositories, NAS or Uliya access.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for item in (ROOT, ROOT / "tools"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from flowpilot_3_live_demo import DemoController, GOAL


class CSVPanelRefused(ValueError):
    pass


class CSVPanel:
    def __init__(self):
        self._engine = DemoController()
        self._closed = False

    def close(self):
        if not self._closed:
            self._closed = True
            self._engine.close()

    def _redact(self, row):
        state = row.get("status")
        if state not in ("WAITING_EXECUTION_APPROVAL", "DECLINED",
                         "LOCAL_REPORT_CREATED_NOT_NAS"):
            raise CSVPanelRefused("UNVERIFIED_CSV_STATUS")
        made = state == "LOCAL_REPORT_CREATED_NOT_NAS"
        answer = {
            "status": state, "generated_only": True,
            "workflow_preview_ready": state == "WAITING_EXECUTION_APPROVAL",
            "csv_created": made, "audit_recorded": False,
            "report_sha256": None,
            "nas_verified": False, "actual_la_integrated": False,
            "actual_sovia_integrated": False, "actual_dbvora_integrated": False,
            "registered_uliya_expert_invoked": False,
            "release_gate": "HOLD",
        }
        if made:
            receipt = row.get("execution", {}).get("result", {})
            audit = row.get("audit", {})
            sha = receipt.get("report_sha256")
            if (type(sha) is not str or len(sha) != 64
                    or any(c not in "0123456789abcdef" for c in sha)
                    or type(audit) is not dict or audit.get("count") != 1):
                raise CSVPanelRefused("UNVERIFIED_CSV_RECEIPT")
            answer["audit_recorded"] = True
            answer["report_sha256"] = sha
        return answer

    def configure(self, request):
        if self._closed or type(request) is not dict or set(request) != {"output"}:
            raise CSVPanelRefused("INVALID_CSV_REQUEST")
        output = request["output"]
        if type(output) is not str or output not in ("summary.csv", "monthly-summary.csv"):
            raise CSVPanelRefused("INVALID_CSV_OUTPUT")
        row = self._engine.configure({
            "goal": GOAL, "sources": ["jan.csv", "feb.csv"], "output": output,
        })
        return self._redact(row)

    def action(self, action):
        if self._closed or action not in ("approve", "reject"):
            raise CSVPanelRefused("INVALID_CSV_ACTION")
        return self._redact(self._engine.act(action))

    def report(self):
        if self._closed:
            raise CSVPanelRefused("CLOSED_CSV_PANEL")
        data = self._engine.report_csv()  # checks digest against actual receipt
        if not 0 < len(data) <= 1_000_000:
            raise CSVPanelRefused("INVALID_CSV_REPORT")
        return data
