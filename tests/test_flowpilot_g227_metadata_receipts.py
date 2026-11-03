"""G227 full local metadata -> owner approval -> SQLite -> HTTP readback E2E."""
from __future__ import annotations
import http.client
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_local_backend import Backend, BackendRefused, create_server
from flowpilot_g227_metadata_receipts import MetadataReceiptRefused, ACK

TOKEN = "x" * 48

class G227Tests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "consented-local-fixture"
        self.root.mkdir()
        (self.root / "README.md").write_bytes(b"private fixture, not NAS")
        self.db = Path(tmp.name) / "new.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)
        self.file_wf = self.backend.create("check required files", "req_" + "a"*12)["workflow_id"]
        self.csv_wf = self.backend.create("고객별 매출 보고서 만들어줘", "req_" + "b"*12)["workflow_id"]

    def approved(self, paths=None):
        paths = ["README.md", "missing.pdf"] if paths is None else paths
        r = self.backend.metadata.begin("check required files", paths)
        got = self.backend.metadata.approve(
            r["review_id"], r["scope_sha256"], "APPROVE_LOCAL_METADATA_READ_ONLY")
        return got

    def test_real_local_metadata_persists_redacted_after_restart(self):
        r = self.approved()
        self.assertEqual(r["status"], "LOCAL_METADATA_BLOCKED")
        stored = self.backend.save_metadata_receipt(
            self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        self.assertEqual([x["state"] for x in stored["record"]["findings"]], ["PRESENT", "MISSING"])
        self.assertFalse(stored["record"]["nas_verified"])
        self.assertNotIn("README.md", json.dumps(stored))
        self.assertNotIn(str(self.root), json.dumps(stored))
        self.assertNotIn("private fixture", self.db.read_bytes().decode("utf-8", "ignore"))
        reopened = Backend(self.db, create=False)
        self.assertEqual(reopened.metadata_receipt(self.file_wf), stored)
        self.assertEqual((self.root / "README.md").read_bytes(), b"private fixture, not NAS")

    def test_all_present_result_stored_but_not_nas(self):
        r = self.approved(["README.md"])
        receipt = self.backend.save_metadata_receipt(
            self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        self.assertEqual(receipt["record"]["inspection_status"], "LOCAL_METADATA_FINDINGS_READY")
        self.assertFalse(receipt["verified_actual_nas"])
        self.assertEqual(receipt["release_gate"], "HOLD")

    def test_denies_unapproved_and_unrelated_workflows(self):
        r = self.backend.metadata.begin("check required files", ["README.md"])
        with self.assertRaises(MetadataReceiptRefused):
            self.backend.save_metadata_receipt(self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        good = self.backend.metadata.approve(
            r["review_id"],r["scope_sha256"],"APPROVE_LOCAL_METADATA_READ_ONLY")
        with self.assertRaisesRegex(BackendRefused, "METADATA_TEMPLATE_REQUIRED"):
            self.backend.save_metadata_receipt(self.csv_wf, good["review_id"], good["scope_sha256"], ACK)
        with self.assertRaisesRegex(BackendRefused, "METADATA_SAVE_APPROVAL_REQUIRED"):
            self.backend.save_metadata_receipt(self.file_wf, good["review_id"], good["scope_sha256"], "APPROVE_LOCAL_METADATA_READ_ONLY")
        with self.assertRaises(MetadataReceiptRefused):
            self.backend.save_metadata_receipt(self.file_wf, good["review_id"], "0"*64, ACK)

    def test_idempotent_only_same_review_and_prevent_double_link(self):
        r = self.approved(["README.md"])
        a = self.backend.save_metadata_receipt(self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        b = self.backend.save_metadata_receipt(self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        self.assertEqual(a,b)
        newer = self.approved(["README.md", "missing.pdf"])
        with self.assertRaisesRegex(MetadataReceiptRefused, "METADATA_WORKFLOW_ALREADY_LINKED"):
            self.backend.save_metadata_receipt(self.file_wf, newer["review_id"], newer["scope_sha256"], ACK)

    def test_corruption_refused_on_readback(self):
        r = self.approved(["README.md"])
        self.backend.save_metadata_receipt(self.file_wf, r["review_id"], r["scope_sha256"], ACK)
        # sqlite3.Connection's context manager COMMITs, but does NOT CLOSE.
        # On Windows an unclosed handle prevents TemporaryDirectory cleanup.
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp_backend_local_metadata_evidence SET payload_sha=?", ("0"*64,))
            db.commit()
        with self.assertRaisesRegex(MetadataReceiptRefused, "METADATA_EVIDENCE_HASH_MISMATCH"):
            self.backend.metadata_receipt(self.file_wf)

    def test_actual_loopback_http_save_readback_auth_and_restart(self):
        server = create_server(self.backend, TOKEN, port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        def call(method, path, body=None, auth=True):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=4)
            headers = {"Host":f"127.0.0.1:{server.server_port}"}
            if auth: headers["Authorization"] = "Bearer " + TOKEN
            data = None if body is None else json.dumps(body).encode()
            if data is not None: headers["Content-Type"] = "application/json"
            try:
                conn.request(method, path, body=data, headers=headers)
                resp = conn.getresponse()
                return resp.status, json.loads(resp.read())
            finally:
                conn.close()
        r = self.approved(["README.md", "missing.pdf"])
        url = "/v1/workflows/" + self.file_wf + "/local-metadata"
        payload = {"review_id": r["review_id"], "scope_sha256": r["scope_sha256"],
                   "acknowledgement": ACK}
        self.assertEqual(call("GET",url,auth=False)[0],403)
        self.assertEqual(call("POST",url,payload,auth=False)[0],403)
        self.assertEqual(call("POST",url,{**payload,"acknowledgement":"READ_ONLY"})[0],403)
        status, saved = call("POST",url,payload)
        self.assertEqual(status,200)
        self.assertEqual(saved["status"], "REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS")
        self.assertEqual(call("GET",url), (200,saved))
        self.assertEqual(call("POST",url,payload)[0],200)
        self.assertEqual(call("POST",url,{**payload,"root":str(self.root)})[0],400)
        self.assertNotIn(str(self.root),json.dumps(saved))
        self.assertNotIn("README.md",json.dumps(saved))

if __name__=="__main__":
    unittest.main()
