"""Interactive *synthetic* NAS FlowPilot handoff review, no external services.

Unlike the separate CSV demonstration, this follows the READ-ONLY Round 1
Skill's handoff/check/version/selected-document scenarios. No NAS, official
Uliya Expert, Uliya Creator, Lightning Azent, SOVIA, DBVORA, user folders,
file contents, file writes, uploads or Devpost submission. All evidence is
built from code-owned synthetic data, NEVER an actual registered-agent call.
"""
from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading

from flowpilot_owner_review_report import assemble_review
from flowpilot_owner_review_dashboard import render_owner_review
from flowpilot_document_result_intake import fingerprint
from flowpilot_selected_document_stage import preview_selected_document
from flowpilot_agent_result_intake import IntakeRefused

ROOT = "/synthetic/flowpilot-demo"
DOC_REFERENCE = "synthetic://deliverable-2"
SCENARIOS = frozenset({"handoff", "missing", "versions", "document"})
GOALS = {
    "handoff": "check handoff deliverables",
    "missing": "check required files",
    "versions": "compare versions",
    "document": "summarize selected document",
}


def fixture(scenario: str) -> dict:
    """In-memory fixture with synthetic filenames; does not inspect any directory."""
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        raise ValueError("Unsupported synthetic example")
    observations = [
        {"relative_path": "README.md", "reference": "synthetic://readme-1",
         "contained": True, "is_symlink": False},
        {"relative_path": "release/output.pdf", "reference": DOC_REFERENCE,
         "contained": True, "is_symlink": False},
    ]
    if scenario == "missing":
        observations.pop()
    if scenario == "versions":
        observations.append(
            {"relative_path": "release/output_v2.pdf",
             "reference": "synthetic://alternate-3",
             "contained": True, "is_symlink": False}
        )
    receipt = {
        "schema": "flowpilot-agent-observation-v1",
        "origin": "SYNTHETIC_TEST",
        "goal": GOALS[scenario],
        "authorized_root": ROOT,
        "required_paths": ["README.md", "release/output.pdf"],
        "metadata_approved": False,
        "unknown_processing_accepted": False,
        "file_agent_report": {
            "agent": "file-agent", "operation": "ug-filesystem find",
            "authorized_root": ROOT, "permission_confirmed": True,
            "registered_adapter_confirmed": True, "scan_complete": True,
            "pagination_complete": True, "failed": False,
            "observations": observations,
        },
    }
    if scenario == "versions":
        receipt["version_candidates"] = {
            "release/output.pdf": ["release/output_v2.pdf"]
        }
    return receipt


