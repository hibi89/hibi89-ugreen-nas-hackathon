"""G185: authenticated single-workflow GET verifies state/event/plan/receipt.

Uses disposable local SQLite and a real loopback HTTP server, no UGREEN NAS,
vendor SDK, permanent owner files or external network.
"""
from __future__ import annotations

from contextlib import closing
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_local_backend as api

TOKEN = "g185" * 12
GOAL = "check required files"


class G185VerifiedStatusReadbackTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / "safe-local.sqlite"
        self.backend = api.Backend(self.db, create=True)

    def create(self, identifier="req_g185fixed123"):
        return self.backend.create(GOAL, identifier)

    def http(self, wf_id, *, token=TOKEN):
        server = api.create_server(self.backend, TOKEN, port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        try:
            headers = {"Host": f"127.0.0.1:{server.server_port}"}
            if token:
                headers["Authorization"] = "Bearer " + token
            conn.request("GET", "/v1/workflows/" + wf_id, headers=headers)
            res = conn.getresponse()
            return res.status, json.loads(res.read())
        finally:
            conn.close()

    def test_valid_planned_tested_approved_completed_readback_is_non_mutating(self):
        row = self.create()
        wf = row["workflow_id"]
        for expected in ("PLANNED", "TESTED", "APPROVED_SYNTHETIC",
                         "COMPLETE_LOCAL_SYNTHETIC"):
            with self.subTest(state=expected):
                before = self.backend.get(wf)
                actual = api.Backend(self.db).verified_get(wf)
                self.assertEqual(actual["status"], expected)
                self.assertEqual(actual["event_count"], before["event_count"])
                self.assertEqual(self.backend.get(wf), before)
            if expected == "PLANNED":
                self.backend.test(wf)
            elif expected == "TESTED":
                self.backend.approve(wf, row["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
            elif expected == "APPROVED_SYNTHETIC":
                self.backend.run(wf)

    def test_forged_tested_status_cannot_be_confirmed_by_readback(self):
        row = self.create()
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='TESTED' WHERE wf_id=?",
                       (row["workflow_id"],))
            db.commit()
        self.assertEqual(self.backend.get(row["workflow_id"])["status"], "TESTED")
        with self.assertRaisesRegex(api.BackendRefused, "GUIDE_EVENT_SEQUENCE_INVALID"):
            self.backend.verified_get(row["workflow_id"])

    def test_forged_completion_without_run_receipt_is_refused(self):
        row = self.create()
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='COMPLETE_LOCAL_SYNTHETIC' "
                       "WHERE wf_id=?", (row["workflow_id"],))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused, "GUIDE_EVENT_SEQUENCE_INVALID"):
            self.backend.verified_get(row["workflow_id"])

    def test_mutated_plan_hash_cannot_be_exposed_via_readback(self):
        row = self.create()
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET plan_sha=? WHERE wf_id=?",
                       ("0"*64, row["workflow_id"]))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused, "GUIDE_PLAN_DRIFT"):
            self.backend.verified_get(row["workflow_id"])

    def test_completed_fixture_tamper_with_matching_hash_is_refused(self):
        row = self.create()
        wf = row["workflow_id"]
        self.backend.test(wf)
        self.backend.approve(wf, row["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
        self.backend.run(wf)
        changed = b"forged-local-report"
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_artifacts SET csv_bytes=?, content_sha=? "
                       "WHERE wf_id=?", (changed, api.sha256(changed).hexdigest(), wf))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,
                                    "REPORT_CANONICAL_FIXTURE_DRIFT"):
            self.backend.verified_get(wf)

    def test_http_requires_auth_and_exposes_only_verified_state(self):
        row = self.create()
        code, denied = self.http(row["workflow_id"], token="")
        self.assertEqual(code, 403)
        self.assertEqual(denied["error"], "AUTH_REQUIRED")
        code, accepted = self.http(row["workflow_id"])
        self.assertEqual(code, 200)
        self.assertEqual(accepted["status"], "PLANNED")
        self.assertEqual(accepted["release_gate"], "HOLD")
        self.assertFalse(accepted["nas_verified"])

    def test_http_forged_status_is_denied_before_browser_reconciliation(self):
        row = self.create()
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='TESTED' WHERE wf_id=?",
                       (row["workflow_id"],))
            db.commit()
        code, data = self.http(row["workflow_id"])
        self.assertEqual(code, 409)
        self.assertEqual(data["error"], "GUIDE_EVENT_SEQUENCE_INVALID")
        self.assertEqual(data["release_gate"], "HOLD")

    def test_running_reservation_never_triggers_implicit_reexecution(self):
        row = self.create()
        wf = row["workflow_id"]
        self.backend.test(wf)
        self.backend.approve(wf, row["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
        with closing(self.backend._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='RUNNING' WHERE wf_id=?", (wf,))
            api.Backend._event(db, wf, "RUN_RESERVED")
            db.commit()
        before = self.backend.get(wf)
        seen = self.backend.verified_get(wf)
        self.assertEqual(seen["status"], "RUNNING")
        self.assertEqual(self.backend.get(wf), before)
        self.assertEqual(seen["event_count"], 4)
        self.assertFalse(seen["production_applied"])


if __name__ == "__main__":
    unittest.main()
