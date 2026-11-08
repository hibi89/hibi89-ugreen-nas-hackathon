"""G161 true loopback HTTP + persistent SQLite integration, synthetic goals only."""
from __future__ import annotations
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
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

    def test_guide_is_reproducible_readonly_and_bound_to_two_templates(self):
        for index,goal in enumerate((GOAL,"고객별 매출 보고서 만들어줘")):
            with self.subTest(goal=goal):
                record=self.b.create(goal,"req_g178guide"+str(index)+"id")
                wf=record["workflow_id"]
                before=self.b.get(wf)["event_count"]
                guide=self.b.guide(wf)
                self.assertEqual(guide["status"],"SYNTHETIC_OPERATOR_GUIDE_READY_NOT_NAS")
                self.assertEqual(guide["workflow_id"],wf)
                self.assertEqual(guide["plan_sha256"],record["plan_sha256"])
                self.assertEqual(guide["release_gate"],"HOLD")
                self.assertEqual(len(guide["steps"]),7)
                self.assertEqual([x["number"] for x in guide["steps"]],list(range(1,8)))
                self.assertIn("실제 NAS",guide["steps"][-1]["instruction"])
                self.assertFalse(guide["commands_executed"])
                self.assertFalse(guide["owner_files_accessed"])
                self.assertFalse(guide["real_nas_verified"])
                digest=guide.pop("guide_sha256")
                self.assertEqual(digest,api._hash(guide))
                guide["guide_sha256"]=digest
                self.assertEqual(api.Backend(self.db).guide(wf),guide)
                self.assertEqual(self.b.get(wf)["event_count"],before)
                self.assertEqual(guide["workflow_state"],"PLANNED")
                self.assertEqual(guide["verified_local_steps"],2)
                self.assertEqual(guide["steps"][2]["progress"],"NEXT")
                self.assertEqual(guide["steps"][6]["progress"],"OFFICIAL_BLOCKED")
                self.b.test(wf)
                tested=self.b.guide(wf)
                self.assertEqual(tested["workflow_state"],"TESTED")
                self.assertEqual(tested["verified_local_steps"],3)
                self.assertEqual(tested["steps"][3]["progress"],"NEXT")
                self.assertNotEqual(tested["guide_sha256"],guide["guide_sha256"])
                self.assertEqual(tested["guide_sha256"],api._hash(
                    {k:v for k,v in tested.items() if k!="guide_sha256"}))
                self.b.approve(wf,record["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
                approved=self.b.guide(wf)
                self.assertEqual(approved["verified_local_steps"],4)
                self.assertEqual(approved["steps"][4]["progress"],"NEXT")
                self.b.run(wf)
                finished=self.b.guide(wf)
                self.assertEqual(finished["workflow_state"],"COMPLETE_LOCAL_SYNTHETIC")
                self.assertEqual(finished["verified_local_steps"],6)
                self.assertEqual(finished["steps"][6]["progress"],"OFFICIAL_BLOCKED")
                self.assertEqual(finished["next_step_number"],7)
                self.assertEqual(api.Backend(self.db).guide(wf),finished)

    def test_guide_running_never_claims_synthetic_completion(self):
        record=self.b.create(GOAL,"req_g179running111")
        wf=record["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,record["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='RUNNING' WHERE wf_id=?",
                       (wf,))
            self.b._event(db,wf,"RUN_RESERVED")
            db.commit()
        guide=self.b.guide(wf)
        self.assertEqual(guide["workflow_state"],"RUNNING")
        self.assertEqual(guide["verified_local_steps"],4)
        self.assertEqual(guide["steps"][4]["progress"],"RECOVERY_REQUIRED")
        self.assertIn("복구 조회",guide["next_action"])
        self.assertEqual(self.b.get(wf)["status"],"RUNNING")

    def test_guide_uses_completed_report_integrity_gate(self):
        record=self.b.create(GOAL,"req_g179forged11")
        wf=record["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,record["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        with api.closing(self.b._connect()) as db:
            fake=b"phase,required_1,required_2\\r\\ncorrupt,YES,YES\\r\\n"
            db.execute("UPDATE fp_backend_artifacts SET csv_bytes=?, content_sha=? "
                       "WHERE wf_id=?",(fake,api.sha256(fake).hexdigest(),wf))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"REPORT_CANONICAL_FIXTURE_DRIFT"):
            self.b.guide(wf)

    def test_guide_rejects_history_that_disagrees_with_state(self):
        record=self.b.create(GOAL,"req_g179hist11")
        wf=record["workflow_id"]
        # Replacing a mutable status cannot manufacture QA and consent evidence.
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET state='TESTED' WHERE wf_id=?",
                       (wf,))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"GUIDE_EVENT_SEQUENCE_INVALID"):
            self.b.guide(wf)

    def test_guide_blocks_plan_tamper_and_unknown_workflow(self):
        record=self.b.create(GOAL,"req_g178guidebad")
        wf=record["workflow_id"]
        with self.assertRaisesRegex(api.BackendRefused,"WORKFLOW_NOT_FOUND"):
            self.b.guide("wf_"+"f"*32)
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET plan_sha=? WHERE wf_id=?",
                       ("0"*64,wf))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"GUIDE_PLAN_DRIFT"):
            self.b.guide(wf)

    def test_no_owner_file_touch_before_or_after_plan(self):
        w=self.b.create(GOAL,"req_abcdefgh1234")
        self.assertEqual(w["status"],"PLANNED")
        self.assertFalse(w["nas_verified"])
        self.assertFalse(w["owner_files_accessed"])
        self.assertEqual(w["release_gate"],"HOLD")
        self.assertEqual(w["event_count"],1)

    def test_g247_version_cli_cannot_create_unrunnable_dashboard_workflow(self):
        for index, goal in enumerate(("review versions", "버전 비교해줘")):
            with self.subTest(goal=goal):
                with self.assertRaisesRegex(api.BackendRefused, "UNSUPPORTED_GOAL"):
                    self.b.create(goal,"req_g247unsupported"+str(index))
        with api.closing(self.b._connect()) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM fp_backend_workflows")
                             .fetchone()[0],0)
        self.assertEqual(self.b.list()["workflows"],[])

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

    def test_g281_windows_reparse_db_entry_denied_before_sqlite_open(self):
        # Synthetic Windows FILE_ATTRIBUTE_REPARSE_POINT on a regular-looking
        # database must not bypass a POSIX-only is_symlink() check.
        actual_lstat = Path.lstat
        def marked_lstat(path, *args, **kwargs):
            original = actual_lstat(path, *args, **kwargs)
            if path == self.db:
                return SimpleNamespace(
                    st_mode=original.st_mode, st_file_attributes=0x400,
                    st_size=original.st_size, st_nlink=original.st_nlink)
            return original
        with patch.object(Path, "lstat", marked_lstat):
            with self.assertRaisesRegex(api.BackendRefused, "DB_PATH_DENIED"):
                api.Backend(self.db)
        self.assertTrue(self.db.is_file())

    def test_g281_windows_junction_parent_denies_existing_db_and_reconnect(self):
        actual_lstat = Path.lstat
        def marked_lstat(path, *args, **kwargs):
            original = actual_lstat(path, *args, **kwargs)
            if path == self.db.parent:
                return SimpleNamespace(
                    st_mode=original.st_mode, st_file_attributes=0x400)
            return original
        with patch.object(Path, "lstat", marked_lstat):
            with self.assertRaisesRegex(api.BackendRefused, "DB_PATH_DENIED"):
                api.Backend(self.db)
            with self.assertRaisesRegex(api.BackendRefused, "DB_PATH_DENIED"):
                self.b.get("wf_" + "0"*32)
        self.assertTrue(self.db.is_file())

    def test_g281_windows_junction_parent_denies_new_db_creation(self):
        newdb = self.db.parent / "uncreated.sqlite"
        actual_lstat = Path.lstat
        def marked_lstat(path, *args, **kwargs):
            original = actual_lstat(path, *args, **kwargs)
            if path == self.db.parent:
                return SimpleNamespace(
                    st_mode=original.st_mode, st_file_attributes=0x400)
            return original
        with patch.object(Path, "lstat", marked_lstat):
            with self.assertRaisesRegex(api.BackendRefused, "DB_PATH_DENIED"):
                api.Backend(newdb, create=True)
        self.assertFalse(newdb.exists())

    def test_g281_actual_symlink_directory_denied(self):
        parent_alias = self.db.parent / "folder-alias"
        try:
            parent_alias.symlink_to(self.db.parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlink privilege unavailable")
        with self.assertRaisesRegex(api.BackendRefused, "DB_PATH_DENIED"):
            api.Backend(parent_alias / self.db.name)
        self.assertTrue(self.db.is_file())

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
        self.assertEqual(call("GET","/v1/workflows")[1]["count"],1)
        self.assertEqual(call("GET",path+"/plan")[1]["plan"]["schema"],
                         "flowpilot-typed-workflow-v1")
        self.assertEqual(call("GET",path+"/guide",auth=False)[0],403)
        self.assertEqual(call("GET",path+"/guide",
                              headers={"Origin":"https://evil.test"})[0],403)
        guide_code,guide=call("GET",path+"/guide")
        self.assertEqual(guide_code,200)
        self.assertEqual(guide["plan_sha256"],record["plan_sha256"])
        self.assertEqual(len(guide["steps"]),7)
        self.assertEqual(guide["workflow_state"],"COMPLETE_LOCAL_SYNTHETIC")
        self.assertEqual(guide["verified_local_steps"],6)
        self.assertEqual(guide["next_step_number"],7)
        self.assertEqual(guide["steps"][6]["progress"],"OFFICIAL_BLOCKED")
        self.assertFalse(guide["real_nas_verified"])
        self.assertEqual(guide["guide_sha256"],
                         api._hash({k:v for k,v in guide.items() if k!="guide_sha256"}))
        self.assertEqual(call("GET",path+"/audit")[1]["execution_evidence_integrity"],
                         "LOCAL_CHAIN_INTACT")
        http_code, evidence=call("GET",path+"/evidence")
        self.assertEqual(http_code,200)
        self.assertEqual(evidence["status"],"LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS")
        self.assertFalse(evidence["registered_expert_invoked"])
        self.assertEqual(call("POST","/v1/advice",{"telemetry":{"disk_used_percent":96},
                                                "opt_in":True})[1]["status"],
                         "SUGGESTIONS_READY")
        self.assertEqual(call("POST",path+"/recover",{"unexpected":1})[0],400)
        self.assertEqual(call("POST",path+"/run",{},headers={"Origin":"https://evil.test"})[0],403)
        self.assertEqual(call("POST",path+"/run",{},headers={"Transfer-Encoding":"chunked"})[0],400)

    def test_dashboard_read_only_list_plan_and_audit(self):
        first=self.b.create(GOAL,"req_first12345678")
        second=self.b.create("고객별 매출 보고서 만들어줘","req_second1234567")
        listing=self.b.list()
        self.assertEqual(listing["count"],2)
        self.assertEqual(listing["workflows"],[second["workflow_id"],first["workflow_id"]])
        self.assertEqual(self.b.plan(first["workflow_id"])["plan"]["status"],"READY_FOR_SYNTHETIC_TEST")
        before=self.b.audit(first["workflow_id"])
        self.assertEqual(before["execution_evidence_integrity"],"NO_SYNTHETIC_RUN")
        self.b.test(first["workflow_id"])
        self.b.approve(first["workflow_id"],first["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(first["workflow_id"])
        self.assertEqual(self.b.audit(first["workflow_id"])["execution_evidence_integrity"],
                         "LOCAL_CHAIN_INTACT")
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET plan_sha='0' WHERE wf_id=?",
                       (first["workflow_id"],))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"PLAN_HASH_DRIFT"):
            self.b.plan(first["workflow_id"])

    def test_proactive_signal_requires_opt_in_and_never_mutates(self):
        self.assertEqual(self.b.advice({"disk_used_percent":95},opt_in=False)["status"],
                         "DISABLED_NO_CONSENT")
        result=self.b.advice({"disk_used_percent":95},opt_in=True)
        self.assertEqual(result["suggestions"][0]["status"],"PROPOSAL_ONLY")
        self.assertFalse(result["actions_executed"])
        with self.assertRaisesRegex(api.BackendRefused,"ADVICE_TELEMETRY_INVALID"):
            self.b.advice({"owner_private_path":"secret"},opt_in=True)

    def test_advice_is_operator_sample_only_and_db_unchanged(self):
        self.b.create(GOAL,"req_g180noside1")
        before=self.b.list()
        off=self.b.advice({"disk_used_percent":95},opt_in=False)
        self.assertEqual(off["status"],"DISABLED_NO_CONSENT")
        self.assertFalse(off["actions_executed"])
        high=self.b.advice({"disk_used_percent":95,
                            "repeated_error_count":3,
                            "backup_age_hours":73},opt_in=True)
        self.assertEqual(high["status"],"SUGGESTIONS_READY")
        self.assertEqual(high["suggestion_count"],3)
        self.assertEqual({p["status"] for p in high["suggestions"]},{"PROPOSAL_ONLY"})
        self.assertEqual(high["source"],"UNVERIFIED_OPERATOR_SUPPLIED_METRICS")
        self.assertFalse(high["nas_polled"])
        self.assertFalse(high["background_service_started"])
        self.assertFalse(high["external_notifications_sent"])
        low=self.b.advice({"disk_used_percent":20},opt_in=True)
        self.assertEqual(low["status"],"NO_ALERTS_IN_SUPPLIED_DATA")
        self.assertEqual(len(low["missing_inputs_not_checked"]),2)
        self.assertEqual(self.b.list(),before)
        with self.assertRaisesRegex(api.BackendRefused,"ADVICE_TELEMETRY_INVALID"):
            self.b.advice({"disk_used_percent":101},opt_in=True)

    def test_g163_complete_receipt_export_uses_real_g119_sqlite(self):
        w=self.b.create(GOAL,"req_export12345678")
        wf=w["workflow_id"]
        with self.assertRaisesRegex(api.BackendRefused,"EVIDENCE_REQUIRES_COMPLETED"):
            self.b.evidence(wf)
        self.b.test(wf)
        self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        report=self.b.evidence(wf)
        self.assertEqual(report["status"],"LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS")
        self.assertEqual(report["receipt_sha256"],self.b.get(wf)["receipt_sha256"])
        self.assertTrue(report["approval_proven_in_local_chain"])
        self.assertEqual({v["role"] for v in report["review_stages"]},
                         {"Architect","Security","Builder","QA"})
        self.assertFalse(report["customer_files_read"])
        self.assertFalse(report["real_nas_verified"])
        self.assertEqual(report["release_gate"],"HOLD")
        self.assertEqual(self.b.evidence(wf),report)
        self.assertEqual(self.b.get(wf)["event_count"],5)
        self.assertEqual(api._hash({k:v for k,v in report.items() if k!="report_sha256"}),
                         report["report_sha256"])

    def test_g163_forged_backend_receipt_fails_audit_and_export(self):
        w=self.b.create(GOAL,"req_forge12345678")
        wf=w["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_workflows SET receipt_sha=? WHERE wf_id=?",
                       ("f"*64,wf))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"LEDGER_RECEIPT_MISMATCH"):
            self.b.audit(wf)
        with self.assertRaisesRegex(api.BackendRefused,"G119_RECEIPT_MISMATCH"):
            self.b.evidence(wf)

    def test_g163_forged_approval_history_refused(self):
        w=self.b.create(GOAL,"req_approvalhist12")
        wf=w["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp_backend_events SET kind='APPROVED_REAL_NAS' "
                       "WHERE wf_id=? AND kind='SYNTHETIC_ONLY_APPROVED'",(wf,))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"EVENT_CHAIN_INVALID"):
            self.b.evidence(wf)

    def test_g163_tampered_g119_event_refuses_export(self):
        w=self.b.create(GOAL,"req_ledgerfake1234")
        wf=w["workflow_id"]
        self.b.test(wf)
        self.b.approve(wf,w["plan_sha256"],"APPROVE_SYNTHETIC_ONLY")
        self.b.run(wf)
        with api.closing(self.b._connect()) as db:
            db.execute("UPDATE fp119_events SET detail=? WHERE run_id=? AND kind='ROLE'",
                       ('{"role":"QA","status":"PASS"}',"run_"+wf[3:]))
            db.commit()
        with self.assertRaisesRegex(api.BackendRefused,"G119_RECEIPT_MISMATCH"):
            self.b.evidence(wf)

    def test_no_network_or_nas_backend_dependency(self):
        text=Path(api.__file__).read_text(encoding="utf-8")
        for word in ("requests.post(", "urllib.request", "docker run", "NAS SSH", "Devpost API"):
            self.assertNotIn(word,text)


if __name__=="__main__":
    unittest.main()
