"""G167 real localhost HTTP + SQLite acceptance: disposable synthetic data only.

No NAS, vendor SDK, external network, existing owner DB or 3-hour trial.
A PASS never implies Chrome/Uliya/NAS readiness.
"""
from __future__ import annotations
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
import threading

from flowpilot_local_backend import Backend, create_server


def run_preflight():
    passed = []
    with TemporaryDirectory(prefix="flowpilot-g167-local-") as temp:
        folder = Path(temp) / "synthetic-non-nas-root"
        folder.mkdir()
        fixture = folder / "README.md"
        fixture.write_bytes(b"G167 synthetic read-only acceptance\n")
        original = fixture.read_bytes()
        db = Path(temp) / "disposable.sqlite"
        token = secrets.token_urlsafe(48)  # never log or persist
        backend = Backend(db, create=True, metadata_root=folder)
        server = create_server(backend, token, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def call(method, route, body=None, *, auth=True, origin=None):
            headers = {"Host": f"127.0.0.1:{server.server_port}"}
            if auth:
                headers["Authorization"] = "Bearer " + token
            if origin:
                headers["Origin"] = origin
            data = None
            if body is not None:
                headers["Content-Type"] = "application/json"
                data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                client.request(method, route, body=data, headers=headers)
                response = client.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                client.close()

        def expect(status, result, case):
            if result[0] != status:
                raise RuntimeError(f"{case}: expected HTTP {status}, got {result[0]}")
            passed.append(case)
            return result

        def parsed(result):
            return json.loads(result[2].decode("utf-8"))

        try:
            expect(403, call("GET", "/v1/health", auth=False), "AUTH_DENIED")
            expect(403, call("GET", "/v1/health",
                             origin="https://evil.invalid"), "ORIGIN_DENIED")
            health = parsed(expect(200, call("GET", "/v1/health"), "HEALTH"))
            if health.get("release_gate") != "HOLD" or health.get("nas_verified") is not False:
                raise RuntimeError("health incorrectly claims NAS readiness")
            for path in ("/dashboard", "/dashboard.css", "/dashboard.js"):
                asset = expect(200, call("GET", path, auth=False), "ASSET_" + path.rsplit("/", 1)[-1])
                if not asset[2] or asset[1].get("Cache-Control") != "no-store":
                    raise RuntimeError("dashboard asset missing or cacheable")
            created = parsed(expect(200, call("POST", "/v1/workflows", {
                "goal": "check required files", "request_id": "req_g167preflight1234"
            }), "CREATE"))
            wid, digest = created["workflow_id"], created["plan_sha256"]
            if created["status"] != "PLANNED" or created.get("nas_verified") is not False:
                raise RuntimeError("unexpected create state")
            route = "/v1/workflows/" + wid
            expect(409, call("POST", route + "/run", {}), "UNAPPROVED_RUN_DENIED")
            plan = parsed(expect(200, call("GET", route + "/plan"), "PLAN"))
            if plan["plan_sha256"] != digest:
                raise RuntimeError("plan hash mismatch")
            tested = parsed(expect(200, call("POST", route + "/test", {}), "COUNCIL"))
            if tested["status"] != "TESTED":
                raise RuntimeError("council not TESTED")
            expect(403, call("POST", route + "/approve", {
                "plan_sha256": digest, "acknowledgement": "APPROVE_REAL_NAS"
            }), "NAS_APPROVAL_DENIED")
            approved = parsed(expect(200, call("POST", route + "/approve", {
                "plan_sha256": digest, "acknowledgement": "APPROVE_SYNTHETIC_ONLY"
            }), "SYNTHETIC_APPROVED"))
            if approved["status"] != "APPROVED_SYNTHETIC":
                raise RuntimeError("missing synthetic approval")
            executed = parsed(expect(200, call("POST", route + "/run", {}), "SYNTHETIC_RUN"))
            if executed["status"] != "COMPLETE_LOCAL_SYNTHETIC":
                raise RuntimeError("synthetic run incomplete")
            repeated = parsed(expect(200, call("POST", route + "/run", {}), "IDEMPOTENT_RUN"))
            if repeated["event_count"] != executed["event_count"]:
                raise RuntimeError("run replay changed event chain")
            audit = parsed(expect(200, call("GET", route + "/audit"), "AUDIT"))
            if audit["execution_evidence_integrity"] != "LOCAL_CHAIN_INTACT":
                raise RuntimeError("audit not intact")
            evidence = parsed(expect(200, call("GET", route + "/evidence"), "EVIDENCE"))
            if evidence["status"] != "LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS":
                raise RuntimeError("evidence not local synthetic")
            report = expect(200, call("GET", route + "/report"), "CSV_SHA")
            if not report[2] or sha256(report[2]).hexdigest() != report[1].get(
                    "X-Flowpilot-Content-SHA256"):
                raise RuntimeError("CSV SHA mismatch")
            review = parsed(expect(200, call("POST", "/v1/local-metadata/preview", {
                "goal": "check required files", "required": ["README.md", "missing.pdf"]
            }), "METADATA_PREVIEW"))
            if review["status"] != "WAITING_APPROVAL" or review["inspection_result"] is not None:
                raise RuntimeError("preview accessed local files")
            ticket = {"review_id": review["review_id"], "scope_sha256": review["scope_sha256"]}
            expect(403, call("POST", "/v1/local-metadata/approve", {
                **ticket, "acknowledgement": "APPROVE_REAL_NAS"
            }), "METADATA_WRONG_ACK_DENIED")
            findings = parsed(expect(200, call("POST", "/v1/local-metadata/approve", {
                **ticket, "acknowledgement": "APPROVE_LOCAL_METADATA_READ_ONLY"
            }), "METADATA_APPROVED_ONCE"))
            if findings["status"] != "LOCAL_METADATA_BLOCKED" or findings["inspection_result"] != [
                {"index": 1, "state": "PRESENT"}, {"index": 2, "state": "MISSING"}
            ]:
                raise RuntimeError("metadata findings mismatch")
            expect(409, call("POST", "/v1/local-metadata/approve", {
                **ticket, "acknowledgement": "APPROVE_LOCAL_METADATA_READ_ONLY"
            }), "METADATA_REPLAY_DENIED")
            if fixture.read_bytes() != original:
                raise RuntimeError("local fixture was changed")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        saved = Backend(db).get(wid)
        if (saved["status"] != "COMPLETE_LOCAL_SYNTHETIC"
                or saved["receipt_sha256"] != executed["receipt_sha256"]):
            raise RuntimeError("SQLite restart receipt mismatch")
        passed.append("SQLITE_RESTART_READBACK")
    return {"status": "LOCAL_SYNTHETIC_ACCEPTANCE_PASS_NOT_NAS",
            "checks": len(passed), "verified_cases": passed,
            "real_browser_verified": False, "real_nas_verified": False,
            "trial_started": False, "release_gate": "HOLD"}


def main():
    try:
        print(json.dumps(run_preflight(), ensure_ascii=True, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "LOCAL_PREFLIGHT_FAILED",
                          "error_type": type(exc).__name__, "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