class HandoffDemo:
    """Single in-memory, lock-protected, explicit-approval demo session."""
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self._lock = threading.RLock()
        self._scenario = None
        self._phase = "WAITING_PREVIEW"
        self._receipt = None
        self._report = None
        self._question = None
        self._consent_nonce = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "phase": self._phase,
                "scenario": self._scenario,
                "report": self._report,
                "consent_nonce": self._consent_nonce,
                "actual_uliya_or_nas_invoked": False,
                "release_gate": "HOLD",
            }

    def current_dashboard(self) -> str:
        with self._lock:
            if self._report is None:
                raise ValueError("Preview the synthetic review first")
            return render_owner_review(self._report)

    def action(self, name: str, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("Invalid action")
        with self._lock:
            if name == "preview":
                if set(params) != {"scenario"}:
                    raise ValueError("Unexpected preview input")
                incoming = fixture(params["scenario"])
                new_report = assemble_review(incoming)
                self._scenario = params["scenario"]
                self._receipt = incoming
                self._report = new_report
                self._phase = "WAITING_METADATA_APPROVAL"
                self._question = None
                self._consent_nonce = None
            elif name == "approve-metadata":
                if (set(params) != {"ack_unknown_processing"}
                        or params["ack_unknown_processing"] is not True
                        or self._phase != "WAITING_METADATA_APPROVAL"):
                    raise ValueError("Explicit metadata approval required")
                candidate = dict(self._receipt)
                candidate["metadata_approved"] = True
                candidate["unknown_processing_accepted"] = True
                new_report = assemble_review(candidate)
                self._receipt = candidate
                self._report = new_report
                self._phase = ("WAITING_DOCUMENT_SELECTION" if self._scenario == "document"
                               else "REVIEW_AVAILABLE")
            elif name == "preview-document":
                if (set(params) != {"question", "select_document"}
                        or params["select_document"] is not True
                        or self._phase not in ("WAITING_DOCUMENT_SELECTION", "WAITING_DOCUMENT_APPROVAL")
                        or self._scenario != "document"):
                    raise ValueError("Selection cannot bypass first approval")
                question = params["question"]
                # The stage-2 engine validates the bounded question and exact
                # reference BEFORE a consent preview can be issued.
                preview = preview_selected_document(
                    self._receipt,
                    selected_refs=[DOC_REFERENCE],
                    question=question,
                    consented_refs=[],
                    content_approved=False,
                )
                if preview["status"] != "WAITING_SEPARATE_DOCUMENT_APPROVAL":
                    raise ValueError("Unverified document selection")
                new_report = assemble_review(
                    self._receipt,
                    selected_refs=[DOC_REFERENCE],
                    question=question,
                    consented_refs=[],
                    content_approved=False,
                )
                self._question = question
                self._report = new_report
                self._phase = "WAITING_DOCUMENT_APPROVAL"
                self._consent_nonce = secrets.token_urlsafe(24)
            elif name == "approve-document":
                if (set(params) != {"consent_nonce", "approve_content"}
                        or self._phase != "WAITING_DOCUMENT_APPROVAL"
                        or params["approve_content"] is not True
                        or not isinstance(params["consent_nonce"], str)
                        or params["consent_nonce"] != self._consent_nonce):
                    raise ValueError("Separate document approval invalid or stale")
                approved = preview_selected_document(
                    self._receipt,
                    selected_refs=[DOC_REFERENCE],
                    question=self._question,
                    consented_refs=[DOC_REFERENCE],
                    content_approved=True,
                )
                if approved["status"] != "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED":
                    raise ValueError("Document draft failed")
                draft = approved["synthetic_instruction_draft"]
                # Operator-provided example response only; this does NOT read
                # any PDF and is NOT evidence of a real Expert answer.
                claim = {
                    "schema": "flowpilot-normalized-document-result-v1",
                    "origin": "SYNTHETIC_TEST",
                    "agent": "document-agent",
                    "operation": "ug-document qa",
                    "authorized_root": draft["authorized_root"],
                    "request_sha256": fingerprint(draft),
                    "question_sha256": draft["question_sha256"],
                    "permission_confirmed": True,
                    "registered_adapter_confirmed": True,
                    "scan_complete": True,
                    "failed": False,
                    "results": [
                        {"reference": DOC_REFERENCE, "state": "ANSWERED",
                         "answer": "Synthetic fixture answer only, not retrieved from any file."}
                    ],
                }
                new_report = assemble_review(
                    self._receipt, document_receipt=claim,
                    selected_refs=[DOC_REFERENCE],
                    question=self._question,
                    consented_refs=[DOC_REFERENCE],
                    content_approved=True,
                )
                self._report = new_report
                self._consent_nonce = None
                self._phase = "REVIEW_AVAILABLE"
            else:
                raise ValueError("Unknown action")
            return self.snapshot()


PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>NAS FlowPilot 3.0 — Handoff Command Center</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,Segoe UI,sans-serif;color:#eaf3ff;background:#081321}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 18% 0%,#1a3653,#081321 60%);min-height:100vh}
main{max-width:1500px;margin:auto;padding:32px 25px 60px}.head{display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap;align-items:center}
h1{font-size:clamp(29px,3vw,44px);margin:7px 0}h2{font-size:18px;margin:25px 0 13px}
.eyebrow{font-size:12px;color:#65d9ff;letter-spacing:.12em;font-weight:800}
.pill{padding:10px 15px;border:1px solid #4884a1;border-radius:40px;color:#b8e6fa;font-size:12px}
p,.desc{color:#a0b8ca;font-size:13px;line-height:1.65}.grid{display:grid;grid-template-columns:1fr 1.4fr;gap:15px}
.panel{border:1px solid #2b526e;background:#10243a;border-radius:15px;padding:22px}
label{display:block;color:#c3d8e8;font-size:12px;font-weight:700;margin:12px 0 6px}
select,input[type=text]{background:#071b2d;border:1px solid #41758f;border-radius:9px;color:#edf7ff;padding:12px;width:100%}
button{background:#1677b0;border:1px solid #55bdec;border-radius:9px;color:white;font-weight:750;
padding:11px 16px;cursor:pointer;margin:8px 7px 8px 0}
button:disabled{opacity:.3;cursor:not-allowed}button.approve{background:#11735e;border-color:#41caa8}
#state{color:#ffd388;font-weight:750;font-size:14px;margin-top:12px}
.preview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
.metric{background:#0b1d2e;border:1px solid #294b60;border-radius:11px;padding:14px}
.metric strong{display:block;font-size:26px;margin:8px 0}
#dashboard{width:100%;height:730px;border:1px solid #31536b;border-radius:12px;background:#081321}
.note{color:#ffcc8e;font-size:12px}
@media(max-width:980px){.grid{grid-template-columns:1fr}.preview{grid-template-columns:repeat(2,1fr)}}
@media(max-width:550px){.preview{grid-template-columns:1fr}main{padding:20px 12px}}
</style></head><body><main>
<div class="head"><div><div class="eyebrow">UGREEN ROUND 1 SKILL CONCEPT · SYNTHETIC HANDOFF DEMO</div>
<h1>NAS FlowPilot 3.0</h1><p>Natural language → Scope preview → Metadata approval → Evidence review → Optional separate document consent</p></div>
<div class="pill">OFFLINE FIXTURES · NOT NAS</div></div>
<div class="grid"><section class="panel">
<h2>1 · Natural-language intent</h2>
<label for="scenario">Choose a fixed synthetic example</label>
<select id="scenario"><option value="handoff">Check project handoff</option>
<option value="missing">Check a missing required file</option>
<option value="versions">Compare conflicting final versions</option>
<option value="document">Summarize one selected document</option></select>
<p>Example checklist: README.md and release/output.pdf. No file system or NAS is accessed.</p>
<button id="preview">Preview scope (no execution)</button>
<h2>2 · Explicit metadata approval</h2><p class="desc">Demonstration acknowledges that actual Uliya processing location is unknown; no vendor call will occur.</p>
<label><input id="ack" type="checkbox"> Approve this synthetic metadata review and acknowledge unknown real-platform processing location</label>
<button class="approve" id="metadata" disabled>Approve metadata inspection</button>
<h2>3 · Optional document review</h2>
<label><input id="selectdoc" type="checkbox"> Select synthetic release/output.pdf</label>
<label for="question">Exact question</label>
<input id="question" type="text" maxlength="512" value="Summarize delivery risks in this document?">
<button id="previewdoc" disabled>Preview separate document consent</button>
<button class="approve" id="approvedoc" disabled>Approve selected document review</button>
<p class="note">Document results are synthetic claim receipts. No real PDF is opened or analyzed.</p>
<div id="state" role="status">Waiting for preview.</div>
</section><section class="panel"><h2>4 · Evidence summary</h2>
<div class="preview"><div class="metric">Present claims<strong id="present">—</strong></div>
<div class="metric">Missing claims<strong id="missing">—</strong></div>
<div class="metric">Not checked<strong id="unchecked">—</strong></div>
<div class="metric">Version review<strong id="version">—</strong></div></div>
<p id="docstate" class="desc">Document result unavailable until separate consent.</p>
<p id="verdict" class="note">Never a production READY certificate.</p>
<p class="desc">Four-stage audit evidence appears below. This simulation only checks the same bounded contracts as the Round 1 Skill concept.</p>
</section></div>
<h2>Offline Owner Review Command Center</h2>
<iframe id="dashboard" title="Redacted synthetic owner review dashboard"></iframe>
<p class="desc">Actual Uliya Creator, registered NAS experts, NAS hardware, Lightning Azent, and Devpost remain NOT_RUN or NOT_SUBMITTED.</p>
<script>
const token=__SESSION_TOKEN__;
const byId=id=>document.getElementById(id);
let current={phase:"WAITING_PREVIEW",report:null,consent_nonce:null};
async function action(name,data){
 try{
 const r=await fetch("/api/"+name,{method:"POST",headers:{"Content-Type":"application/json","X-Flowpilot-Token":token},body:JSON.stringify(data)});
 const body=await r.json();if(!r.ok)throw Error(body.error||"Request refused");show(body);
 }catch(err){byId("state").textContent=err.message;}
}
function show(data){
 current=data;byId("state").textContent="Session: "+data.phase+" (LOCAL ONLY)";
 const c=data.report?.file_stage?.counts||{};
 for(const [id,key] of [["present","PRESENT"],["missing","MISSING"],["unchecked","NOT_CHECKED"],["version","VERSION_REVIEW"]])
 byId(id).textContent=c[key]??"—";
 byId("verdict").textContent=data.report?.status||"No evidence yet";
 byId("docstate").textContent="Document stage: "+(data.report?.document_stage?.status||"NOT_REQUESTED");
 const metadata=data.phase==="WAITING_METADATA_APPROVAL";
 byId("metadata").disabled=!metadata||!byId("ack").checked;
 byId("previewdoc").disabled=!(data.scenario==="document"&&["WAITING_DOCUMENT_SELECTION","WAITING_DOCUMENT_APPROVAL"].includes(data.phase));
 byId("approvedoc").disabled=data.phase!=="WAITING_DOCUMENT_APPROVAL";
 if(data.report)byId("dashboard").src="/api/dashboard?stage="+encodeURIComponent(data.phase);
}
byId("ack").addEventListener("change",()=>byId("metadata").disabled=!(current.phase==="WAITING_METADATA_APPROVAL"&&byId("ack").checked));
byId("preview").addEventListener("click",()=>{byId("ack").checked=false;action("preview",{scenario:byId("scenario").value});});
byId("metadata").addEventListener("click",()=>action("approve-metadata",{ack_unknown_processing:byId("ack").checked}));
byId("previewdoc").addEventListener("click",()=>action("preview-document",{question:byId("question").value,select_document:byId("selectdoc").checked}));
byId("approvedoc").addEventListener("click",()=>action("approve-document",{consent_nonce:current.consent_nonce,approve_content:true}));
for(const id of ["question","selectdoc"])byId(id).addEventListener("input",()=>{byId("approvedoc").disabled=true;byId("state").textContent="Selection changed. Preview document consent again.";});
</script></main></body></html>'''


def create_server(demo: HandoffDemo, port: int = 0) -> ThreadingHTTPServer:
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Invalid demo port")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_unused):
            pass

        def respond(self, status: int, payload: bytes, content_type: str, *, frame: bool = False):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                             "connect-src 'self'; frame-src 'self'; frame-ancestors " +
                             ("'self'" if frame else "'none'"))
            self.end_headers()
            self.wfile.write(payload)

        def json(self, status: int, data: dict):
            self.respond(status, json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8"),
                         "application/json; charset=utf-8")

        def safe_host(self) -> bool:
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.safe_host():
                self.json(403, {"error": "Host refused"}); return
            if self.path == "/":
                html = PAGE.replace("__SESSION_TOKEN__", json.dumps(demo.token))
                self.respond(200, html.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/state":
                self.json(200, demo.snapshot())
            elif self.path.startswith("/api/dashboard") and (
                self.path == "/api/dashboard" or self.path.startswith("/api/dashboard?stage=")
            ):
                try:
                    html = demo.current_dashboard()
                except ValueError:
                    self.json(409, {"error": "No preview"}); return
                self.respond(200, html.encode("utf-8"), "text/html; charset=utf-8", frame=True)
            else:
                self.json(404, {"error": "Not found"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed_origin = f"http://127.0.0.1:{self.server.server_port}"
            if (not self.safe_host()
                    or origin not in (None, allowed_origin)
                    or self.headers.get("X-Flowpilot-Token") != demo.token
                    or self.headers.get("Content-Type") != "application/json"):
                self.json(403, {"error": "Request refused"}); return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                length = -1
            if not 2 <= length <= 2048:
                self.json(413, {"error": "Invalid request size"}); return
            if self.path not in ("/api/preview", "/api/approve-metadata",
                                 "/api/preview-document", "/api/approve-document"):
                self.json(404, {"error": "Unknown action"}); return
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                result = demo.action(self.path.removeprefix("/api/"), data)
            except (ValueError, TypeError, IntakeRefused, UnicodeError, json.JSONDecodeError):
                self.json(409, {"error": "Action refused"}); return
            self.json(200, result)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Synthetic handoff read-only review; NOT NAS")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    demo = HandoffDemo()
    server = create_server(demo, args.port)
    print(f"SYNTHETIC LOCAL HANDOFF DEMO: http://127.0.0.1:{server.server_port}/",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
