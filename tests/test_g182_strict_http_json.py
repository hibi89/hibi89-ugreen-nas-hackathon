"""G182: actual loopback HTTP JSON consent/telemetry ambiguity regressions.

Synthetic local SQLite only: no NAS, vendor code, owner files or external API.
"""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_local_backend import Backend, create_server

TOKEN = "g182" * 12


class G182StrictJsonHttpTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.backend = Backend(Path(tmp.name) / "g182.sqlite", create=True)
        self.server = create_server(self.backend, TOKEN, port=0)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.host = "127.0.0.1:" + str(self.server.server_port)

    def post_raw(self, path, payload):
        conn = http.client.HTTPConnection("127.0.0.1",
                                          self.server.server_port, timeout=4)
        try:
            conn.request("POST", path, body=payload,
                         headers={"Host": self.host,
                                  "Content-Type": "application/json",
                                  "Authorization": "Bearer " + TOKEN})
            result = conn.getresponse()
            return result.status, json.loads(result.read())
        finally:
            conn.close()

    def test_duplicate_consent_key_cannot_turn_false_into_true(self):
        code, data = self.post_raw(
            "/v1/advice",
            b'{"telemetry":{"disk_used_percent":96},"opt_in":false,"opt_in":true}')
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_reversed_duplicate_consent_is_rejected_too(self):
        code, data = self.post_raw(
            "/v1/advice",
            b'{"opt_in":true,"telemetry":{"disk_used_percent":96},"opt_in":false}')
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_nested_duplicate_telemetry_key_is_rejected(self):
        code, data = self.post_raw(
            "/v1/advice",
            b'{"telemetry":{"disk_used_percent":1,"disk_used_percent":96},"opt_in":true}')
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_nonfinite_telemetry_values_are_invalid_json(self):
        for value in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(value=value):
                code, data = self.post_raw(
                    "/v1/advice",
                    b'{"telemetry":{"disk_used_percent":' + value +
                    b'},"opt_in":true}')
                self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_non_utf8_json_is_refused(self):
        payload = '{"telemetry":{},"opt_in":false}'.encode("utf-16")
        code, data = self.post_raw("/v1/advice", payload)
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_trailing_second_json_object_refused(self):
        code, data = self.post_raw(
            "/v1/advice", b'{"telemetry":{},"opt_in":false} {"opt_in":true}')
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))

    def test_duplicate_idempotency_request_has_no_db_side_effect(self):
        code, data = self.post_raw(
            "/v1/workflows",
            b'{"goal":"check required files","request_id":"req_g182123456",'
            b'"request_id":"req_g182999999"}')
        self.assertEqual((code, data["error"]), (400, "INVALID_JSON"))
        self.assertEqual(self.backend.list()["count"], 0)

    def test_unique_false_consent_keeps_advice_disabled(self):
        code, data = self.post_raw(
            "/v1/advice",
            b'{"telemetry":{"disk_used_percent":96},"opt_in":false}')
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "DISABLED_NO_CONSENT")
        self.assertEqual(data["suggestions"], [])

    def test_unique_true_consent_returns_suggestions_without_actions(self):
        code, data = self.post_raw(
            "/v1/advice",
            b'{"telemetry":{"disk_used_percent":96},"opt_in":true}')
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "SUGGESTIONS_READY")
        self.assertEqual(data["suggestion_count"], 1)
        self.assertFalse(data["actions_executed"])
        self.assertFalse(data["nas_polled"])

    def test_unique_workflow_create_remains_idempotent(self):
        payload = b'{"goal":"check required files","request_id":"req_g182123456"}'
        first_code, first = self.post_raw("/v1/workflows", payload)
        second_code, second = self.post_raw("/v1/workflows", payload)
        self.assertEqual((first_code, second_code), (200, 200))
        self.assertEqual(first["workflow_id"], second["workflow_id"])
        self.assertEqual(self.backend.list()["count"], 1)


if __name__ == "__main__":
    unittest.main()
