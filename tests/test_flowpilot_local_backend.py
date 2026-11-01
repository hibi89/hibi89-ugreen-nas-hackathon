"""G161 true loopback HTTP + persistent SQLite integration, synthetic goals only."""
from __future__ import annotations
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import flowpilot_local_backend as api

GOAL="check required files"
TOKEN="t"*48


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/"flowpilot.sqlite"
        self.b=api.Backend(self.db,create=True)

    def test_no_owner_file_touch_before_or_after_plan(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        self.assertEqual(w["status"],"PLANNED")
        self.assertFalse(w["nas_verified"])
        self.assertFalse(w["owner_files_accessed"])
        self.assertEqual(w["release_gate"],"HOLD")
        self.assertEqual(w["event_count"],1)

    def test_idempotent_create_and_same_key_conflict(self):
        a=self.b.create(GOAL,"req_abcdefgh1234")
        b=self.b.create(GOAL,"req_abcdefgh1234")
        self.assertEqual(a["workflow_id"],b["workflow_id"])
        self.assertEqual(b["event_count"],1)
        with self.assertRaisesRegex(api.BackendRefused,"IDEMPOTENCY_KEY_CONFLICT"):
            self.b.create("고객별 매출 보고서 만들어줘","req_abcdefgh1234")

    def test_unsupported_goal_never_stored(self):
        with self.assertRaisesRegex(api.BackendRefused,"UNSUPPORTED_GOAL"):
            self.b.create("delete all nas files","req_abcdefgh1234")
        with api.closing(self.b._connect()) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM fp_backend_workflows").fetchone()[0],0)

    def test_real_synthetic_council_approval_run_idempotent(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        wf=w["workflow_id"]
        with self.assertRaisesRegex(api.BackendRefused,"APPROVAL_STATE_CONFLICT"):
            self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        tested=self.b.test(wf)
        self.assertEqual(tested["status"],"TESTED")
        self.assertEqual(self.b.test(wf)["event_count"],2)
        with self.assertRaisesRegex(api.BackendRefused,"EXACT_SYNTHETIC_APPROVAL_REQUIRED"):
            self.b.approve(wf,w["plan_sha256"],"APPROVE_REAL_NAS")
        self.assertEqual(self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")["status"],
                         "APPROVED_SYNTHETIC")
        done=self.b.run(wf)
        self.assertEqual(done["status"],"COMPLETE_LOCAL_SYNTHETIC")
        self.assertEqual(done["event_count"],5)
        self.assertEqual(self.b.run(wf)["event_count"],5)
        self.assertFalse(done["production_applied"])
        with api.closing(self.b._connect()) as db:
            evidence=api.verify_record(db,"run_"+wf[3:])
            self.assertEqual(evidence["status"],"LOCAL_CHAIN_INTACT")

    def test_restart_readback_persists(self):
        first=self.b.create(GOAL,"req_restart12345")
        restored=api.Backend(self.db)
        self.assertEqual(restored.get(first["workflow_id"])["status"],"PLANNED")
        with self.assertRaisesRegex(api.BackendRefused,"DB_EXISTS_NO_OVERWRITE"):
            api.Backend(self.db,create=True)

    def test_unknown_existing_db_refused(self):
        bad=Path(self.temp.name)/"bad.sqlite"
        bad.write_bytes(b"not a database")
        with self.assertRaises(api.BackendRefused):
            api.Backend(bad)

    def test_approval_wrong_plan_sha_denied(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        self.b.test(w["workflow_id"])
        with self.assertRaisesRegex(api.BackendRefused,"EXACT_SYNTHETIC_APPROVAL_REQUIRED"):
            self.b.approve(w["workflow_id"],"0"*64,"APPROVE_SYNTHETIC_ONLY")

    def test_evidence_chain_tampering_refused(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_events SET kind='FAKE' WHERE wf_id=?",
                       (w["workflow_id"],))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"EVENT_CHAIN_INVALID"):
            self.b.get(w["workflow_id"])

    def test_interrupted_run_reconcile_fails_closed(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        self.b.test(w["workflow_id"])
        self.b.approve(w["workflow_id"],w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='RUNNING' WHERE wf_id=?",
                       (w["workflow_id"],))
            db.commit()
        fixed=self.b.recover(w["workflow_id"])
        self.assertEqual(fixed["status"],"INTERRUPTED_BLOCKED")
        with self.assertRaisesRegex(api.BackendRefused,"RUN_STATE_CONFLICT"):
            self.b.run(w["workflow_id"])

    def test_symlink_database_path_refused(self):
        link=Path(self.temp.name)/"alias.sqlite"
        try:link.symlink_to(self.db)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(api.BackendRefused,"DB_PATH_DENIED"):
            api.Backend(link)

    def test_requires_explicit_token(self):
        with self.assertRaisesRegex(api.BackendRefused,"TOKEN_MUST"):
            api.create_server(self.b,"short")

    def test_live_loopback_http_authorization_and_flow(self):
        server=api.create_server(self.b,TOKEN,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def call(method,path,body=None,auth=True,headers=None):
            h={"Host":f"127.0.0.1:{server.server_port}"}
            if auth:h["Authorization"]="Bearer "+TOKEN
            if body is not None:
                h["Content-Type"]="application/json"
                raw=json.dumps(body).encode()
            else:raw=None
            h.update(headers or {})
            c=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
            try:
                c.request(method,path,body=raw,headers=h)
                v=c.getresponse();parsed=json.loads(v.read());return v.status,parsed
            finally:c.close()
        self.assertEqual(call("GET","/v1/health",auth=False)[0],403)
        self.assertEqual(call("GET","/v1/health",headers={"Host":"evil.test"})[0],403)
        self.assertEqual(call("GET","/v1/health")[0],200)
        status,record=call("POST","/v1/workflows",
                           {"goal":GOAL,"request_id":"req_http123456"})
        self.assertEqual(status,200)
        path="/v1/workflows/"+record["workflow_id"]
        self.assertEqual(call("POST",path+"/run",{})[0],409)
        self.assertEqual(call("POST",path+"/test",{})[1]["status"],"TESTED")
        self.assertEqual(call("POST",path+"/approve",{
            "plan_sha256":record["plan_sha256"],
            "acknowledgement":"APPROVE_SYNTHETIC_ONLY"})[1]["status"],"APPROVED_SYNTHETIC")
        self.assertEqual(call("POST",path+"/run",{})[1]["status"],"COMPLETE_LOCAL_SYNTHETIC")
        self.assertEqual(call("GET",path)[1]["release_gate"],"HOLD")
        self.assertEqual(call("POST",path+"/recover",{"unexpected":1})[0],400)
        self.assertEqual(call("POST",path+"/run",{},headers={"Origin":"https://evil.test"})[0],403)
        self.assertEqual(call("POST",path+"/run",{},headers={"Transfer-Encoding":"chunked"})[0],400)

    def test_no_network_or_nas_backend_dependency(self):
        text=Path(api.__file__).read_text()
        for word in ("requests.post(", "urllib.request", "docker run", "NAS SSH", "Devpost API"):
            self.assertNotIn(word,text)


if __name__=="__main__":
    unittest.main()
