"""Local-only interactive FlowPilot 3.0 Command Center demo on synthetic CSVs.

No real NAS, Uliya, HAE, LA, SOVIA or DBVORA integration. Loopback only.
Explicit per-preview approval is mandatory before synthetic CSV output is created.
"""
from __future__ import annotations

import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
from tempfile import TemporaryDirectory

from flowpilot_csv_e2e import run_session
from flowpilot_command_center import render_dashboard

GOAL = "고객별 매출 보고서 만들어줘"


class DemoController:
    def __init__(self):
        self._temp = TemporaryDirectory(prefix="flowpilot-demo-")
        self.root = Path(self._temp.name)
        for name, rows in (("jan.csv", [("alice", "1.25"), ("bob", "2.00")]),
                           ("feb.csv", [("alice", "3.75"), ("bob", "4.00")])):
            with (self.root / name).open("x", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["customer", "revenue"])
                writer.writerows(rows)
        self.args = dict(goal=GOAL, root=self.root, sources=["jan.csv", "feb.csv"],
                         output="summary.csv", group="customer", amount="revenue")
        self.db = self.root / "audit.sqlite"
        self.token = secrets.token_urlsafe(32)
        self._pending = False
        self._finished = False
        self._lock = threading.Lock()
        self._last = run_session(GOAL)

    def close(self):
        self._temp.cleanup()

    def view(self) -> dict:
        with self._lock:
            return dict(self._last)

    def configure(self, payload: dict) -> dict:
        """One guided intake turn using ONLY synthetic, allowlisted CSV fixtures.

        No caller-supplied filesystem roots or arbitrary paths are accepted.
        Any new preview invalidates the previous approval state.
        """
        if not isinstance(payload, dict) or set(payload) != {"goal", "sources", "output"}:
            raise ValueError("Invalid guided input")
        goal, sources, output = payload["goal"], payload["sources"], payload["output"]
        if not isinstance(goal, str) or len(goal) > 200:
            raise ValueError("Invalid goal")
        if (not isinstance(sources, list) or not 1 <= len(sources) <= 2
                or len(sources) != len(set(sources))
                or any(type(name) is not str or name not in ("jan.csv", "feb.csv")
                       for name in sources)):
            raise ValueError("Only explicit synthetic example files are supported")
        if type(output) is not str or output not in ("summary.csv", "monthly-summary.csv"):
            raise ValueError("Only bounded output paths are supported")
        with self._lock:
            if self._finished:
                raise ValueError("Demo already executed; restart to reset")
            args = dict(goal=goal, root=self.root, sources=sources,
                        output=output, group="customer", amount="revenue")
            # Validation and file preflight happen before mutating the pending plan.
            candidate = run_session(**args)
            if candidate["status"] != "WAITING_EXECUTION_APPROVAL":
                raise ValueError("Missing or unsupported inputs")
            self.args = args
            self._last = candidate
            self._pending = True
            return dict(self._last)

    def report_csv(self) -> bytes:
        """Expose only the approved synthetic output, never arbitrary paths."""
        with self._lock:
            if not self._finished or self._last.get("status") != "LOCAL_REPORT_CREATED_NOT_NAS":
                raise ValueError("No approved report available")
            path = self.root / self.args["output"]
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
                raise ValueError("Report unavailable")
            return path.read_bytes()

    def act(self, action: str) -> dict:
        with self._lock:
            if action == "preview":
                if self._finished:
                    raise ValueError("Demo already executed; restart to reset")
                self._last = run_session(**self.args)
                self._pending = True
            elif action == "reject":
                if not self._pending or self._finished:
                    raise ValueError("No pending preview")
                self._last = run_session(**self.args, approval="REJECT")
                self._pending = False
            elif action == "approve":
                if not self._pending or self._finished:
                    raise ValueError("No pending preview")
                self._pending = False  # single use, even if execution raises
                self._last = run_session(**self.args, approval="APPROVE_EXECUTION",
                                         audit_db=self.db)
                self._finished = True
            else:
                raise ValueError("Unknown action")
            return dict(self._last)


