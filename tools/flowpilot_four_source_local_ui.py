"""Loopback-only explicit-approval operator UI; disposable local synthetic data."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import secrets
import sys
import webbrowser
from threading import Lock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from tools.flowpilot_source_doctor import inspect_sources
from tools.flowpilot_four_source_suite import run_suite
from tools.flowpilot_real_os_demo import run_real_local_demo

CONSENT = "I_APPROVE_DISPOSABLE_SYNTHETIC_WRITES"
EVIDENCE_HTML = frozenset({"index.html", *(f"proof-{i}.html" for i in (1, 2, 3))})
EVIDENCE_JSON = frozenset({"manifest.json", *(f"proof-{i}.json" for i in (1, 2, 3))})
EVIDENCE_FILES = EVIDENCE_HTML | EVIDENCE_JSON
MAX_EVIDENCE_BYTES = 256_000


class OperatorRefused(ValueError):
    """Do not echo caller source paths or exception messages."""


class Operator:
    def __init__(self, hae: Path, sovia: Path, dbvora: Path, output: Path | None = None):
        self.roots = (hae, sovia, dbvora)
        self.output = output
        self.lock = Lock()
        self.challenge = None
        self.attempted = False
        self.evidence_ready = False

    def sources(self) -> dict:
        return inspect_sources(*self.roots)

    @staticmethod
    def real_os_demo() -> dict:
        # Independent of private source checkouts and without customer paths.
        return run_real_local_demo()

    def preview(self) -> dict:
        with self.lock:
            if self.attempted:
                raise OperatorRefused("SYNTHETIC_EXECUTION_ALREADY_ATTEMPTED")
            self.challenge = None
            readiness = self.sources()
            if (readiness.get("owner_local_synthetic_preview_readiness",
                              readiness.get("owner_local_synthetic_source_readiness"))
                    is not True):
                raise OperatorRefused("HAE_SOVIA_SOURCES_NOT_READY")
            row = run_suite(*self.roots, approve_disposable_synthetic=False)
            if (row.get("status") != "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL"
                    or row.get("scenario_count") != 3
                    or row.get("actual_nas_verified") is not False
                    or row.get("release_gate") != "HOLD"):
                raise OperatorRefused("UNSAFE_SYNTHETIC_PREVIEW")
            self.challenge = secrets.token_hex(24)
            return {"status": "WAITING_EXPLICIT_SYNTHETIC_APPROVAL",
                    "challenge": self.challenge,
                    "intent_counts": [1, 2, 3],
                    "synthetic_writes_executed": False,
                    "actual_nas_verified": False, "release_gate": "HOLD"}

    def execute(self, challenge: str, consent: str) -> dict:
        with self.lock:
            if self.attempted or self.challenge is None:
                raise OperatorRefused("NO_PENDING_APPROVAL")
            if (type(challenge) is not str
                    or not secrets.compare_digest(challenge, self.challenge)
                    or consent != CONSENT):
                raise OperatorRefused("EXACT_DISPOSABLE_APPROVAL_REQUIRED")
            self.challenge = None
            self.attempted = True
        # Before any approved temp SQLite write, separately require DBVORA
        # as well as the two sources already checked for read-only preview.
        readiness = self.sources()
        if (readiness.get("owner_local_synthetic_execution_readiness",
                          readiness.get("owner_local_synthetic_source_readiness"))
                is not True):
            raise OperatorRefused("THREE_PINNED_SOURCES_NOT_READY_FOR_EXECUTION")
        result = run_suite(*self.roots, approve_disposable_synthetic=True,
                           output_dir=self.output)
        if (result.get("status") != "PASS_SYNTHETIC_LOCAL_ONLY"
                or result.get("scenario_count") != 3
                or result.get("actual_nas_verified") is not False
                or result.get("registered_uliya_expert_invoked") is not False
                or result.get("release_gate") != "HOLD"):
            raise OperatorRefused("SYNTHETIC_EVIDENCE_NOT_PROVEN")
        with self.lock:
            self.evidence_ready = result.get("evidence_bundle_created") is True
        return {"status": "OPERATOR_REPORTED_SYNTHETIC_PASS",
                "intent_counts": [1, 2, 3],
                "evidence_bundle_created": self.evidence_ready,
                "actual_nas_verified": False,
                "registered_uliya_expert_invoked": False, "release_gate": "HOLD"}

    def evidence(self, filename: str) -> bytes:
        """Serve only digest-matched generated synthetic evidence after approval."""
        with self.lock:
            if (not self.evidence_ready or self.output is None
                    or type(filename) is not str or filename not in EVIDENCE_FILES):
                raise OperatorRefused("EVIDENCE_NOT_AVAILABLE")
            folder = self.output
            if (folder.is_symlink() or not folder.is_dir()
                    or any(parent.is_symlink() for parent in folder.parents)):
                raise OperatorRefused("UNSAFE_EVIDENCE_ROOT")
            manifest = folder / "manifest.json"
            if (manifest.is_symlink() or not manifest.is_file()
                    or not 0 < manifest.stat().st_size <= MAX_EVIDENCE_BYTES):
                raise OperatorRefused("EVIDENCE_MANIFEST_REFUSED")
            claims = json.loads(manifest.read_text(encoding="utf-8"))
            if (type(claims) is not dict
                    or claims.get("kind") != "ugreen-four-source-synthetic-bundle.v1"
                    or claims.get("actual_nas_verified") is not False
                    or claims.get("registered_uliya_expert_invoked") is not False
                    or claims.get("release_gate") != "HOLD"
                    or type(claims.get("file_sha256")) is not dict):
                raise OperatorRefused("EVIDENCE_MANIFEST_UNVERIFIED")
            doc = folder / filename
            if (doc.is_symlink() or not doc.is_file()
                    or not 0 < doc.stat().st_size <= MAX_EVIDENCE_BYTES):
                raise OperatorRefused("EVIDENCE_FILE_UNAVAILABLE")
            data = doc.read_bytes()
            if filename != "manifest.json":
                expected = claims["file_sha256"].get(filename)
                if (type(expected) is not str
                        or hashlib.sha256(data).hexdigest() != expected):
                    raise OperatorRefused("EVIDENCE_DIGEST_MISMATCH")
            return data


HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NAS FlowPilot 3.0 — Local Integration</title><style>
:root{font:15px system-ui,Segoe UI,sans-serif;background:#071522;color:#e8f5ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(at top,#183e5c,#071522 64%)}
main{max-width:1160px;margin:auto;padding:42px 24px}
small{letter-spacing:.15em;color:#6cdeff;font-weight:800}
h1{font-size:clamp(30px,4vw,48px)}p{color:#adc4d6;line-height:1.65}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:11px;margin:30px 0}
article,section{background:#142a40;border:1px solid #315775;border-radius:13px;padding:18px}
article b{display:block;margin:10px 0}article small{color:#80c6df}
section{margin-top:22px}button{padding:12px 18px;background:#135f90;color:white;
border:1px solid #6cbad8;border-radius:9px;margin:8px 5px;cursor:pointer}
button:disabled{opacity:.4;cursor:not-allowed}
button.execute{background:#156e56;border-color:#6cdbac}
label{display:block;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;
background:#081a2a;border-radius:9px;padding:16px;max-height:310px;overflow:auto}
.notice{color:#f4c584}footer{margin-top:30px;color:#8aa5b9}
@media(max-width:880px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:550px){.grid{grid-template-columns:1fr}}
</style></head><body><main>
<small>UGREEN · OWNER LOCAL DEVELOPMENT</small><h1>NAS FlowPilot 3.0</h1>
<p>Natural-language intent → source validation → explicit approval → disposable SQLite audit.</p>
<p class="notice">LOCAL SYNTHETIC ONLY · NAS/ULIYA NOT VERIFIED · RELEASE HOLD</p>
<div class="grid">
<article><small>01</small><b>FlowPilot</b><p>1–3 bounded intents</p></article>
<article><small>02</small><b>HAE / LA</b><p>Exact Git source and isolated SQLite</p></article>
<article><small>03</small><b>SOVIA</b><p>Advisory risk review</p></article>
<article><small>04</small><b>DBVORA</b><p>Read-only synthetic schema</p></article>
<article><small>05</small><b>NAS / Uliya</b><p>NOT RUN</p></article>
</div><section><h2>Real local filesystem demo — no private checkouts needed</h2>
<p>Run the actual FlowPilot goal parser and OS metadata checks against five
automatically generated, disposable folders. No LA, SOVIA, DBVORA or NAS calls.</p>
<button id="demo">Run 1–3 intent real OS demo + missing-file cases</button>
</section><section><h2>Full pinned-source operator controls (optional)</h2>
<button id="doctor">1 · Verify source SHAs</button>
<button id="preview">2 · Preview 3 test scenarios</button>
<label><input id="agree" type="checkbox"> Approve disposable synthetic SQLite writes only</label>
<button id="execute" class="execute" disabled>3 · Run approved synthetic E2E</button>
<pre id="output" role="status" aria-live="polite">No operations performed.</pre>
<p id="reports" hidden><a href="/evidence/index.html" target="_blank" rel="noopener">
Open approved local JSON/HTML evidence dashboard</a></p>
</section>
<footer>Single-use execution. No owner file inputs, network calls, real NAS/Uliya,
Creator invocation or Devpost submission. All PASS claims are operator-reported synthetic.</footer>
<script>
const session="__SESSION__";let challenge=null;
const out=document.getElementById("output"),go=document.getElementById("execute"),
checkbox=document.getElementById("agree");
function enable(){go.disabled=!(challenge&&checkbox.checked)}
checkbox.onchange=enable;
async function request(path,data){
out.textContent="Executing local check...";
try{
 const response=await fetch(path,{method:"POST",cache:"no-store",
 headers:{"Content-Type":"application/json","X-FlowPilot-Session":session},
 body:JSON.stringify(data)});
 const result=await response.json();
 out.textContent=JSON.stringify(result,null,2);
 if(path==="/execute"&&response.ok&&result.evidence_bundle_created===true){
   document.getElementById("reports").hidden=false;
 }
 challenge=(path==="/preview"&&response.ok)?result.challenge:null;enable();
}catch(e){challenge=null;enable();out.textContent="LOCAL_REQUEST_FAILED";}
}
document.getElementById("demo").onclick=()=>request("/demo",{});
document.getElementById("doctor").onclick=()=>request("/doctor",{});
document.getElementById("preview").onclick=()=>request("/preview",{});
go.onclick=()=>{
 if(!challenge||!checkbox.checked)return;
 const ch=challenge;challenge=null;enable();
 request("/execute",{challenge:ch,consent:"I_APPROVE_DISPOSABLE_SYNTHETIC_WRITES"});
};
</script></main></body></html>"""


