"""G82: uncertain write NEVER becomes a blind retry; read-only HAE audit recovery.

The test server is an intentionally synthetic HAE protocol double, NOT the
private HAE / native LA executable. Exercises real 127.0.0.1 HTTP sockets and
malformed replies after a simulated completed write.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_hae_bridge import (
    APPROVAL, BridgeRefused, _request, main, reconcile_run, run_bridge,
)
from flowpilot_csv_e2e import run_session
from flowpilot_csv_report import ReportRefused

RUN = "Gui" + "b" * 12
OTHER = "Gui" + "c" * 12
TOKEN = "a" * 32
TASK = "Import this CSV into local SQLite"
CSV = "contacts.csv"


class TestHAE(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.mode = "normal"
        self.rows = 2
        self.runs = 0
        self.previews = 0
        self.status_reads = 0
        self.audit_reads = 0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_raw(self, status, body: bytes, content_type="application/json"):
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def reply(self, status, payload):
        self.send_raw(status, json.dumps(payload).encode())

    def do_GET(self):
        if self.path == "/api/health":
            self.reply(200, {
                "service": "HAE", "ready": True,
                "engine_backend": {
                    "name": "Lightning Azent",
                    "api_version": "bad-version" if self.server.mode == "bad_version"
                                   else "azent.api.v0",
                },
            })
        elif self.path.startswith("/api/status?run_id="):
            self.server.status_reads += 1
            if self.server.mode == "missing_status":
                return self.reply(404, {"error": "no run"})
            self.reply(200, {
                "run_id": OTHER if self.server.mode == "wrong_status_id" else RUN,
                "status": "failed" if self.server.mode == "failed_status" else "completed",
            })
        elif self.path.startswith("/api/la-audit?run_id="):
            self.server.audit_reads += 1
            if self.server.mode == "missing_audit":
                return self.reply(404, {"error": "no audit"})
            self.reply(200, {
                "run_id": OTHER if self.server.mode == "wrong_audit_id" else RUN,
                "approval_count": 1, "total_events": 5,
            })
        else:
            self.reply(404, {"error": "unknown"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        if self.headers.get("Origin") != "http://127.0.0.1:" + str(self.server.server_port):
            return self.reply(403, {"error": "cross-origin"})
        if self.path == "/api/preview":
            self.server.previews += 1
            return self.reply(200, {
                "validated": True,
                "requires_approval": True,
                "preview_id": TOKEN,
                "pending_run_id": "wrong" if self.server.mode == "bad_pending_id"
                                  else RUN,
                "workflow": "csv_to_sqlite",
                "input": {"row_count": 2, "column_count": 2, "size_bytes": 40},
                "engine_backend": {"name": "Lightning Azent"},
            })
        if self.path != "/api/run":
            return self.reply(404, {"error": "unknown"})
        self.server.runs += 1
        if body.get("preview_id") != TOKEN or body.get("approve_writes") is not True:
            return self.reply(403, {"error": "no approval"})
        if body.get("pending_run_id") not in (None, RUN):
            return self.reply(409, {"error": "pending run ID differs from approved preview"})
        if self.server.mode == "prewrite_409":
            return self.reply(409, {"error": "preview expired or no longer matches the request"})
        if self.server.mode == "postwrite_500":
            return self.reply(500, {"error": "run failed after write"})
        if self.server.mode == "postwrite_422":
            return self.reply(422, {"error": "local workflow failed"})
        if self.server.mode == "postwrite_409":
            return self.reply(409, {"error": "unexpected commit conflict"})
        if self.server.mode == "drop":
            self.close_connection = True
            return
        if self.server.mode == "bad_json":
            return self.send_raw(200, b"{invalid")
        if self.server.mode == "duplicate_json":
            return self.send_raw(200, b'{"run_id":"a","run_id":"b"}')
        if self.server.mode == "wrong_type":
            return self.send_raw(200, b"OK", "text/plain")
        if self.server.mode == "redirect":
            return self.reply(302, {"error": "redirect"})
        if self.server.mode == "huge":
            return self.send_raw(200, b"x" * 40000)
        self.reply(200, {
            "run_id": OTHER if self.server.mode == "mismatch" else RUN,
            "status": {"status": "completed"},
            "result": {"imported_rows": 2},
            "backend": {"name": "Lightning Azent"},
        })


class G82RecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.server = TestHAE()
        self.addCleanup(self.server.server_close)
        self.worker = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
            daemon=True)
        self.worker.start()
        self.addCleanup(self.stop)
        self.port = self.server.server_port

    def stop(self):
        self.server.shutdown()
        self.worker.join(timeout=3)

    def call(self, **opts):
        request = {
            "csv_path": CSV, "port": self.port, "confirm_synthetic": True,
        }
        request.update(opts)
        return run_bridge(TASK, **request)

    def pending(self):
        prior_writes = self.server.runs
        result = self.call()
        self.assertEqual(result["status"], "WAITING_HAE_WRITE_APPROVAL")
        self.assertEqual(result["pending_run_id"], RUN)
        self.assertEqual(self.server.runs, prior_writes,
                         "Preview must never create a write")
        return result

    def approve(self, preview):
        return self.call(
            approval=APPROVAL, preview_id=preview["preview_id"],
            pending_run_id=preview["pending_run_id"])

    def test_healthy_preview_exposes_run_id_but_writes_nothing(self):
        first = self.pending()
        self.assertEqual(first["preview_id"], TOKEN)
        self.assertEqual((self.server.previews, self.server.runs), (1, 0))

    def test_approved_write_must_match_bound_run_id(self):
        preview = self.pending()
        done = self.approve(preview)
        self.assertEqual(done["status"], "HAE_LA_SQLITE_AUDIT_CONFIRMED")
        self.assertEqual(self.server.runs, 1)
        self.assertEqual(self.server.audit_reads, 1)

    def test_bad_preview_run_id_rejected_without_writes(self):
        self.server.mode = "bad_pending_id"
        self.assertEqual(self.call()["status"], "BLOCKED_HAE_PREVIEW_REJECTED")
        self.assertEqual(self.server.runs, 0)

    def test_invalid_approval_pending_run_id_fails_before_io(self):
        for invalid in ("wrong", 123, True, "Gui" + "0" * 13):
            with self.subTest(value=invalid), self.assertRaises(BridgeRefused):
                self.call(approval=APPROVAL, preview_id=TOKEN, pending_run_id=invalid)
        self.assertEqual(self.server.runs, 0)

    def test_wrong_api_version_refuses_before_preview(self):
        self.server.mode = "bad_version"
        self.assertEqual(self.call()["status"], "BLOCKED_HAE_LA_BACKEND_NOT_READY")
        self.assertEqual((self.server.previews, self.server.runs), (0, 0))

    def test_readonly_reconcile_does_not_post_write(self):
        report = reconcile_run(self.port, RUN, confirm_synthetic=True)
        self.assertEqual(report["status"], "HAE_LA_AUDIT_RECONCILED")
        self.assertTrue(report["executed"])
        self.assertFalse(report["actual_la_execution_verified"])
        self.assertTrue(report["do_not_retry_automatically"])
        self.assertEqual(self.server.runs, 0)
        self.assertEqual((self.server.status_reads, self.server.audit_reads), (1, 1))

    def test_readonly_reconcile_requires_confirmation_and_exact_id(self):
        with self.assertRaises(BridgeRefused):
            reconcile_run(self.port, RUN)
        with self.assertRaises(BridgeRefused):
            reconcile_run(self.port, "Gui" + "z" * 12, confirm_synthetic=True)
        self.assertEqual(self.server.runs, 0)

    def test_readonly_reconcile_denied_when_no_matching_durable_receipt(self):
        for mode in ("missing_status", "wrong_status_id", "failed_status",
                     "missing_audit", "wrong_audit_id"):
            with self.subTest(mode=mode):
                self.server.mode = mode
                report = reconcile_run(self.port, RUN, confirm_synthetic=True)
                self.assertEqual(report["status"], "EXECUTION_OUTCOME_UNKNOWN")
                self.assertFalse(report["executed"])
                self.assertTrue(report["do_not_retry_automatically"])
        self.assertEqual(self.server.runs, 0)

    def test_postwrite_http_5xx_422_409_only_reconcile_readonly(self):
        for mode in ("postwrite_500", "postwrite_422", "postwrite_409"):
            with self.subTest(mode=mode):
                self.server.mode = mode
                preview = self.pending()
                before = self.server.runs
                report = self.approve(preview)
                self.assertEqual(report["status"], "HAE_LA_AUDIT_RECONCILED")
                self.assertTrue(report["do_not_retry_automatically"])
                self.assertEqual(self.server.runs, before + 1)
                self.assertEqual(report["run_id"], RUN)

    def test_postwrite_corrupt_reply_and_redirect_never_retry(self):
        for mode in ("bad_json", "duplicate_json", "wrong_type", "redirect", "huge"):
            with self.subTest(mode=mode):
                self.server.mode = mode
                before = self.server.runs
                preview = self.pending()
                report = self.approve(preview)
                self.assertEqual(report["status"], "HAE_LA_AUDIT_RECONCILED")
                self.assertEqual(self.server.runs, before + 1)
                self.assertTrue(report["do_not_retry_automatically"])

    def test_drop_after_commit_reconciles_with_run_id(self):
        self.server.mode = "drop"
        preview = self.pending()
        report = self.approve(preview)
        self.assertEqual(report["status"], "HAE_LA_AUDIT_RECONCILED")
        self.assertEqual(self.server.runs, 1)

    def test_drop_with_unavailable_audit_returns_unknown_not_blocked(self):
        self.server.mode = "drop"
        preview = self.pending()
        self.server.mode = "drop"
        # Simulate unavailability of the read-only audit after transport loss.
        from unittest.mock import patch
        from flowpilot_hae_bridge import BridgeUnavailable
        original = _request
        def error_audit(port, method, route, *args, **kwargs):
            if method == "GET" and route.startswith("/api/la-audit"):
                raise BridgeUnavailable("audit offline")
            return original(port, method, route, *args, **kwargs)
        with patch("flowpilot_hae_bridge._request", side_effect=error_audit):
            report = self.approve(preview)
        self.assertEqual(report["status"], "EXECUTION_OUTCOME_UNKNOWN")
        self.assertEqual(report["run_id"], RUN)
        self.assertEqual(self.server.runs, 1)
        self.assertTrue(report["do_not_retry_automatically"])

    def test_missing_pending_id_legacy_fails_safe_after_500(self):
        self.server.mode = "postwrite_500"
        report = self.call(approval=APPROVAL, preview_id=TOKEN)
        self.assertEqual(report["status"], "EXECUTION_OUTCOME_UNKNOWN")
        self.assertEqual(report["recovery"], "REQUIRES_HAE_PREVIEW_RUN_ID")
        self.assertEqual(self.server.runs, 1)
        self.assertEqual(self.server.status_reads, 0)

    def test_confirmed_early_preview_rejection_does_not_claim_commit(self):
        self.server.mode = "prewrite_409"
        report = self.call(approval=APPROVAL, preview_id=TOKEN,
                           pending_run_id=RUN)
        self.assertEqual(report["status"], "BLOCKED_HAE_EXECUTION_REJECTED")
        self.assertFalse(report["executed"])
        self.assertEqual(self.server.runs, 1)

    def test_pending_run_id_must_match_exact_server_preview_before_write(self):
        preview = self.pending()
        response = self.call(
            approval=APPROVAL, preview_id=preview["preview_id"],
            pending_run_id=OTHER)
        self.assertEqual(response["status"], "BLOCKED_HAE_EXECUTION_REJECTED")
        self.assertFalse(response["executed"])
        self.assertEqual(self.server.status_reads, 0)
        self.assertEqual(self.server.audit_reads, 0)
        self.assertTrue(response["do_not_retry_automatically"])

    def test_mismatched_postwrite_run_id_reconciles_original_only(self):
        self.server.mode = "mismatch"
        report = self.call(approval=APPROVAL, preview_id=TOKEN, pending_run_id=RUN)
        self.assertEqual(report["status"], "HAE_LA_AUDIT_RECONCILED")
        self.assertEqual(report["run_id"], RUN)
        self.assertEqual(self.server.runs, 1)

    def test_cli_readonly_mode_does_not_allow_mixed_write_request(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            code = main(["--port", str(self.port), "--confirm-synthetic",
                         "--reconcile-run-id", RUN])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(capture.getvalue())["status"],
                         "HAE_LA_AUDIT_RECONCILED")
        capture = io.StringIO()
        with redirect_stdout(capture):
            code = main(["--port", str(self.port), "--confirm-synthetic",
                         "--reconcile-run-id", RUN, "--task", TASK])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(capture.getvalue())["status"], "BRIDGE_REFUSED")
        self.assertEqual(self.server.runs, 0)

    def test_flowpilot_cli_passes_exact_pending_run_id_to_bridge(self):
        preview = run_session(
            TASK, backend="hae-la-loopback", hae_csv=CSV, hae_port=self.port,
            confirm_synthetic=True)
        self.assertEqual(preview["pending_run_id"], RUN)
        self.server.mode = "postwrite_500"
        result = run_session(
            TASK, backend="hae-la-loopback", hae_csv=CSV, hae_port=self.port,
            preview_id=preview["preview_id"], hae_pending_run_id=preview["pending_run_id"],
            approval=APPROVAL, confirm_synthetic=True)
        self.assertEqual(result["status"], "HAE_LA_AUDIT_RECONCILED")
        self.assertFalse(result["actual_nas_integrated"])
        with self.assertRaises(ReportRefused):
            run_session(
                TASK, backend="projectready-local-metadata", hae_pending_run_id=RUN)


if __name__ == "__main__":
    unittest.main()
