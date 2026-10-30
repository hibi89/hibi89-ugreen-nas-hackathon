"""G81 FlowPilot -> HAE -> LA loopback bridge transport contract.

A real OS loopback HTTP socket and an isolated HAE-contract test server are
used. This is NOT the private HAE binary or true Lightning Azent; actual HAE
execution must be independently exercised in an authorized local environment.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_hae_bridge import (
    APPROVAL, MAX_RESPONSE_BYTES, BridgeRefused, BridgeUnavailable,
    WriteOutcomeUnknown, _request, run_bridge, main,
)
from flowpilot_csv_e2e import run_session
from flowpilot_csv_report import ReportRefused

TASK = "Import this CSV into local SQLite"
CSV = "contacts.csv"
TOKEN = "a" * 32
RUN_ID = "Gui" + "b" * 12


class StatefulHAE(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.mode = "normal"
        self.previews = 0
        self.runs = 0
        self.readbacks = 0
        self.audits = 0
        self.last_headers = {}
        self.last_approval = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_data(self, code, obj, *, content_type="application/json"):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/health":
            backend = "HAE local engine" if self.server.mode == "wrong_backend" else "Lightning Azent"
            status = 503 if self.server.mode == "unready" else 200
            return self.send_data(status, {
                "service": "HAE", "ready": status == 200,
                "engine_backend": {"name": backend, "api_version": "azent.api.v0"},
            })
        if self.path.startswith("/api/status?run_id="):
            self.server.readbacks += 1
            return self.send_data(200, {"status": "completed"})
        if self.path.startswith("/api/la-audit?run_id="):
            self.server.audits += 1
            if self.server.mode == "audit_absent":
                return self.send_data(404, {"error": "audit missing"})
            return self.send_data(200, {"run_id": RUN_ID, "approval_count": 1, "total_events": 5})
        return self.send_data(404, {"error": "missing"})

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size).decode())
        self.server.last_headers = dict(self.headers)
        if self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
            return self.send_data(403, {"error": "cross-origin"})
        if self.path == "/api/preview":
            self.server.previews += 1
            if self.server.mode == "bad_token":
                return self.send_data(200, {"validated": True,
                                            "requires_approval": True, "preview_id": "WRONG",
                                            "input": {}, "engine_backend": {"name": "Lightning Azent"}})
            return self.send_data(200, {
                "validated": True, "requires_approval": True,
                "preview_id": TOKEN, "workflow": "csv_to_sqlite",
                "input": {"row_count": 2, "column_count": 2, "size_bytes": 40,
                          "source_sha256": "should_never_disclose"},
                "engine_backend": {"name": "Lightning Azent"},
            })
        if self.path == "/api/run":
            self.server.runs += 1
            self.server.last_approval = body.get("approve_writes")
            if self.server.mode == "run_rejected" or body.get("preview_id") != TOKEN:
                return self.send_data(409, {"error": "preview expired"})
            if self.server.mode == "drop_after_write":
                self.close_connection = True
                return
            if self.server.mode == "unconfirmed":
                return self.send_data(200, {"run_id": RUN_ID,
                                            "status": {"status": "failed"},
                                            "result": {"imported_rows": 2},
                                            "backend": {"name": "Lightning Azent"}})
            return self.send_data(200, {
                "run_id": RUN_ID, "status": {"status": "completed"},
                "result": {"imported_rows": 2}, "backend": {"name": "Lightning Azent"},
            })
        return self.send_data(404, {"error": "missing"})


class HAELoopbackBridgeTests(unittest.TestCase):
    def setUp(self):
        self.service = StatefulHAE()
        self.addCleanup(self.service.server_close)
        self.thread = threading.Thread(
            target=self.service.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        self.thread.start()
        self.addCleanup(self._stop)
        self.port = self.service.server_port

    def _stop(self):
        self.service.shutdown()
        self.thread.join(timeout=3)

    def invoke(self, **extra):
        options = dict(task=TASK, csv_path=CSV, port=self.port, confirm_synthetic=True)
        options.update(extra)
        return run_bridge(**options)

    def test_no_consent_performs_no_http(self):
        with patch("flowpilot_hae_bridge._request") as request:
            with self.assertRaises(BridgeRefused):
                run_bridge(TASK, csv_path=CSV, port=self.port)
            request.assert_not_called()

    def test_invalid_port_and_path_block_before_http(self):
        for port in (0, 80, 65536, True, "8765"):
            with self.subTest(port=port), self.assertRaises(BridgeRefused):
                run_bridge(TASK, csv_path=CSV, port=port, confirm_synthetic=True)
        for name in ("../contacts.csv", "a/b.csv", r"a\b.csv", ".secrets.csv",
                     "a..csv", "contacts.txt", "안전.csv"):
            with self.subTest(name=name), self.assertRaises(BridgeRefused):
                run_bridge(TASK, csv_path=name, port=self.port, confirm_synthetic=True)
        self.assertEqual(self.service.previews, 0)

    def test_preview_is_read_only_and_returns_backend_evidence(self):
        result = self.invoke()
        self.assertEqual(result["status"], "WAITING_HAE_WRITE_APPROVAL")
        self.assertEqual(result["preview_id"], TOKEN)
        self.assertEqual(result["backend"], "Lightning Azent")
        self.assertEqual(result["input"]["row_count"], 2)
        self.assertNotIn("source_sha256", result["input"])
        self.assertFalse(result["executed"])
        self.assertEqual((self.service.previews, self.service.runs), (1, 0))
        self.assertEqual(self.service.last_headers["Origin"],
                         f"http://127.0.0.1:{self.port}")
        self.assertEqual(self.service.last_headers["Host"],
                         f"127.0.0.1:{self.port}")

    def test_separate_approval_real_loopback_http_and_audit(self):
        self.invoke()
        result = self.invoke(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(result["status"], "HAE_LA_SQLITE_AUDIT_CONFIRMED")
        self.assertEqual(result["run_id"], RUN_ID)
        self.assertTrue(result["executed"])
        self.assertTrue(result["actual_la_execution_verified"])
        self.assertFalse(result["real_nas_verified"])
        self.assertEqual(result["imported_rows"], 2)
        self.assertEqual(result["audit_events"], 5)
        self.assertEqual(self.service.runs, 1)
        self.assertEqual(self.service.readbacks, 1)
        self.assertEqual(self.service.audits, 1)
        self.assertIs(self.service.last_approval, True)

    def test_declined_does_not_connect_or_write(self):
        result = self.invoke(approval="DECLINE", preview_id=TOKEN)
        self.assertEqual(result["status"], "DECLINED")
        self.assertEqual((self.service.previews, self.service.runs), (0, 0))

    def test_bad_or_missing_preview_refuses_before_io(self):
        for token in (None, "bad", "A"*32):
            with self.subTest(token=token), self.assertRaises(BridgeRefused):
                self.invoke(approval=APPROVAL, preview_id=token)
        self.assertEqual(self.service.runs, 0)

    def test_only_la_backend_may_run(self):
        self.service.mode = "wrong_backend"
        result = self.invoke()
        self.assertEqual(result["status"], "BLOCKED_HAE_LA_BACKEND_NOT_READY")
        self.assertEqual(self.service.previews, 0)

    def test_unready_hae_is_blocked(self):
        self.service.mode = "unready"
        self.assertEqual(self.invoke()["status"], "BLOCKED_HAE_LA_BACKEND_NOT_READY")
        self.assertEqual(self.service.runs, 0)

    def test_missing_preview_token_from_hae_cannot_run(self):
        self.service.mode = "bad_token"
        self.assertEqual(self.invoke()["status"], "BLOCKED_HAE_PREVIEW_REJECTED")
        self.assertEqual(self.service.runs, 0)

    def test_hae_expired_token_refuses_without_retry(self):
        self.service.mode = "run_rejected"
        response = self.invoke(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(response["status"], "BLOCKED_HAE_EXECUTION_REJECTED")
        self.assertEqual(response["http_status"], 409)
        self.assertEqual(self.service.runs, 1)

    def test_after_commit_connection_drop_is_unknown_without_retry(self):
        self.service.mode = "drop_after_write"
        response = self.invoke(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(response["status"], "EXECUTION_OUTCOME_UNKNOWN")
        self.assertTrue(response["do_not_retry_automatically"])
        self.assertEqual(self.service.runs, 1)

    def test_after_write_audit_absent_preserves_write_result(self):
        self.service.mode = "audit_absent"
        response = self.invoke(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(response["status"], "EXECUTED_AUDIT_NOT_VERIFIED")
        self.assertTrue(response["executed"])
        self.assertFalse(response["actual_la_execution_verified"])
        self.assertEqual(self.service.runs, 1)

    def test_unconfirmed_execution_does_not_claim_la(self):
        self.service.mode = "unconfirmed"
        response = self.invoke(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(response["status"], "EXECUTION_NOT_CONFIRMED")
        self.assertFalse(response["actual_la_execution_verified"])
        self.assertEqual(self.service.runs, 1)

    def test_unknown_local_service_is_blocked(self):
        with patch("flowpilot_hae_bridge._request", side_effect=BridgeUnavailable("nope")):
            response = self.invoke()
        self.assertEqual(response["status"], "BLOCKED_HAE_UNAVAILABLE")

    def test_duplicate_response_key_and_overlarge_request_refused(self):
        with self.assertRaises(BridgeRefused):
            _request(self.port, "POST", "/arbitrary", {"task": TASK})
        with self.assertRaises(BridgeRefused):
            _request(self.port, "POST", "/api/preview", {"task": "X"*MAX_RESPONSE_BYTES})

    def test_flowpilot_single_cli_backend_uses_bridge(self):
        pre = run_session(TASK, backend="hae-la-loopback",
                          hae_port=self.port, hae_csv=CSV,
                          confirm_synthetic=True)
        self.assertEqual(pre["status"], "WAITING_HAE_WRITE_APPROVAL")
        self.assertFalse(pre["actual_nas_integrated"])
        end = run_session(TASK, backend="hae-la-loopback",
                          hae_port=self.port, hae_csv=CSV, preview_id=pre["preview_id"],
                          approval=APPROVAL, confirm_synthetic=True)
        self.assertEqual(end["status"], "HAE_LA_SQLITE_AUDIT_CONFIRMED")
        self.assertTrue(end["actual_la_execution_verified"])

    def test_hae_backend_cannot_mix_local_csv_or_metadata_options(self):
        with self.assertRaises(ReportRefused):
            run_session(TASK, backend="hae-la-loopback", root=Path("/tmp"),
                        hae_csv=CSV, hae_port=self.port, confirm_synthetic=True)
        with self.assertRaises(ReportRefused):
            run_session(TASK, backend="hae-la-loopback", required=["README.md"],
                        hae_csv=CSV, hae_port=self.port, confirm_synthetic=True)
        with self.assertRaises(ReportRefused):
            run_session(TASK, backend="projectready-local-metadata",
                        hae_port=self.port)
        self.assertEqual(self.service.runs, 0)

    def test_cli_preview_execution_and_exit(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            rc = main(["--task", TASK, "--csv", CSV, "--port", str(self.port),
                       "--confirm-synthetic"])
        self.assertEqual(rc, 0)
        pre = json.loads(capture.getvalue())
        self.assertEqual(pre["preview_id"], TOKEN)
        capture = io.StringIO()
        with redirect_stdout(capture):
            rc = main(["--task", TASK, "--csv", CSV, "--port", str(self.port),
                       "--confirm-synthetic", "--approval", APPROVAL, "--preview-id", TOKEN])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(capture.getvalue())["status"],
                         "HAE_LA_SQLITE_AUDIT_CONFIRMED")

    def test_cli_missing_synthetic_approval_refused(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            rc = main(["--task", TASK, "--csv", CSV, "--port", str(self.port)])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(capture.getvalue())["status"], "BRIDGE_REFUSED")
        self.assertEqual(self.service.previews, 0)


if __name__ == "__main__":
    unittest.main()
