"""G239 authentic local HTTP + once-only redacted companion SQLite receipts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from contextlib import closing
import http.client
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_local_backend import Backend, create_server
from flowpilot_g238_local_csv_engine import READ_ACK

TOKEN = "g239" * 12
CSV = b"customer,amount_cents\nalice,125\nbob,300\nalice,275\n"


class G239CsvGatewayTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.db=self.root/"source.sqlite"
        self.csv=self.root/"private-owner-test.csv"
        self.csv.write_bytes(CSV)
        self.backend=Backend(self.db,create=True)
        self.sidecar=self.root/"source-csv-g239.sqlite"
        self.server=create_server(self.backend,TOKEN)
        self.addCleanup(self.server.server_close)
        t=threading.Thread(target=self.server.serve_forever,daemon=True)
        t.start()
        self.addCleanup(self.server.shutdown)

    def call(self,route,body=None,auth=True,method=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=5)
        try:
            headers={"Host":f"127.0.0.1:{self.server.server_port}"}
            if auth: headers["Authorization"]="Bearer "+TOKEN
            method=method or ("POST" if body is not None else "GET")
            if body is not None:headers["Content-Type"]="application/json"
            conn.request(method,route,json.dumps(body) if body is not None else None,
                         headers)
            res=conn.getresponse()
            return res.status,json.loads(res.read())
        finally:
            conn.close()

    def preview(self):
        code,data=self.call("/v1/local-csv/preview",
                            {"input_path":str(self.csv),"group_column":"customer"})
        self.assertEqual(code,200,data)
        self.assertEqual(data["status"],"WAITING_EXPLICIT_LOCAL_CSV_JOB_APPROVAL")
        return data

    def run_once(self,plan,job="csv_"+"a"*24,approval=READ_ACK):
        return self.call("/v1/local-csv/run", {
            "preview_id":plan["preview_id"],
            "plan_sha256":plan["plan_sha256"],
            "request_id":job,"acknowledgement":approval})


    def test_g244_owner_approved_create_only_full_report(self):
        plan=self.preview()
        target=self.root/"new-aggregate.csv"
        body={"preview_id":plan["preview_id"],"request_id":"csv_"+"9"*24,
              "plan_sha256":plan["plan_sha256"],"acknowledgement":READ_ACK,
              "export_to":str(target),
              "export_approval":"APPROVE_LOCAL_REPORT_CREATE"}
        status,receipt=self.call("/v1/local-csv/run",body)
        self.assertEqual(status,200,receipt)
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_bytes(),
                         b"customer,total_cents,source_rows\n"
                         b"alice,400,2\nbob,300,1\n")
        self.assertEqual(target.stat().st_size,len(target.read_bytes()))
        self.assertEqual(sha256(target.read_bytes()).hexdigest(),
                         receipt["result"]["report_sha256"])
        self.assertIs(receipt["result"]["report_file_created"],True)
        self.assertEqual(receipt["result"]["owner_source_modified"],False)
        self.assertEqual(self.csv.read_bytes(),CSV)
        self.assertNotIn(str(target),json.dumps(receipt))
        self.assertNotIn(str(target),self.sidecar.read_bytes().decode())
        self.assertNotIn("alice",self.sidecar.read_bytes().decode())
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("duplicate report create")):
            self.assertEqual(self.call("/v1/local-csv/jobs/"+body["request_id"]),
                             (200,receipt))
            self.assertEqual(self.call("/v1/local-csv/run",body)[0],409)
        self.assertEqual(len(list(self.root.glob("new-aggregate.csv"))),1)

    def test_g244_create_without_distinct_ack_refused_before_input_read(self):
        p=self.preview()
        target=self.root/"not-created.csv"
        common={"preview_id":p["preview_id"],"request_id":"csv_"+"8"*24,
                "plan_sha256":p["plan_sha256"],"acknowledgement":READ_ACK}
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("no source read")), \
             patch("flowpilot_g239_csv_jobs.LocalCsvJobs._initialize_only_on_approval",
                   side_effect=AssertionError("no SQLite create")):
            self.assertEqual(self.call("/v1/local-csv/run",
                             {**common,"export_to":str(target)})[0],400)
            self.assertEqual(self.call("/v1/local-csv/run",
                             {**common,"export_to":str(target),
                              "export_approval":"wrong"})[0],403)
            self.assertEqual(self.call("/v1/local-csv/run",
                             {**common,"export_to":str(target.with_suffix(".txt")),
                              "export_approval":"APPROVE_LOCAL_REPORT_CREATE"})[0],403)
        self.assertFalse(target.exists())
        self.assertFalse(self.sidecar.exists())

    def test_g244_existing_destination_is_never_overwritten(self):
        p=self.preview()
        target=self.root/"existing-report.csv"
        target.write_bytes(b"preserve bytes")
        body={"preview_id":p["preview_id"],"request_id":"csv_"+"7"*24,
              "plan_sha256":p["plan_sha256"],"acknowledgement":READ_ACK,
              "export_to":str(target),
              "export_approval":"APPROVE_LOCAL_REPORT_CREATE"}
        self.assertEqual(self.call("/v1/local-csv/run",body)[0],409)
        self.assertEqual(target.read_bytes(),b"preserve bytes")
        self.assertEqual(self.csv.read_bytes(),CSV)
        status,receipt=self.call("/v1/local-csv/jobs/"+body["request_id"])
        self.assertEqual(status,200)
        self.assertEqual(receipt["status"],"LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY")
        self.assertEqual(self.call("/v1/local-csv/run",body)[0],409)

    def test_g243_empty_history_is_opt_in_and_never_creates_db(self):
        self.assertEqual(self.call("/v1/local-csv/jobs")[0],403)
        self.assertEqual(self.call("/v1/local-csv/jobs",auth=False)[0],403)
        self.assertFalse(self.sidecar.exists())
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("history must not read source")):
            status,data=self.call_history()
        self.assertEqual(status,200)
        self.assertEqual(data["schema"],"flowpilot-g243-csv-history-v1")
        self.assertEqual(data["jobs"],[])
        self.assertEqual(data["max_returned"],10)
        self.assertEqual(data["source_files_accessed"],False)
        self.assertFalse(self.sidecar.exists())

    def call_history(self, *, token=TOKEN):
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=5)
        try:
            conn.request("GET","/v1/local-csv/jobs",headers={
                "Host":f"127.0.0.1:{self.server.server_port}",
                "Authorization":"Bearer "+token,
                "X-Local-Receipt-Review":"APPROVE_LOCAL_CSV_HISTORY_READ_ONCE",
            })
            res=conn.getresponse()
            return res.status,json.loads(res.read())
        finally:
            conn.close()

    def test_g243_recent_history_is_bounded_and_redacted(self):
        source=self.csv.read_bytes()
        for i in range(12):
            plan=self.preview()
            job="csv_"+format(i,"024x")
            self.assertEqual(self.run_once(plan,job)[0],200)
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("history source re-opened")):
            status,data=self.call_history()
        self.assertEqual(status,200)
        self.assertEqual(data["count"],10)
        self.assertEqual(len(data["jobs"]),10)
        self.assertEqual(data["jobs"][0]["request_id"],"csv_"+format(11,"024x"))
        self.assertEqual(data["jobs"][-1]["request_id"],"csv_"+format(2,"024x"))
        self.assertTrue(all(x["group_count"]==2 and x["source_rows"]==3
                            for x in data["jobs"]))
        self.assertEqual(self.csv.read_bytes(),source)
        for private in (str(self.csv),"alice","bob","private-owner-test.csv"):
            self.assertNotIn(private,json.dumps(data))
        self.assertEqual(data["nas_verified"],False)

    def test_g243_history_tampered_receipt_fails_closed(self):
        plan=self.preview()
        self.assertEqual(self.run_once(plan,"csv_"+"b"*24)[0],200)
        with closing(sqlite3.connect(self.sidecar)) as db:
            db.execute("UPDATE g239_jobs SET receipt_sha=?",("0"*64,))
            db.commit()
        status,result=self.call_history()
        self.assertEqual(status,409)
        self.assertNotIn("jobs",result)

    def test_g243_history_includes_blocked_without_retry(self):
        plan=self.preview()
        self.csv.write_bytes(b"customer,amount_cents\nalice,3O0\n")
        job="csv_"+"f"*24
        self.assertEqual(self.run_once(plan,job)[0],409)
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("blocked job rerun")):
            status,data=self.call_history()
        self.assertEqual(status,200)
        self.assertEqual(data["jobs"],[
            {"request_id":job,"status":"LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY"}
        ])

    def test_auth_and_preview_no_owner_file_read_or_disk_write(self):
        self.assertEqual(self.call("/v1/local-csv/preview",
            {"input_path":str(self.csv),"group_column":"customer"},auth=False)[0],403)
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("execution before consent")):
            x=self.preview()
        self.assertFalse(self.sidecar.exists())
        self.assertNotIn(str(self.csv),json.dumps(x))
        self.assertNotIn("alice",json.dumps(x))
        self.assertFalse(x["input_file_touched"])

    def test_exact_one_approved_execution_and_restart_readback(self):
        p=self.preview()
        job="csv_"+"b"*24
        status,created=self.run_once(p,job)
        self.assertEqual(status,200,created)
        self.assertEqual(created["result"]["source_rows"],3)
        self.assertEqual([r["total_cents"] for r in
                          created["result"]["redacted_group_totals"]],[400,300])
        self.assertTrue(self.sidecar.is_file())
        self.assertEqual(self.csv.read_bytes(),CSV)
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("source reread")):
            self.assertEqual(self.run_once(p,job),(200,created))
            self.assertEqual(self.call("/v1/local-csv/jobs/"+job),(200,created))
            reopened=Backend(self.db,create=False)
            self.assertEqual(reopened.csv_jobs.readback(job),created)
        with closing(sqlite3.connect(self.sidecar)) as db:
            row=db.execute("SELECT state,receipt_json FROM g239_jobs").fetchone()
        self.assertEqual(row[0],"COMPLETE")
        for secret in ("private-owner-test.csv","alice","bob",str(self.csv)):
            self.assertNotIn(secret,self.sidecar.read_bytes().decode("utf-8","ignore"))
            self.assertNotIn(secret,json.dumps(created))
        self.assertEqual(row[1],json.dumps(created,sort_keys=True,
                            separators=(",",":"),ensure_ascii=True))

    def test_no_approval_no_db_and_no_read(self):
        p=self.preview()
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("source read")), \
             patch("flowpilot_g239_csv_jobs.LocalCsvJobs._initialize_only_on_approval",
                   side_effect=AssertionError("sidecar created")):
            self.assertEqual(self.run_once(p,approval="yes")[0],403)
            self.assertEqual(self.run_once({**p,"plan_sha256":"0"*64})[0],403)
        self.assertFalse(self.sidecar.exists())

    def test_concurrent_duplicate_only_reads_once(self):
        p=self.preview()
        calls=[0]
        from flowpilot_g239_csv_jobs import execute
        def counted(*a,**kw):
            calls[0]+=1
            return execute(*a,**kw)
        with patch("flowpilot_g239_csv_jobs.execute",side_effect=counted):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _ : self.run_once(p,"csv_"+"c"*24),
                                      range(2)))
        self.assertEqual([r[0] for r in results],[200,200])
        self.assertEqual(results[0][1],results[1][1])
        self.assertEqual(calls[0],1)

    def test_failed_source_read_never_auto_retries(self):
        p=self.preview()
        self.csv.write_bytes(b"customer,amount_cents\nalice,3O0\n")
        job="csv_"+"d"*24
        self.assertEqual(self.run_once(p,job)[0],409)
        s,blocked=self.call("/v1/local-csv/jobs/"+job)
        self.assertEqual(s,200)
        self.assertEqual(blocked["status"],"LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY")
        self.csv.write_bytes(CSV)
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("retry executed")):
            self.assertEqual(self.run_once(p,job),(200,blocked))
        self.assertEqual(self.csv.read_bytes(),CSV)

    def test_crash_reserved_state_fails_closed_after_restart(self):
        p=self.preview()
        store=self.backend.csv_jobs
        store._initialize_only_on_approval()
        job="csv_"+"e"*24
        with closing(store._connect()) as db:
            db.execute("INSERT INTO g239_jobs VALUES(?,?,'RESERVED',NULL,NULL)",
                       (job,p["plan_sha256"]))
            db.commit()
        reopened=Backend(self.db,create=False)
        self.assertEqual(reopened.csv_jobs.readback(job)["status"],
                         "RUN_RESERVED_UNCERTAIN_NO_AUTORETRY")
        with patch("flowpilot_g239_csv_jobs.execute",
                   side_effect=AssertionError("restarted run")):
            self.assertEqual(reopened.csv_jobs.run(p["preview_id"],job,
                p["plan_sha256"],READ_ACK)["status"],
                "RUN_RESERVED_UNCERTAIN_NO_AUTORETRY")

    def test_id_conflict_and_corrupted_proof_denied(self):
        p=self.preview()
        job="csv_"+"f"*24
        self.assertEqual(self.run_once(p,job)[0],200)
        self.assertEqual(self.run_once({**p,"plan_sha256":"a"*64},job)[0],409)
        with closing(sqlite3.connect(self.sidecar)) as db:
            db.execute("UPDATE g239_jobs SET receipt_sha=?",("0"*64,))
            db.commit()
        self.assertEqual(self.call("/v1/local-csv/jobs/"+job)[0],409)
        self.assertEqual(self.run_once(p,job)[0],409)

    def test_host_query_and_post_unknown_route_blocked(self):
        p=self.preview()
        job="csv_"+"a"*24
        self.assertEqual(self.call("/v1/local-csv/jobs/"+job+"?execute=1")[0],404)
        self.assertEqual(self.call("/v1/local-csv/jobs/"+job,
                                   {"anything":True})[0],404)
        self.assertEqual(self.call("/v1/local-csv/run",
                                   {"plan_sha256":p["plan_sha256"]})[0],400)

    def test_sqlite_original_database_tables_remain_untouched(self):
        self.run_once(self.preview())
        with closing(sqlite3.connect(self.db)) as db:
            rows={x[0] for x in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertFalse(any("g239" in x for x in rows))

    def test_expired_ticket_cannot_be_reused(self):
        p=self.preview()
        old=self.backend.csv_jobs.tickets[p["preview_id"]]
        self.backend.csv_jobs.tickets[p["preview_id"]]=(
            *old[:3],0.0)
        self.assertEqual(self.run_once(p)[0],403)
        self.assertFalse(self.sidecar.exists())


if __name__=="__main__":
    unittest.main()
