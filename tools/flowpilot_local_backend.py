"""G161 FlowPilot 3.0 LOCAL backend: persisted plan -> council -> approval -> synthetic run.

Not Uliya, NAS, production automation, external API or general-purpose NLU.
All owner-facing inputs are exact allowlisted goals; no owner file paths accepted.
Only explicit local database creation is permitted. No vendor execution/network.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import threading

from flowpilot_task_compiler import compile_goal
from flowpilot_code_council import run_council
from flowpilot_repair_ledger import run_once, verify_record
from flowpilot_proactive_advisor import advise_local
from flowpilot_g164_report_artifact import fixture_csv, ArtifactRefused, CANONICAL_CSV
from flowpilot_g165_local_metadata_api import MetadataGate, MetadataRefused

SCHEMA = "flowpilot-backend-local-v1"
IDENTITY = "flowpilot-g161-owner-created-backend-v1"
REQ = re.compile(r"req_[A-Za-z0-9_-]{8,48}\Z")
WF = re.compile(r"wf_[0-9a-f]{32}\Z")
MAX_BODY = 2048
MAX_DB_BYTES = 16 * 1024 * 1024
_ALLOWED_STATES = frozenset(("PLANNED", "TESTED", "APPROVED_SYNTHETIC",
                             "RUNNING", "COMPLETE_LOCAL_SYNTHETIC", "BLOCKED",
                             "INTERRUPTED_BLOCKED"))


class BackendRefused(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code = code
        self.status = status
        super().__init__(code)


def _hash(data: object) -> str:
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")).hexdigest()


def _path_gate(path: Path, *, create: bool) -> None:
    if (not isinstance(path, Path) or not path.is_absolute() or
            path.suffix != ".sqlite" or not path.parent.is_dir() or
            str(path).startswith(("//", "\\\\")) or path.is_symlink() or
            any(p.is_symlink() for p in (path.parent, *path.parent.parents))):
        raise BackendRefused("DB_PATH_DENIED", 400)
    if create and path.exists():
        raise BackendRefused("DB_EXISTS_NO_OVERWRITE", 409)
    if not create:
        try:
            s = path.stat()
            if (not stat.S_ISREG(s.st_mode) or not 0 <= s.st_size < MAX_DB_BYTES or
                    (os.name != "nt" and s.st_nlink != 1)):
                raise BackendRefused("DB_NOT_OWNED_OR_OVERSIZED")
        except OSError as exc:
            raise BackendRefused("DB_NOT_FOUND") from exc


class Backend:
    def __init__(self, path: Path, *, create: bool = False,
                 metadata_root: Path | None = None):
        _path_gate(path, create=create)
        self.path = path
        self.lock = threading.RLock()
        self.metadata = MetadataGate(metadata_root)
        if create:
            flags = os.O_CREAT | os.O_EXCL | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            try:
                fd = os.open(path, flags, 0o600)
                os.close(fd)
            except OSError as exc:
                raise BackendRefused("DB_EXCLUSIVE_CREATE_FAILED") from exc
            with closing(self._connect()) as db:
                db.execute("CREATE TABLE fp_backend_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("INSERT INTO fp_backend_meta VALUES('identity',?)", (IDENTITY,))
                db.execute("CREATE TABLE fp_backend_workflows ("
                           "wf_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,"
                           "goal TEXT NOT NULL, template TEXT NOT NULL, plan_sha TEXT NOT NULL,"
                           "state TEXT NOT NULL, receipt_sha TEXT)")
                db.execute("CREATE TABLE fp_backend_events (wf_id TEXT NOT NULL, "
                           "seq INTEGER NOT NULL, kind TEXT NOT NULL, "
                           "previous_sha TEXT NOT NULL, event_sha TEXT NOT NULL,"
                           "PRIMARY KEY(wf_id, seq))")
                db.execute("CREATE TABLE fp_backend_artifacts ("
                           "wf_id TEXT PRIMARY KEY, template TEXT NOT NULL, "
                           "receipt_sha TEXT NOT NULL, content_sha TEXT NOT NULL,"
                           "csv_bytes BLOB NOT NULL)")
                db.commit()  # closing() never implicitly commits transactions.
        with closing(self._connect()) as db:
            try:
                if db.execute("SELECT value FROM fp_backend_meta WHERE key='identity'").fetchone() != (IDENTITY,):
                    raise BackendRefused("DB_IDENTITY_MISMATCH")
            except sqlite3.Error as exc:
                raise BackendRefused("DB_IDENTITY_MISSING") from exc

    def _connect(self):
        _path_gate(self.path, create=False)
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=3)
        db.execute("PRAGMA busy_timeout=3000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _event(db, wf_id: str, kind: str):
        row = db.execute("SELECT seq,event_sha FROM fp_backend_events WHERE wf_id=? "
                         "ORDER BY seq DESC LIMIT 1", (wf_id,)).fetchone()
        seq, prev = (row[0]+1, row[1]) if row else (1, "0"*64)
        digest = _hash({"wf_id":wf_id, "seq":seq, "kind":kind, "previous_sha":prev})
        db.execute("INSERT INTO fp_backend_events VALUES (?,?,?,?,?)",
                   (wf_id, seq, kind, prev, digest))

    @staticmethod
    def _row(db, wf_id):
        if not isinstance(wf_id, str) or WF.fullmatch(wf_id) is None:
            raise BackendRefused("WORKFLOW_ID_INVALID", 400)
        row = db.execute("SELECT wf_id, request_id, goal, template, plan_sha, state, receipt_sha "
                         "FROM fp_backend_workflows WHERE wf_id=?", (wf_id,)).fetchone()
        if row is None:
            raise BackendRefused("WORKFLOW_NOT_FOUND", 404)
        if row[5] not in _ALLOWED_STATES:
            raise BackendRefused("WORKFLOW_STATE_CORRUPT")
        return row

    @staticmethod
    def _verify_events(db, wf_id):
        rows = db.execute("SELECT seq,kind,previous_sha,event_sha FROM fp_backend_events "
                          "WHERE wf_id=? ORDER BY seq", (wf_id,)).fetchall()
        prev="0"*64
        if not rows:
            raise BackendRefused("EVENT_CHAIN_MISSING")
        for i,(seq,kind,prior,digest) in enumerate(rows,1):
            if (seq!=i or prior!=prev or
                    digest!=_hash({"wf_id":wf_id,"seq":i,"kind":kind,"previous_sha":prior})):
                raise BackendRefused("EVENT_CHAIN_INVALID")
            prev=digest
        return {"integrity":"LOCAL_HASH_CHAIN_INTACT_NOT_NOTARIZED",
                "event_count":len(rows),"last_event_sha256":prev}

    @staticmethod
    def _public(row, proof):
        return {"schema":SCHEMA, "workflow_id":row[0], "template":row[3],
                "plan_sha256":row[4], "status":row[5], "receipt_sha256":row[6],
                **proof, "synthetic_only":True, "owner_files_accessed":False,
                "nas_verified":False, "registered_expert_invoked":False,
                "production_applied":False, "devpost_submitted":False,
                "release_gate":"HOLD"}

    def create(self, goal, request_id):
        if type(goal) is not str or type(request_id) is not str or not REQ.fullmatch(request_id):
            raise BackendRefused("INVALID_INPUT",400)
        plan=compile_goal(goal)
        if plan.get("status")!="READY_FOR_SYNTHETIC_TEST":
            raise BackendRefused("UNSUPPORTED_GOAL",422)
        sha=_hash(plan)
        with self.lock, closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT wf_id,goal FROM fp_backend_workflows WHERE request_id=?",
                           (request_id,)).fetchone()
            if old:
                if old[1]!=goal:
                    raise BackendRefused("IDEMPOTENCY_KEY_CONFLICT")
                db.commit()
                return self.get(old[0])
            wf_id="wf_"+secrets.token_hex(16)
            db.execute("INSERT INTO fp_backend_workflows VALUES(?,?,?,?,?,?,NULL)",
                       (wf_id,request_id,goal,plan["template"],sha,"PLANNED"))
            self._event(db,wf_id,"CREATED")
            db.commit()
        return self.get(wf_id)

    def get(self,wf_id):
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            integrity=self._verify_events(db,wf_id)
            return self._public(row,integrity)

    def list(self):
        """At most 20 recent local-only workflow states; never expose request IDs."""
        with self.lock, closing(self._connect()) as db:
            rows=db.execute("SELECT wf_id FROM fp_backend_workflows ORDER BY rowid DESC LIMIT 20").fetchall()
            return {"schema":SCHEMA,"status":"LOCAL_WORKFLOW_LIST",
                    "workflows":[self.get(wf_id)["workflow_id"] for (wf_id,) in rows],
                    "count":len(rows),"nas_verified":False,"release_gate":"HOLD"}

    def plan(self,wf_id):
        """Return trusted compiled graph only after re-deriving and hashing it."""
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            proof=self._verify_events(db,wf_id)
            plan=compile_goal(row[2])
            if plan.get("status")!="READY_FOR_SYNTHETIC_TEST" or _hash(plan)!=row[4]:
                raise BackendRefused("PLAN_HASH_DRIFT")
            return {"schema":SCHEMA,"workflow_id":wf_id,"plan":plan,
                    "plan_sha256":row[4],**proof,"release_gate":"HOLD"}

    def audit(self,wf_id):
        """Read back event-chain integrity and independently check G119 receipt."""
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            proof=self._verify_events(db,wf_id)
            integrity="NO_SYNTHETIC_RUN"
            if row[5] in ("COMPLETE_LOCAL_SYNTHETIC","BLOCKED","RUNNING",
                          "INTERRUPTED_BLOCKED"):
                try:
                    verified=verify_record(db,"run_"+wf_id[3:])
                    integrity=verified["status"]
                except (ValueError,sqlite3.Error):
                    integrity="NOT_VERIFIED"
            if row[5]=="COMPLETE_LOCAL_SYNTHETIC":
                if integrity!="LOCAL_CHAIN_INTACT":
                    raise BackendRefused("LEDGER_INTEGRITY_MISMATCH")
                receipt=db.execute("SELECT final_sha FROM fp119_runs WHERE run_id=?",
                                   ("run_"+wf_id[3:],)).fetchone()
                if (not receipt or type(row[6]) is not str
                        or type(receipt[0]) is not str
                        or not hmac.compare_digest(row[6],receipt[0])):
                    raise BackendRefused("LEDGER_RECEIPT_MISMATCH")
            return {"schema":SCHEMA,"workflow_id":wf_id,"state":row[5],
                    "audit_events":proof["event_count"],"audit_chain_sha256":proof["last_event_sha256"],
                    "event_integrity":proof["integrity"],"execution_evidence_integrity":integrity,
                    "independently_notarized":False,"real_nas_verified":False,
                    "release_gate":"HOLD"}

    @staticmethod
    def advice(telemetry,*,opt_in):
        """Caller-supplied numeric telemetry, not a live NAS watcher."""
        if type(opt_in) is not bool:
            raise BackendRefused("ADVICE_CONSENT_INVALID",400)
        result=advise_local(telemetry,opt_in=opt_in)
        if result.get("status") in ("INVALID_CONSENT","INVALID_TELEMETRY"):
            raise BackendRefused("ADVICE_TELEMETRY_INVALID",422)
        return result

    def test(self,wf_id):
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            self._verify_events(db,wf_id)
            if row[5] in ("TESTED","APPROVED_SYNTHETIC","COMPLETE_LOCAL_SYNTHETIC"):
                return self.get(wf_id)
            if row[5]!="PLANNED":
                raise BackendRefused("TEST_STATE_CONFLICT")
            checked=run_council(row[2])
            good=(checked.get("status")=="OFFLINE_COUNCIL_REHEARSAL_PASS"
                  and checked.get("actual_nas_verified") is False
                  and checked.get("owner_nas_accessed") is False
                  and checked.get("fixture_executed") is True)
            receipt=_hash({"goal_sha":row[4],"status":checked.get("status"),
                           "trace":checked.get("trace",[])})
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE fp_backend_workflows SET state=?, receipt_sha=? WHERE wf_id=?",
                       ("TESTED" if good else "BLOCKED",receipt,wf_id))
            self._event(db,wf_id,"SYNTHETIC_QA_PASS" if good else "SYNTHETIC_QA_BLOCKED")
            db.commit()
            return self.get(wf_id)

    def evidence(self,wf_id):
        """Export a verified, redacted REAL G119 SQLite fixture receipt.

        This is not an operator report, NAS proof, or an independently signed
        statement. No source files are read and repeated GET cannot rerun QA.
        """
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            self._verify_events(db,wf_id)
            if row[5]!="COMPLETE_LOCAL_SYNTHETIC":
                raise BackendRefused("EVIDENCE_REQUIRES_COMPLETED_SYNTHETIC_RUN")
            plan=compile_goal(row[2])
            if (plan.get("status")!="READY_FOR_SYNTHETIC_TEST"
                    or plan.get("template")!=row[3] or _hash(plan)!=row[4]):
                raise BackendRefused("EVIDENCE_PLAN_DRIFT")
            events=db.execute(
                "SELECT kind FROM fp_backend_events WHERE wf_id=? ORDER BY seq",
                (wf_id,)).fetchall()
            if ([event[0] for event in events] not in (
                    ["CREATED","SYNTHETIC_QA_PASS","SYNTHETIC_ONLY_APPROVED",
                     "RUN_RESERVED","LOCAL_SYNTHETIC_RUN_PASS"],
                    ["CREATED","SYNTHETIC_QA_PASS","SYNTHETIC_ONLY_APPROVED",
                     "RUN_RESERVED","RUN_RECONCILED_WITH_LEDGER"])):
                raise BackendRefused("APPROVAL_OR_RUN_SEQUENCE_INVALID")
            run_id="run_"+wf_id[3:]
            try:
                evidence=verify_record(db,run_id)
                saved=db.execute("SELECT status,final_sha FROM fp119_runs WHERE run_id=?",
                                 (run_id,)).fetchone()
                steps=db.execute(
                    "SELECT seq,kind,detail FROM fp119_events "
                    "WHERE run_id=? ORDER BY seq",(run_id,)).fetchall()
            except (sqlite3.Error,ValueError) as exc:
                raise BackendRefused("G119_EVIDENCE_UNAVAILABLE") from exc
            if (evidence.get("status")!="LOCAL_CHAIN_INTACT" or not saved
                    or saved[0]!="PASS" or type(saved[1]) is not str
                    or type(row[6]) is not str or len(row[6])!=64
                    or not hmac.compare_digest(saved[1],row[6])):
                raise BackendRefused("G119_RECEIPT_MISMATCH")
            stages=[]
            if len(steps)<5 or len(steps)>10:
                raise BackendRefused("G119_EVENT_STRUCTURE_INVALID")
            for index,(seq,kind,raw) in enumerate(steps,1):
                if seq!=index or kind not in ("RESERVED","ROLE","TERMINAL"):
                    raise BackendRefused("G119_EVENT_STRUCTURE_INVALID")
                try:
                    data=json.loads(raw)
                except (ValueError,TypeError) as exc:
                    raise BackendRefused("G119_DETAIL_INVALID") from exc
                if type(data) is not dict:
                    raise BackendRefused("G119_DETAIL_INVALID")
                if kind=="RESERVED":
                    if seq!=1 or data!={"template":row[3]}:
                        raise BackendRefused("G119_RESERVATION_INVALID")
                elif kind=="TERMINAL":
                    if seq!=len(steps) or data!={"result":"SYNTHETIC_QA_PASS"}:
                        raise BackendRefused("G119_TERMINAL_INVALID")
                else:
                    if (set(data)!={"role","status"} or
                            data["role"] not in ("Architect","Security","Builder","Repair","QA")
                            or data["status"]!="PASS"):
                        raise BackendRefused("G119_ROLE_INVALID")
                    stages.append({"role":data["role"],"result":"PASS_SYNTHETIC"})
            if not {"Architect","Security","Builder","QA"}.issubset(
                    {item["role"] for item in stages}):
                raise BackendRefused("G119_REQUIRED_REVIEWS_MISSING")
            report={
                "schema":"flowpilot-backend-evidence-v1",
                "status":"LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS",
                "workflow_id":wf_id,
                "template":row[3],
                "plan_sha256":row[4],
                "receipt_sha256":row[6],
                "audit_event_count":evidence["event_count"],
                "review_stages":stages,
                "approval_proven_in_local_chain":True,
                "customer_files_read":False,
                "registered_expert_invoked":False,
                "real_nas_verified":False,
                "independently_notarized":False,
                "release_gate":"HOLD",
            }
            return {**report, "report_sha256":_hash(report)}

    def approve(self,wf_id,plan_sha,ack):
        if type(plan_sha) is not str or type(ack) is not str:
            raise BackendRefused("APPROVAL_INPUT_INVALID",400)
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            self._verify_events(db,wf_id)
            if plan_sha!=row[4] or ack!="APPROVE_SYNTHETIC_ONLY":
                raise BackendRefused("EXACT_SYNTHETIC_APPROVAL_REQUIRED",403)
            if row[5]=="APPROVED_SYNTHETIC":
                return self.get(wf_id)
            if row[5]!="TESTED":
                raise BackendRefused("APPROVAL_STATE_CONFLICT")
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE fp_backend_workflows SET state='APPROVED_SYNTHETIC' WHERE wf_id=?",
                       (wf_id,))
            self._event(db,wf_id,"SYNTHETIC_ONLY_APPROVED")
            db.commit()
            return self.get(wf_id)

    def report(self,wf_id) -> tuple[bytes,str]:
        """GET a persisted binary artifact, only when G119 receipt is intact."""
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            if row[5]!="COMPLETE_LOCAL_SYNTHETIC":
                raise BackendRefused("REPORT_NOT_YET_COMPLETE")
            # G163 verifies canonical plan, exact human approval sequence,
            # G119 terminal and matching backend/G119 receipt before export.
            self.evidence(wf_id)
            try:
                stored=db.execute("SELECT template,receipt_sha,content_sha,csv_bytes "
                                  "FROM fp_backend_artifacts WHERE wf_id=?",
                                  (wf_id,)).fetchone()
            except sqlite3.Error as exc:
                raise BackendRefused("REPORT_SCHEMA_MISSING") from exc
            if (not stored or stored[0]!=row[3] or
                    type(stored[1]) is not str or type(row[6]) is not str
                    or not hmac.compare_digest(stored[1],row[6]) or
                    type(stored[2]) is not str or len(stored[2])!=64):
                raise BackendRefused("REPORT_BINDING_MISMATCH")
            content=stored[3]
            if (type(content) is not bytes or not 0<len(content)<=4096 or
                    not hmac.compare_digest(stored[2],sha256(content).hexdigest())):
                raise BackendRefused("REPORT_CONTENT_CORRUPTED")
            if content!=CANONICAL_CSV.get(row[3]):
                raise BackendRefused("REPORT_CANONICAL_FIXTURE_DRIFT")
            return content,stored[2]

    def run(self,wf_id):
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            self._verify_events(db,wf_id)
            if row[5]=="COMPLETE_LOCAL_SYNTHETIC":
                return self.get(wf_id)
            if row[5]!="APPROVED_SYNTHETIC":
                raise BackendRefused("RUN_STATE_CONFLICT")
            # Existing DB from pre-G164 is never modified/migrated silently.
            if db.execute("SELECT name FROM sqlite_master WHERE type='table' "
                          "AND name='fp_backend_artifacts'").fetchone() is None:
                raise BackendRefused("ARTIFACT_SCHEMA_NEEDS_OWNER_MIGRATION")
            # Commit reservation BEFORE calling the already replay-protected
            # G119 engine. A crash leaves RUNNING, never silently reruns.
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE fp_backend_workflows SET state='RUNNING' WHERE wf_id=?", (wf_id,))
            self._event(db,wf_id,"RUN_RESERVED")
            db.commit()
            run_id="run_"+wf_id[3:]
            result=run_once(row[2],run_id,db)
            try:
                integrity=verify_record(db,run_id)
                intact=integrity["status"]=="LOCAL_CHAIN_INTACT"
            except (ValueError,sqlite3.Error):
                intact=False
            good=result.get("status")=="SYNTHETIC_LEDGER_PASS" and intact
            content=None
            if good:
                try:
                    content=fixture_csv(row[3],result.get("synthetic_test_evidence"))
                except (ArtifactRefused,ValueError,TypeError):
                    good=False
            receipt=result.get("receipt_sha256") if good else None
            db.execute("BEGIN IMMEDIATE")
            if good:
                db.execute("INSERT INTO fp_backend_artifacts VALUES(?,?,?,?,?)",
                           (wf_id,row[3],receipt,sha256(content).hexdigest(),content))
            db.execute("UPDATE fp_backend_workflows SET state=?, receipt_sha=? WHERE wf_id=?",
                       ("COMPLETE_LOCAL_SYNTHETIC" if good else "BLOCKED",receipt,wf_id))
            self._event(db,wf_id,"LOCAL_SYNTHETIC_RUN_PASS" if good else "RUN_BLOCKED")
            db.commit()
            return self.get(wf_id)

    def recover(self,wf_id):
        """Explicit reconciliation after restart. Never reruns a reserved job."""
        with self.lock, closing(self._connect()) as db:
            row=self._row(db,wf_id)
            self._verify_events(db,wf_id)
            if row[5]!="RUNNING":
                return self.get(wf_id)
            run_id="run_"+wf_id[3:]
            try:
                result=verify_record(db,run_id)
                intact=result["status"]=="LOCAL_CHAIN_INTACT"
                outcome=db.execute("SELECT status,final_sha FROM fp119_runs WHERE run_id=?",
                                   (run_id,)).fetchone()
            except (ValueError,sqlite3.Error):
                intact=False;outcome=None
            # Never mark a previous attempt complete without its already
            # committed artifact. Do not rerun the G119 fixture to repair it.
            try:
                stored=db.execute("SELECT template,receipt_sha,content_sha,csv_bytes "
                                  "FROM fp_backend_artifacts WHERE wf_id=?",
                                  (wf_id,)).fetchone()
                prior=db.execute("SELECT kind FROM fp_backend_events "
                                 "WHERE wf_id=? ORDER BY seq",(wf_id,)).fetchall()
                ledger_goal=db.execute("SELECT goal_sha FROM fp119_runs WHERE run_id=?",
                                       (run_id,)).fetchone()
            except sqlite3.Error:
                stored=None;prior=[];ledger_goal=None
            # A valid SHA of a corrupted CSV is still a corrupted artifact.
            # Recovery must enforce the SAME exact source/template/CSV checks
            # as the normal report path, not only compare mutable DB digests.
            plan=compile_goal(row[2])
            plan_ok=(plan.get("status")=="READY_FOR_SYNTHETIC_TEST" and
                     plan.get("template")==row[3] and _hash(plan)==row[4])
            expected_prior=[("CREATED",),("SYNTHETIC_QA_PASS",),
                            ("SYNTHETIC_ONLY_APPROVED",),("RUN_RESERVED",)]
            good=bool(
                plan_ok and intact and outcome and outcome[0]=="PASS" and
                type(outcome[1]) is str and len(outcome[1])==64 and
                ledger_goal and ledger_goal[0]==_hash(
                    {"template":row[3],"goal":row[2]}) and
                prior==expected_prior and stored and stored[0]==row[3] and
                type(stored[1]) is str and
                hmac.compare_digest(stored[1],outcome[1]) and
                type(stored[3]) is bytes and 0<len(stored[3])<=4096 and
                stored[3]==CANONICAL_CSV.get(row[3]) and
                type(stored[2]) is str and len(stored[2])==64 and
                hmac.compare_digest(stored[2],sha256(stored[3]).hexdigest()))
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE fp_backend_workflows SET state=?,receipt_sha=? WHERE wf_id=?",
                       ("COMPLETE_LOCAL_SYNTHETIC" if good else "INTERRUPTED_BLOCKED",
                        outcome[1] if good else None,wf_id))
            self._event(db,wf_id,"RUN_RECONCILED_WITH_LEDGER" if good else "RUN_INTERRUPTED_NO_RETRY")
            db.commit()
            return self.get(wf_id)


def create_server(backend: Backend, token: str, *, port: int=0):
    if type(token) is not str or len(token)<32 or len(token)>256:
        raise BackendRefused("TOKEN_MUST_BE_32_PLUS_CHARS",400)
    class Handler(BaseHTTPRequestHandler):
        server_version="FlowPilotLocal/1"
        def log_message(self, format, *args):
            return  # no owner IDs/tokens/paths in logs
        def send(self,status,data):
            raw=json.dumps(data,sort_keys=True).encode("utf-8")
            self.send_response(status)
            for k,v in (("Content-Type","application/json; charset=utf-8"),
                        ("Cache-Control","no-store"),("X-Content-Type-Options","nosniff"),
                        ("Content-Security-Policy","default-src 'none'"),
                        ("Content-Length",str(len(raw)))):
                self.send_header(k,v)
            self.end_headers()
            self.wfile.write(raw)
        def send_csv(self,data,digest):
            self.send_response(200)
            for k,v in (("Content-Type","text/csv; charset=utf-8"),
                        ("Content-Disposition",'attachment; filename="flowpilot-synthetic-fixture.csv"'),
                        ("Cache-Control","no-store"),
                        ("X-Content-Type-Options","nosniff"),
                        ("Content-Security-Policy","default-src 'none'"),
                        ("X-Flowpilot-Content-SHA256",digest),
                        ("Content-Length",str(len(data)))):
                self.send_header(k,v)
            self.end_headers()
            self.wfile.write(data)
        def host_guarded(self):
            host=self.headers.get("Host","")
            valid={f"127.0.0.1:{self.server.server_port}",
                   f"localhost:{self.server.server_port}","127.0.0.1","localhost"}
            origin=self.headers.get("Origin")
            if host not in valid or (origin is not None and origin not in
                  {f"http://127.0.0.1:{self.server.server_port}",
                   f"http://localhost:{self.server.server_port}"}):
                self.send(403,{"error":"HOST_ORIGIN_DENIED"});return False
            return True
        def guarded(self):
            if not self.host_guarded():return False
            auth=self.headers.get("Authorization","")
            if not hmac.compare_digest(auth,"Bearer "+token):
                self.send(403,{"error":"AUTH_REQUIRED"});return False
            return True
        def serve_dashboard_asset(self,path):
            # Public only to loopback; static bytes contain no bearer token.
            # Credentials are entered by the owner and held in JS memory only.
            files={"/dashboard":"flowpilot_g166_dashboard.html",
                   "/dashboard.js":"flowpilot_g166_dashboard.js",
                   "/dashboard.css":"flowpilot_g166_dashboard.css"}
            types={"/dashboard":"text/html; charset=utf-8",
                   "/dashboard.js":"text/javascript; charset=utf-8",
                   "/dashboard.css":"text/css; charset=utf-8"}
            try:
                asset=Path(__file__).with_name(files[path])
                if not asset.is_file() or asset.stat().st_size>100000:
                    raise OSError("missing or oversized local dashboard asset")
                raw=asset.read_bytes()
            except OSError:
                self.send(404,{"error":"DASHBOARD_ASSET_UNAVAILABLE"});return
            self.send_response(200)
            for key,value in (
                    ("Content-Type",types[path]),
                    ("Content-Length",str(len(raw))),
                    ("Cache-Control","no-store"),
                    ("Referrer-Policy","no-referrer"),
                    ("X-Content-Type-Options","nosniff"),
                    ("X-Frame-Options","DENY"),
                    ("Content-Security-Policy",
                     "default-src 'none'; script-src 'self'; style-src 'self'; "
                     "connect-src 'self'; img-src 'none'; object-src 'none'; "
                     "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")):
                self.send_header(key,value)
            self.end_headers()
            self.wfile.write(raw)
        def dispatch(self,method):
            if method=="GET" and self.path=="/favicon.ico":
                # Chromium requests favicon automatically. 204 avoids false
                # console 403/404 failures without exposing API/credentials.
                if self.host_guarded():
                    self.send_response(204)
                    self.send_header("Cache-Control","no-store")
                    self.send_header("Content-Length","0")
                    self.end_headers()
                return
            if method=="GET" and self.path in ("/dashboard","/dashboard.js","/dashboard.css"):
                if self.host_guarded():self.serve_dashboard_asset(self.path)
                return
            if not self.guarded():return
            path=self.path
            if "?" in path or "#" in path:
                self.send(404,{"error":"NO_QUERY_PATH"});return
            try:
                if method=="GET":
                    if path=="/v1/health":
                        data={"schema":SCHEMA,"status":"LOCAL_BACKEND_READY",
                              "nas_verified":False,"release_gate":"HOLD"}
                    elif path=="/v1/workflows":
                        data=backend.list()
                    elif re.fullmatch(r"/v1/local-metadata/reviews/rev_[0-9a-f]{32}",path):
                        data=backend.metadata.get(path.rsplit("/",1)[-1])
                    elif re.fullmatch(r"/v1/workflows/wf_[0-9a-f]{32}",path):
                        data=backend.get(path.rsplit("/",1)[-1])
                    elif re.fullmatch(r"/v1/workflows/wf_[0-9a-f]{32}/(plan|audit|evidence|report)",path):
                        wf,action=path.rsplit("/",2)[-2:]
                        if action=="report":
                            blob,digest=backend.report(wf)
                            self.send_csv(blob,digest)
                            return
                        data=getattr(backend,action)(wf)
                    else:
                        self.send(404,{"error":"UNKNOWN_ROUTE"});return
                else:
                    if self.headers.get("Transfer-Encoding") is not None:
                        self.send(400,{"error":"CHUNKED_BODY_REFUSED"});return
                    ct=self.headers.get("Content-Type","")
                    if ct!="application/json":
                        self.send(415,{"error":"JSON_ONLY"});return
                    try:size=int(self.headers.get("Content-Length","-1"))
                    except ValueError:size=-1
                    if size<2 or size>MAX_BODY:
                        self.send(413,{"error":"BODY_LIMIT"});return
                    try:body=json.loads(self.rfile.read(size))
                    except (ValueError,UnicodeError):
                        self.send(400,{"error":"INVALID_JSON"});return
                    if type(body) is not dict:
                        self.send(400,{"error":"JSON_OBJECT_REQUIRED"});return
                    if path=="/v1/workflows":
                        if set(body)!={"goal","request_id"}:
                            raise BackendRefused("UNEXPECTED_KEYS",400)
                        data=backend.create(body["goal"],body["request_id"])
                    elif path=="/v1/local-metadata/preview":
                        if set(body)!={"goal","required"}:
                            raise BackendRefused("UNEXPECTED_KEYS",400)
                        data=backend.metadata.begin(body["goal"],body["required"])
                    elif path=="/v1/local-metadata/approve":
                        if set(body)!={"review_id","scope_sha256","acknowledgement"}:
                            raise BackendRefused("UNEXPECTED_KEYS",400)
                        data=backend.metadata.approve(body["review_id"],body["scope_sha256"],
                                                      body["acknowledgement"])
                    elif path=="/v1/local-metadata/cancel":
                        if set(body)!={"review_id"}:
                            raise BackendRefused("UNEXPECTED_KEYS",400)
                        data=backend.metadata.cancel(body["review_id"])
                    elif path=="/v1/advice":
                        if set(body)!={"telemetry","opt_in"}:
                            raise BackendRefused("UNEXPECTED_KEYS",400)
                        data=backend.advice(body["telemetry"],opt_in=body["opt_in"])
                    else:
                        match=re.fullmatch(r"/v1/workflows/(wf_[0-9a-f]{32})/(test|approve|run|recover)",path)
                        if not match:
                            self.send(404,{"error":"UNKNOWN_ROUTE"});return
                        wf,action=match.groups()
                        if action=="approve":
                            if set(body)!={"plan_sha256","acknowledgement"}:
                                raise BackendRefused("UNEXPECTED_KEYS",400)
                            data=backend.approve(wf,body["plan_sha256"],body["acknowledgement"])
                        else:
                            if body:
                                raise BackendRefused("UNEXPECTED_KEYS",400)
                            data=getattr(backend,action)(wf)
                self.send(200,data)
            except (BackendRefused, MetadataRefused) as exc:
                self.send(exc.status,{"error":exc.code,"release_gate":"HOLD"})
            except (OSError,sqlite3.Error,AssertionError,ValueError):
                self.send(409,{"error":"LOCAL_BACKEND_REFUSED","release_gate":"HOLD"})
        def do_GET(self):self.dispatch("GET")
        def do_POST(self):self.dispatch("POST")
    server=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    server.daemon_threads=True
    return server


def main(argv=None):
    p=argparse.ArgumentParser(description="LOCAL synthetic FlowPilot backend, no real NAS")
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--init-db",action="store_true")
    p.add_argument("--metadata-root",type=Path,
                   help="Explicit operator-selected local non-NAS folder; never exposed through HTTP")
    p.add_argument("--port",type=int,default=8766)
    a=p.parse_args(argv)
    token=os.environ.get("FLOWPILOT_LOCAL_API_TOKEN","")
    try:
        backend=Backend(a.db,create=a.init_db,metadata_root=a.metadata_root)
        server=create_server(backend,token,port=a.port)
    except (BackendRefused,MetadataRefused,OSError,sqlite3.Error):
        print(json.dumps({"status":"LOCAL_BACKEND_START_REFUSED","release_gate":"HOLD"}))
        return 2
    try:
        print(json.dumps({"status":"LOCAL_BACKEND_LISTENING_NOT_NAS",
                          "url":f"http://127.0.0.1:{server.server_port}",
                          "token_in_logs":False,"release_gate":"HOLD"}),flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