def handler_for(controller: Operator, session: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, payload, kind="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(payload)

        def trusted_host(self):
            return self.headers.get("Host", "") == (
                "127.0.0.1:" + str(self.server.server_port))

        def do_GET(self):
            if not self.trusted_host():
                return self.send(404, b"NOT_FOUND", "text/plain")
            if self.path == "/":
                return self.send(200, HTML.replace("__SESSION__", session).encode("utf-8"),
                                 "text/html; charset=utf-8")
            if self.path.startswith("/evidence/"):
                name = self.path[len("/evidence/"):]
                if name not in EVIDENCE_FILES:
                    return self.send(404, b"NOT_FOUND", "text/plain")
                try:
                    payload = controller.evidence(name)
                except (OSError, ValueError, TypeError, KeyError):
                    return self.send(404, b"NOT_FOUND", "text/plain")
                kind = ("text/html; charset=utf-8" if name in EVIDENCE_HTML
                        else "application/json")
                return self.send(200, payload, kind)
            return self.send(404, b"NOT_FOUND", "text/plain")

        def do_POST(self):
            origin = self.headers.get("Origin")
            if (not self.trusted_host()
                    or (origin is not None and origin != "http://127.0.0.1:" +
                        str(self.server.server_port))
                    or not secrets.compare_digest(
                        self.headers.get("X-FlowPilot-Session", ""), session)):
                return self.send(403, b'{"status":"FORBIDDEN"}')
            try:
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise OperatorRefused("JSON_REQUIRED")
                length = int(self.headers.get("Content-Length", "-1"))
                if not 2 <= length <= 512:
                    raise OperatorRefused("BODY_REFUSED")
                body = json.loads(self.rfile.read(length))
                if type(body) is not dict:
                    raise OperatorRefused("JSON_OBJECT_REQUIRED")
                if self.path == "/demo" and not body:
                    result = controller.real_os_demo()
                elif self.path == "/doctor" and not body:
                    result = controller.sources()
                elif self.path == "/preview" and not body:
                    result = controller.preview()
                elif self.path == "/execute" and set(body) == {"challenge", "consent"}:
                    result = controller.execute(body["challenge"], body["consent"])
                else:
                    raise OperatorRefused("UNKNOWN_ACTION")
                status = 200
            except Exception:
                result = {"status": "SYNTHETIC_ACTION_REFUSED",
                          "actual_nas_verified": False, "release_gate": "HOLD"}
                status = 400
            self.send(status, json.dumps(result, sort_keys=True).encode("utf-8"))
    return Handler


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Loopback synthetic FlowPilot UI, no NAS")
    for root, folder in (("hae", "HAE"), ("sovia", "SOVIA_sovereign"),
                         ("dbvora", "DBVORA")):
        p.add_argument("--" + root + "-root", type=Path,
                       default=PROJECT.parent / folder,
                       help="Optional private source root (not needed for real OS demo)")
    p.add_argument("--open-browser", action="store_true",
                   help="Open the loopback UI locally after server startup")
    p.add_argument("--demo-check", action="store_true",
                   help="Run actual local OS demo without browser or private repositories")
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--port", type=int, default=0)
    a = p.parse_args(argv)
    if not 0 <= a.port <= 65535:
        p.error("Invalid port")
    if a.demo_check:
        try:
            report = run_real_local_demo()
        except (OSError, ValueError, TypeError, RuntimeError):
            print(json.dumps({"status": "REAL_OS_DEMO_REFUSED", "release_gate": "HOLD"}))
            return 2
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    controller = Operator(a.hae_root, a.sovia_root, a.dbvora_root, a.output_dir)
    server = ThreadingHTTPServer(
        ("127.0.0.1", a.port), handler_for(controller, secrets.token_hex(32)))
    url = "http://127.0.0.1:" + str(server.server_port) + "/"
    print("OPEN_LOCAL_UI " + url, flush=True)
    if a.open_browser:
        try:
            webbrowser.open(url)
        except (OSError, RuntimeError):
            # Browser availability does not change local server safety.
            print("OPEN_BROWSER_MANUALLY " + url, flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