# HTML is owned by this demo, no user-supplied HTML is interpolated into it.
PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NAS FlowPilot 3.0 — Interactive Local Demo</title><style>
:root{color-scheme:dark;font-family:Inter,system-ui,Arial,sans-serif;color:#e9f4ff;background:#071422}
body{margin:0;background:linear-gradient(145deg,#0b2441,#071422 60%)}
main{max-width:1280px;margin:auto;padding:36px 24px}header{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
h1{font-size:clamp(29px,3vw,44px);margin:6px 0}.caption{color:#78d9ff;font-size:12px;letter-spacing:.13em;font-weight:800}
p{color:#afc3d4;line-height:1.5}.pill{border:1px solid #46718c;border-radius:50px;padding:9px 14px;color:#a6d9ee}
.steps,.artifacts{display:grid;grid-template-columns:repeat(5,1fr);gap:11px;margin-top:18px}
.step,.card{background:#11263c;border:1px solid #2b4e68;border-radius:14px;padding:18px}
.step small{color:#59d0ff}.step strong{display:block;margin-top:12px}h2{margin-top:30px;font-size:19px}
.content{display:grid;grid-template-columns:1.2fr 1fr;gap:14px}.card{min-height:190px}.artifacts{grid-template-columns:repeat(4,1fr)}
input[type=text],input:not([type]),select{background:#071625;border:1px solid #41718c;border-radius:8px;color:#e6f6ff;padding:10px;max-width:100%;margin:9px 8px 9px 0}.choices{display:flex;gap:18px;flex-wrap:wrap;margin:8px 0}button{padding:12px 17px;background:#0e76b5;border:1px solid #42bfff;color:white;border-radius:9px;font-weight:700;cursor:pointer;margin:4px 6px 4px 0}
button:disabled{opacity:.35;cursor:not-allowed}.reject{background:#512b3e;border-color:#c96073}.approve{background:#117b65;border-color:#4adbad}
pre{white-space:pre-wrap;word-break:break-word;max-height:290px;overflow:auto;background:#071625;padding:14px;border-radius:9px;font-size:12px;color:#cce3f8}
#status{color:#f4cb7b;font-weight:700}footer{margin-top:25px;color:#91a9bc;font-size:12px}
@media(max-width:900px){.steps,.artifacts{grid-template-columns:repeat(2,1fr)}.content{grid-template-columns:1fr}}
@media(max-width:550px){.steps,.artifacts{grid-template-columns:1fr}}
</style></head><body><main><header><div><div class="caption">UGREEN NAS AI HACKATHON · SYNTHETIC LOCAL DEMO</div>
<h1>NAS FlowPilot 3.0</h1><p>Natural Language to NAS Automation · Interactive Command Center</p></div>
<span class="pill">LOCAL ONLY · NAS UNVERIFIED</span></header>
<h2>Five-stage E2E flow</h2><div class="steps">
<div class="step"><small>01</small><strong>Natural Request</strong><p>고객별 매출 보고서 만들어줘</p></div>
<div class="step"><small>02</small><strong>Guided Slots</strong><p>Example CSV input and grouping fields</p></div>
<div class="step"><small>03</small><strong>Workflow Preview</strong><p>Deterministic graph; LA not invoked</p></div>
<div class="step"><small>04</small><strong>Approved Execute</strong><p>Local CSV grouping, new output</p></div>
<div class="step"><small>05</small><strong>Audit Result</strong><p>SQLite record; not SOVIA</p></div></div>
<h2>Live workflow</h2><div class="content"><div class="card">
<p>Step 1 · Give a supported natural-language goal and select synthetic NAS-like files.</p>
<label for="goal">Natural language goal</label><input id="goal" value="고객별 매출 보고서 만들어줘" maxlength="200" aria-label="Natural language goal">
<div class="choices"><label><input id="jan" type="checkbox" checked> jan.csv</label>
<label><input id="feb" type="checkbox" checked> feb.csv</label></div>
<label for="output">New output filename</label><select id="output"><option value="summary.csv">summary.csv</option>
<option value="monthly-summary.csv">monthly-summary.csv</option></select>
<p>Grouping: customer · Numeric field: revenue (fixed safe demo capabilities)</p>
<p>Step 2 · Preview the workflow, then approve or reject it.</p>
<button id="preview">Preview selected workflow</button><button class="approve" id="approve" disabled>Approve &amp; run</button>
<button class="reject" id="reject" disabled>Reject</button><p id="status" role="status">Loading...</p><h3>Workflow graph</h3>
<pre id="graph">No preview yet.</pre></div><div class="card"><h3>Output &amp; audit</h3><pre id="result">Awaiting preview.</pre><button id="download" disabled>Download approved CSV</button><pre id="csv">Report not created.</pre></div></div>
<h2>Submission package · target</h2><div class="artifacts"><div class="card"><b>Skill ZIP</b><p>Official compatibility pending</p></div>
<div class="card"><b>English Summary PDF</b><p>500 words max · 1MB max</p></div>
<div class="card"><b>Demo video</b><p>2–3 min proposal; mandatory status unverified</p></div>
<div class="card"><b>Devpost</b><p>Not submitted</p></div></div>
<footer>This is a local synthetic demo. Actual Uliya/NAS, LA, SOVIA and DBVORA integrations have NOT been verified.</footer>
<script>
const secret = __DEMO_TOKEN__;
const el = id => document.getElementById(id);
async function update(){ const r = await fetch('/api/state',{cache:'no-store'}); if(!r.ok)throw Error('State unavailable'); show(await r.json()); }
function show(s){ const state=s.status || 'UNKNOWN'; el('status').textContent=state;
const graph=s.workflow_graph?.nodes || []; el('graph').textContent=JSON.stringify(graph,null,2);
const audit=s.audit?.runs || []; el('result').textContent=JSON.stringify({execution:s.execution?.result || null,audit:audit,la_compatibility:s.la_compatibility?.status || 'NOT_CHECKED'},null,2);
const ready=state==='WAITING_EXECUTION_APPROVAL'; el('approve').disabled=!ready;el('reject').disabled=!ready;
el('preview').disabled=state==='LOCAL_REPORT_CREATED_NOT_NAS'; el('download').disabled=state!=='LOCAL_REPORT_CREATED_NOT_NAS'; }
async function action(type){ try {const r=await fetch('/api/'+type,{method:'POST',headers:{'X-Flowpilot-Token':secret,'Content-Type':'application/json'},body:'{}'});
const data=await r.json();if(!r.ok)throw Error(data.error || 'Request failed');show(data);}catch(e){el('status').textContent=e.message;}}
async function downloadReport(){ try {
const r=await fetch('/api/report',{headers:{'X-Flowpilot-Token':secret},cache:'no-store'});
if(!r.ok)throw Error('Approved report unavailable');
const csv=await r.text();el('csv').textContent=csv;
const link=document.createElement('a');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
link.href=url;link.download='flowpilot-summary.csv';document.body.appendChild(link);link.click();link.remove();
setTimeout(()=>URL.revokeObjectURL(url),1000);
}catch(e){el('status').textContent=e.message;}}
el('download').addEventListener('click',downloadReport);
async function previewSelection(){
const body={goal:el('goal').value,sources:['jan','feb'].filter(id=>el(id).checked).map(id=>id+'.csv'),output:el('output').value};
try{const r=await fetch('/api/configure',{method:'POST',headers:{'X-Flowpilot-Token':secret,'Content-Type':'application/json'},body:JSON.stringify(body)});
const data=await r.json();if(!r.ok)throw Error(data.error||'Configuration refused');show(data);
}catch(e){el('approve').disabled=true;el('reject').disabled=true;el('status').textContent=e.message;}}
el('preview').addEventListener('click',previewSelection);
for(const a of ['approve','reject'])el(a).addEventListener('click',()=>action(a));update().catch(e=>el('status').textContent=e.message);
</script></main></body></html>'''


def create_server(controller: DemoController, port: int = 0) -> ThreadingHTTPServer:
    if type(port) is not int or port < 0 or port > 65535:
        raise ValueError("Invalid port")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # No local path or token in logs

        def send_payload(self, status: int, content: bytes, kind: str):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, status: int, payload: dict):
            self.send_payload(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def host_ok(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.host_ok():
                self.send_json(403, {"error": "Invalid host"}); return
            if self.path == "/":
                html = PAGE.replace("__DEMO_TOKEN__", json.dumps(controller.token))
                self.send_payload(200, html.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/state":
                self.send_json(200, controller.view())
            elif self.path == "/api/report":
                if self.headers.get("X-Flowpilot-Token") != controller.token:
                    self.send_json(403, {"error": "Report authorization required"}); return
                try:
                    body = controller.report_csv()
                except (ValueError, OSError):
                    self.send_json(409, {"error": "No approved CSV report"}); return
                self.send_payload(200, body, "text/csv; charset=utf-8")
            else:
                self.send_json(404, {"error": "Not found"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            expected = f"http://127.0.0.1:{self.server.server_port}"
            if (not self.host_ok() or origin not in (None, expected)
                    or self.headers.get("X-Flowpilot-Token") != controller.token
                    or self.headers.get("Content-Type") != "application/json"):
                self.send_json(403, {"error": "Request denied"}); return
            try:
                body_size = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                body_size = -1
            if self.path == "/api/configure":
                if not 2 <= body_size <= 512:
                    self.send_json(413, {"error": "Invalid input size"}); return
                try:
                    payload = json.loads(self.rfile.read(body_size))
                    value = controller.configure(payload)
                except (ValueError, OSError, TypeError, UnicodeError):
                    self.send_json(409, {"error": "Guided configuration refused"}); return
                self.send_json(200, value); return
            if body_size != 2 or self.rfile.read(2) != b"{}":
                self.send_json(400, {"error": "Unexpected body"}); return
            if self.path not in ("/api/preview", "/api/approve", "/api/reject"):
                self.send_json(404, {"error": "Unknown action"}); return
            try:
                value = controller.act(self.path[len("/api/"):])
            except (ValueError, OSError, TypeError):
                self.send_json(409, {"error": "Action refused"}); return
            self.send_json(200, value)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Synthetic local FlowPilot 3.0 interactive demo")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    controller = DemoController()
    try:
        server = create_server(controller, args.port)
        print(f"LOCAL SYNTHETIC DEMO: http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        controller.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
