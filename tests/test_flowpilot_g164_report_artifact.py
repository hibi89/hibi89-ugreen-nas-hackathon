"""G164: real fixture CSV readback is bound to G119 receipt; no NAS data."""
from __future__ import annotations
from hashlib import sha256
import http.client
import json
from pathlib import Path
import sys
import threading
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from flowpilot_local_backend import Backend,BackendRefused,create_server
from flowpilot_g164_report_artifact import fixture_csv, ArtifactRefused
from flowpilot_repair_ledger import run_once
import sqlite3
from contextlib import closing

C_GOAL="create customer revenue summary"
F_GOAL="check required files"
TOKEN="j"*48

class G164Tests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.p=Path(t.name)/"owner-only-new.sqlite"
        self.b=Backend(self.p,create=True)

    def completed(self,goal=C_GOAL,key="req_g164render123"):
        first=self.b.create(goal,key)
        wf=first["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,first["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.assertEqual(self.b.run(wf)["status"],"COMPLETE_LOCAL_SYNTHETIC")
        return wf

    def test_genuine_csv_fixture_persisted_and_restarted(self):
        wf=self.completed()
        raw,digest=self.b.report(wf)
        self.assertEqual(raw,b"customer,total_revenue\r\nalice,4.00\r\nbob,3.00\r\n")
        self.assertEqual(digest,sha256(raw).hexdigest())
        restarted=Backend(self.p)
        self.assertEqual(restarted.report(wf),(raw,digest))
        self.assertEqual(self.b.run(wf)["status"],"COMPLETE_LOCAL_SYNTHETIC")
        with closing(self.b._connect()) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM fp_backend_artifacts").fetchone()[0],1)
        self.assertEqual(self.b.evidence(wf)["release_gate"],"HOLD")

    def test_file_metadata_receipt_creates_real_csv_from_states(self):
        wf=self.completed(F_GOAL,"req_g164filemeta1")
        raw,digest=self.b.report(wf)
        self.assertEqual(raw,
                         b"phase,required_1,required_2\r\ninitial,PRESENT,MISSING\r\n"
                         b"after_fixture_repair,PRESENT,PRESENT\r\n")
        self.assertEqual(digest,sha256(raw).hexdigest())
        self.assertEqual(self.b.get(wf)["event_count"],5)

    def test_no_artifact_before_approval_and_run(self):
        wf=self.b.create(C_GOAL,"req_g164denied123")["workflow_id"]
        with self.assertRaisesRegex(BackendRefused,"REPORT_NOT_YET_COMPLETE"):
            self.b.report(wf)
        self.b.test(wf)
        with self.assertRaisesRegex(BackendRefused,"REPORT_NOT_YET_COMPLETE"):
            self.b.report(wf)

    def test_byte_flip_fails_closed(self):
        wf=self.completed()
        with closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_artifacts SET csv_bytes=? WHERE wf_id=?",
                       (b"malicious,row\n",wf))
            db.commit()
        with self.assertRaisesRegex(BackendRefused,"REPORT_CONTENT_CORRUPTED"):
            self.b.report(wf)

    def test_receipt_forgery_fails_closed(self):
        wf=self.completed()
        with closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_artifacts SET receipt_sha=? WHERE wf_id=?",
                       ("f"*64,wf))
            db.commit()
        with self.assertRaisesRegex(BackendRefused,"REPORT_BINDING_MISMATCH"):
            self.b.report(wf)

    def test_bad_fixture_evidence_refused(self):
        with self.assertRaisesRegex(ArtifactRefused,"UNTRUSTED_CSV_FIXTURE"):
            fixture_csv("csv_customer_revenue_v1",{"observed_rows":[["=cmd","100"]]})
        with self.assertRaisesRegex(ArtifactRefused,"UNTRUSTED_FILE_METADATA"):
            fixture_csv("required_file_metadata_v1",{"initial_states":["PRESENT","PRESENT"]})
        with self.assertRaisesRegex(ArtifactRefused,"UNSUPPORTED_ARTIFACT"):
            fixture_csv("arbitrary_shell",{})

    def test_crashed_reserved_run_does_not_reexecute_and_cannot_claim_complete(self):
        initial=self.b.create(C_GOAL,"req_g164crashrun1")
        wf=initial["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,initial["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        # Simulates a crash between G119 durable fixture and G164 artifact storage.
        with closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='RUNNING' WHERE wf_id=?",(wf,))
            db.commit()
            result=run_once(C_GOAL,"run_"+wf[3:],db)
        self.assertEqual(result["status"],"SYNTHETIC_LEDGER_PASS")
        recovered=Backend(self.p).recover(wf)
        self.assertEqual(recovered["status"],"INTERRUPTED_BLOCKED")
        with self.assertRaises(BackendRefused):
            self.b.report(wf)

    def test_legacy_owner_db_schema_must_not_auto_migrate(self):
        workflow=self.b.create(C_GOAL,"req_g164oldschema")["workflow_id"]
        self.b.test(workflow)
        self.b.approve(workflow,self.b.get(workflow)["plan_sha256"],
                       "APPROVE_SYNTHETIC_ONLY")
        with closing(self.b._connect()) as db:
            db.execute("DROP TABLE fp_backend_artifacts")
            db.commit()
        with self.assertRaisesRegex(BackendRefused,"ARTIFACT_SCHEMA_NEEDS_OWNER_MIGRATION"):
            self.b.run(workflow)
        self.assertEqual(Backend(self.p).get(workflow)["status"],"APPROVED_SYNTHETIC")

    def test_real_http_csv_binary_download_and_auth(self):
        wf=self.completed()
        server=create_server(self.b,TOKEN,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def call(auth,origin=None):
            conn=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
            headers={"Host":f"127.0.0.1:{server.server_port}"}
            if auth:headers["Authorization"]="Bearer "+TOKEN
            if origin:headers["Origin"]=origin
            try:
                conn.request("GET",f"/v1/workflows/{wf}/report",headers=headers)
                v=conn.getresponse()
                return v.status,dict(v.getheaders()),v.read()
            finally:conn.close()
        status,headers,body=call(False)
        self.assertEqual(status,403)
        status,headers,body=call(True,"https://attacker.test")
        self.assertEqual(status,403)
        status,headers,body=call(True)
        self.assertEqual(status,200)
        self.assertEqual(headers["Content-Type"],"text/csv; charset=utf-8")
        self.assertIn("attachment;",headers["Content-Disposition"])
        self.assertEqual(headers["X-Flowpilot-Content-SHA256"],sha256(body).hexdigest())
        self.assertEqual(headers["Cache-Control"],"no-store")
        self.assertIn(b"alice,4.00",body)
        self.assertNotIn(b"DEVPOST",body)


if __name__=="__main__":
    unittest.main()
