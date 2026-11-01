"""G183: persistent safe workflow resume summaries over actual local SQLite/HTTP."""
from __future__ import annotations
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_local_backend import Backend, BackendRefused, create_server, closing

TOKEN = "g183" * 12

class PersistentWorkflowListTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "g183.sqlite"
        self.b = Backend(self.db, create=True)

    def test_new_api_keeps_legacy_id_list_and_bounded_summaries(self):
        one = self.b.create("check required files", "req_g183first123")
        two = self.b.create("고객별 매출 보고서 만들어줘", "req_g183second123")
        self.b.test(one["workflow_id"])
        result = self.b.list()
        self.assertEqual(result["workflows"], [two["workflow_id"], one["workflow_id"]])
        self.assertEqual(result["summaries"], [
            {"workflow_id":two["workflow_id"],"template":"csv_customer_revenue_v1","status":"PLANNED"},
            {"workflow_id":one["workflow_id"],"template":"required_file_metadata_v1","status":"TESTED"}])
        dumped = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("고객별 매출 보고서 만들어줘", dumped)
        self.assertNotIn("check required files", dumped)
        self.assertNotIn("req_g183", dumped)
        self.assertFalse(result["nas_verified"])

    def test_restart_recovers_approved_state_without_implicit_approval(self):
        one = self.b.create("check required files", "req_g183restart123")
        self.b.test(one["workflow_id"])
        self.b.approve(one["workflow_id"], one["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
        again = Backend(self.db)
        entry = again.list()["summaries"][0]
        self.assertEqual(entry["status"], "APPROVED_SYNTHETIC")
        self.assertEqual(again.get(one["workflow_id"])["status"], "APPROVED_SYNTHETIC")
        self.assertEqual(again.get(one["workflow_id"])["event_count"], 3)

    def test_completed_receipt_is_verified_on_listing(self):
        item = self.b.create("check required files", "req_g183complete123")
        wf = item["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf, item["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        self.assertEqual(Backend(self.db).list()["summaries"][0]["status"],
                         "COMPLETE_LOCAL_SYNTHETIC")
        with closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_artifacts SET csv_bytes=? WHERE wf_id=?",
                       (b"tampered", wf))
            db.commit()
        with self.assertRaises(BackendRefused):
            Backend(self.db).list()

    def test_forged_mutable_state_is_not_exposed_as_progress(self):
        item = self.b.create("check required files", "req_g183forge123")
        with closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='TESTED' WHERE wf_id=?",
                       (item["workflow_id"],))
            db.commit()
        with self.assertRaisesRegex(BackendRefused,"GUIDE_EVENT_SEQUENCE_INVALID"):
            self.b.list()

    def test_list_is_bounded_and_does_not_mutate_hash_chain(self):
        for i in range(25):
            self.b.create("check required files", "req_g183bounded" + str(i) + "id")
        before = self.b.list()
        self.assertEqual(before["count"], 20)
        self.assertEqual(len(before["summaries"]), 20)
        self.assertEqual(Backend(self.db).list(), before)

    def test_real_http_requires_auth_and_preserves_summary_shape(self):
        item = self.b.create("check required files", "req_g183http123")
        srv = create_server(self.b, TOKEN, port=0)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        def get(auth):
            c = http.client.HTTPConnection("127.0.0.1",srv.server_port,timeout=3)
            try:
                h={"Host":f"127.0.0.1:{srv.server_port}"}
                if auth: h["Authorization"]="Bearer "+TOKEN
                c.request("GET","/v1/workflows",headers=h)
                response=c.getresponse()
                return response.status,json.loads(response.read())
            finally:c.close()
        self.assertEqual(get(False)[0],403)
        code,result = get(True)
        self.assertEqual(code,200)
        self.assertEqual(result["summaries"][0]["workflow_id"],item["workflow_id"])
        self.assertEqual(result["summaries"][0]["status"],"PLANNED")

if __name__ == "__main__":
    unittest.main()
