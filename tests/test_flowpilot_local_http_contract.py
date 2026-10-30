"""Real loopback HTTP regressions; no NAS, credentials or private source imports."""
from __future__ import annotations

import hashlib
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from tools.flowpilot_four_source_local_ui import CONSENT, Operator, handler_for


class LocalHTTPContractTests(unittest.TestCase):
    def setUp(self):
        self.operator = Operator(Path("/hae"), Path("/sovia"), Path("/dbvora"))
        self.session = "fixed-test-session-only"
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), handler_for(self.operator, self.session),
        )
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self._close)

    def _close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method: str, path: str, *, data=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            supplied = dict(headers or {})
            if data is not None:
                supplied.setdefault("Content-Type", "application/json")
            payload = json.dumps(data).encode("utf-8") if data is not None else None
            connection.request(method, path, body=payload, headers=supplied)
            response = connection.getresponse()
            return (response.status, response.read(), dict(response.getheaders()))
        finally:
            connection.close()

    def authorized(self, path, data):
        return self.request("POST", path, data=data, headers={
            "X-FlowPilot-Session": self.session,
            "Origin": f"http://127.0.0.1:{self.port}",
        })

    def test_home_page_is_loopback_only_with_security_headers(self):
        status, payload, headers = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"NAS/ULIYA NOT VERIFIED", payload)
        self.assertIn(self.session.encode(), payload)
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_real_os_demo_endpoint_works_without_private_checkouts(self):
        with patch.object(self.operator, "sources",
                          side_effect=AssertionError("PRIVATE_CHECKOUT_ACCESSED")):
            status, body, _ = self.authorized("/demo", {})
        self.assertEqual(status, 200)
        row = json.loads(body)
        self.assertEqual(row["status"], "PASS_REAL_OS_LSTAT_SYNTHETIC_DEMO")
        self.assertEqual(row["scenario_count"], 5)
        self.assertFalse(row["actual_nas_verified"])

    def test_selected_local_folder_requires_preview_and_explicit_approval(self):
        with tempfile.TemporaryDirectory(prefix="ugreen-http-owner-") as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("synthetic generated file")
            preview_req = {
                "goal": "파일 누락 확인", "root": str(root),
                "required": ["README.md"], "candidates": None,
                "confirm_local_only": True,
            }
            self.assertEqual(self.authorized("/owner/execute", {
                "approval_token": "none", "consent": "APPROVE_LOCAL_METADATA_LSTAT"
            })[0], 400)
            status, payload, _ = self.authorized("/owner/preview", preview_req)
            self.assertEqual(status, 200)
            ticket = json.loads(payload)["approval_token"]
            bad, _, _ = self.authorized("/owner/execute", {
                "approval_token": ticket, "consent": "NOT_APPROVED"
            })
            self.assertEqual(bad, 400)
            good, body, _ = self.authorized("/owner/execute", {
                "approval_token": ticket, "consent": "APPROVE_LOCAL_METADATA_LSTAT"
            })
            self.assertEqual(good, 200)
            result = json.loads(body)
            self.assertEqual(result["finding_counts"]["PRESENT"], 1)
            self.assertEqual(result["stage_results"][0]["items"][0],
                             {"item_index": 1, "state": "PRESENT"})
            self.assertNotIn(str(root), body.decode("utf-8"))
            self.assertNotIn("README.md", body.decode("utf-8"))
            self.assertEqual(self.authorized("/owner/execute", {
                "approval_token": ticket, "consent": "APPROVE_LOCAL_METADATA_LSTAT"
            })[0], 400)

    def test_actual_csv_pipeline_via_local_http_approval_and_sha_download(self):
        self.assertEqual(self.request("GET", "/csv/report.csv")[0], 403)
        self.assertEqual(self.request("GET", "/csv/report.csv", headers={
            "X-FlowPilot-Session": self.session,
        })[0], 404)
        preview_status, preview_data, _ = self.authorized("/csv/configure", {
            "output": "summary.csv",
        })
        self.assertEqual(preview_status, 200)
        preview = json.loads(preview_data)
        self.assertTrue(preview["workflow_preview_ready"])
        self.assertFalse(preview["csv_created"])
        status, payload, _ = self.authorized("/csv/approve", {})
        self.assertEqual(status, 200, payload)
        result = json.loads(payload)
        self.assertEqual(result["status"], "LOCAL_REPORT_CREATED_NOT_NAS")
        self.assertTrue(result["audit_recorded"])
        self.assertFalse(result["nas_verified"])
        report_status, csv_bytes, _ = self.request("GET", "/csv/report.csv", headers={
            "X-FlowPilot-Session": self.session,
        })
        self.assertEqual(report_status, 200)
        self.assertIn(b"alice,5.00", csv_bytes)
        self.assertIn(b"bob,6.00", csv_bytes)
        self.assertEqual(hashlib.sha256(csv_bytes).hexdigest(),
                         result["report_sha256"])
        self.assertEqual(self.authorized("/csv/approve", {})[0], 400)

    def test_generated_csv_rejects_unknown_output_before_write(self):
        self.assertEqual(self.authorized("/csv/configure", {
            "output": "../secret.csv",
        })[0], 400)
        self.assertEqual(self.authorized("/csv/approve", {})[0], 400)
        self.assertEqual(self.request("GET", "/csv/report.csv", headers={
            "X-FlowPilot-Session": self.session,
        })[0], 404)

    def test_all_report_files_inaccessible_before_success(self):
        for name in ("index.html", "proof-1.html", "proof-1.json", "manifest.json"):
            with self.subTest(name=name):
                self.assertEqual(self.request("GET", "/evidence/" + name)[0], 404)

    def test_bad_session_and_origin_never_call_doctor(self):
        with patch.object(self.operator, "sources",
                          side_effect=AssertionError("SHOULD_NOT_BE_CALLED")) as mocked:
            self.assertEqual(self.request("POST", "/doctor", data={})[0], 403)
            self.assertEqual(self.request("POST", "/doctor", data={}, headers={
                "X-FlowPilot-Session": self.session,
                "Origin": "https://malicious.example",
            })[0], 403)
            self.assertEqual(self.request("POST", "/doctor", data={}, headers={
                "X-FlowPilot-Session": self.session,
                "Host": "malicious.example",
            })[0], 403)
            mocked.assert_not_called()

    def test_valid_doctor_json_and_bounded_fail_closed(self):
        with patch.object(self.operator, "sources", return_value={
            "status": "BLOCKED", "actual_nas_verified": False,
            "release_gate": "HOLD",
        }):
            status, payload, _ = self.authorized("/doctor", {})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload)["status"], "BLOCKED")
        self.assertEqual(self.authorized("/execute", {})[0], 400)
        self.assertEqual(self.authorized("/unrecognized", {})[0], 400)

    def test_preview_then_approved_execution_cannot_be_replayed(self):
        def fake_suite(*args, **kwargs):
            if kwargs["approve_disposable_synthetic"]:
                return {
                    "status": "PASS_SYNTHETIC_LOCAL_ONLY", "scenario_count": 3,
                    "actual_nas_verified": False,
                    "registered_uliya_expert_invoked": False,
                    "evidence_bundle_created": False, "release_gate": "HOLD",
                }
            return {
                "status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                "scenario_count": 3, "actual_nas_verified": False,
                "release_gate": "HOLD",
            }
        with (patch.object(self.operator, "sources",
                           return_value={"owner_local_synthetic_source_readiness": True}),
              patch("tools.flowpilot_four_source_local_ui.run_suite",
                    side_effect=fake_suite) as called):
            status, payload, _ = self.authorized("/preview", {})
            self.assertEqual(status, 200)
            token = json.loads(payload)["challenge"]
            self.assertEqual(self.authorized("/execute", {
                "challenge": token, "consent": "NO",
            })[0], 400)
            ok, body, _ = self.authorized("/execute", {
                "challenge": token, "consent": CONSENT,
            })
            self.assertEqual(ok, 200)
            self.assertEqual(json.loads(body)["status"], "OPERATOR_REPORTED_SYNTHETIC_PASS")
            self.assertEqual(self.authorized("/execute", {
                "challenge": token, "consent": CONSENT,
            })[0], 400)
            self.assertEqual(called.call_count, 2)
            self.assertEqual(self.request("GET", "/evidence/index.html")[0], 404)

    def test_evidence_allowlist_digest_and_path_traversal(self):
        with tempfile.TemporaryDirectory(prefix="ugreen-http-proof-") as tmp:
            root = Path(tmp) / "proof"
            root.mkdir()
            body = b"<h1>Synthetic counts only</h1>"
            (root / "index.html").write_bytes(body)
            (root / "manifest.json").write_text(json.dumps({
                "kind": "ugreen-four-source-synthetic-bundle.v1",
                "actual_nas_verified": False,
                "registered_uliya_expert_invoked": False,
                "release_gate": "HOLD",
                "file_sha256": {"index.html": hashlib.sha256(body).hexdigest()},
            }))
            self.operator.output = root
            self.operator.evidence_ready = True
            status, payload, _ = self.request("GET", "/evidence/index.html")
            self.assertEqual((status, payload), (200, body))
            for path in ("/evidence/../manifest.json",
                         "/evidence/private.txt", "/evidence/.git/config"):
                self.assertEqual(self.request("GET", path)[0], 404)
            (root / "index.html").write_bytes(b"altered")
            self.assertEqual(self.request("GET", "/evidence/index.html")[0], 404)


if __name__ == "__main__":
    unittest.main()
