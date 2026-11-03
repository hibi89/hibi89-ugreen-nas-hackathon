"""G236: real local SQLite -> review -> redacted Expert handoff HTTP.

Uses disposable folder only; never calls a vendor, NAS, or network service.
"""
from __future__ import annotations

from contextlib import closing
import copy
import http.client
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_local_backend import Backend, create_server
from flowpilot_g227_metadata_receipts import ACK
from flowpilot_g236_native_handoff import NativeHandoffRefused, build_native_handoff

TOKEN = "g236" * 12
PRIVATE = "private-nas-metadata-README.md"


class NativeHandoffTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "local-consented-root"
        self.root.mkdir()
        (self.root / PRIVATE).write_bytes(b"never-read-file-body")
        self.db = Path(temp.name) / "evidence.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)
        self.workflow = self.backend.create("check required files",
            "req_" + "g" * 12)["workflow_id"]
        self.path = f"/v1/workflows/{self.workflow}/native-handoff"

    def store(self, text=None):
        if text is None:
            text = f"파일 확인: {PRIVATE}; 납품 확인: missing.pdf"
        preview = self.backend.begin_text_preview(self.workflow, text)
        self.backend.metadata.approve(
            preview["review_id"], preview["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.backend.save_metadata_receipt(
            self.workflow, preview["review_id"], preview["scope_sha256"], ACK)
        return preview

    def test_stage_handoff_is_redacted_and_never_approves_native_execution(self):
        self.store()
        result = self.backend.native_handoff(self.workflow)
        self.assertEqual(result["status"],
                         "NATIVE_EXECUTION_BLOCKED_PENDING_RUNTIME_EVIDENCE")
        self.assertEqual([x["local_verdict"] for x in result["stages"]],
                         ["PASS_LOCAL", "BLOCKED"])
        self.assertEqual([x["catalog_label_not_executable"] for x in result["stages"]],
                         ["ug-filesystem find", "ug-filesystem find"])
        for value in (PRIVATE, "missing.pdf", str(self.root), "never-read-file-body"):
            self.assertNotIn(value, json.dumps(result))
            self.assertNotIn(value, self.db.read_bytes().decode("utf-8", "ignore"))
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["effective_nas_rights_verified"])
        self.assertFalse(result["actual_registered_expert_invoked"])
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertEqual(len(result["handoff_sha256"]), 64)
        self.assertEqual(result, self.backend.native_handoff(self.workflow))

    def test_version_candidate_stage_is_label_not_live_command(self):
        self.store(f"파일 확인: {PRIVATE}; 버전 비교: final.pdf => final_v2.pdf")
        handoff = self.backend.native_handoff(self.workflow)
        self.assertEqual(handoff["stages"][1]["catalog_label_not_executable"],
                         "ug-filesystem stat")
        self.assertFalse(handoff["stages"][1]["live_action_allowed"])

    def test_no_saved_receipt_denied(self):
        with self.assertRaises(Exception):
            self.backend.native_handoff(self.workflow)

    def test_legacy_receipt_has_single_fallback_stage(self):
        preview = self.backend.metadata.begin("check required files", [PRIVATE])
        self.backend.metadata.approve(preview["review_id"],preview["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.backend.save_metadata_receipt(self.workflow,
            preview["review_id"],preview["scope_sha256"],ACK)
        result = self.backend.native_handoff(self.workflow)
        self.assertEqual(len(result["stages"]), 1)
        self.assertEqual(result["stages"][0]["kind"], "REQUIRED_FILES")

    def test_tampered_stored_receipt_is_rejected(self):
        self.store()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp_backend_local_metadata_evidence "
                       "SET payload_sha=? WHERE workflow_id=?",
                       ("0" * 64, self.workflow))
            db.commit()
        with self.assertRaises(Exception):
            self.backend.native_handoff(self.workflow)

    def test_forged_council_fields_and_fake_nas_readback_denied(self):
        self.store()
        council = self.backend.local_council(self.workflow)
        changes = (
            ("real_nas_verified", True), ("registered_expert_invoked", True),
            ("local_receipt_sha256", "not-a-digest"),
            ("item_count", 999), ("status", "NAS_READY"),
            ("release_gate", "READY"),
        )
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(NativeHandoffRefused):
                item = copy.deepcopy(council)
                item[key] = value
                build_native_handoff(item)

    def test_stage_verdict_and_count_mismatch_denied(self):
        self.store()
        item = self.backend.local_council(self.workflow)
        item["stage_reviews"][0]["verdict"] = "PASS_NAS"
        with self.assertRaises(NativeHandoffRefused):
            build_native_handoff(item)
        item = self.backend.local_council(self.workflow)
        item["counts"]["PRESENT"] = 2
        with self.assertRaises(NativeHandoffRefused):
            build_native_handoff(item)

    def test_http_auth_no_query_and_readback_after_restart(self):
        self.store()
        self.server = create_server(self.backend, TOKEN)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)
        def call(path, method="GET", authorized=True):
            conn = http.client.HTTPConnection("127.0.0.1",self.server.server_port,
                                               timeout=5)
            try:
                headers = {"Host": f"127.0.0.1:{self.server.server_port}"}
                if authorized: headers["Authorization"] = "Bearer " + TOKEN
                if method == "POST":
                    headers["Content-Type"] = "application/json"
                conn.request(method, path, body="{}" if method == "POST" else None,
                             headers=headers)
                res = conn.getresponse()
                return res.status, json.loads(res.read())
            finally:
                conn.close()
        self.assertEqual(call(self.path, authorized=False)[0], 403)
        self.assertEqual(call(self.path + "?run=true")[0], 404)
        code, payload = call(self.path)
        self.assertEqual(code,200)
        self.assertFalse(payload["nas_verified"])
        self.assertEqual(call(self.path, method="POST")[0], 404)
        reopened = Backend(self.db, create=False)
        self.assertEqual(payload, reopened.native_handoff(self.workflow))
        self.assertNotIn(PRIVATE,json.dumps(payload))

    def test_council_get_does_not_read_owner_folder_again(self):
        self.store()
        original_lstat = Path.lstat
        def guard(path, *args, **kwargs):
            # Protect ONLY the owner-selected input root, never normal SQLite
            # path/symlink integrity checks performed by Backend._path_gate.
            current = Path(path)
            if current == self.root or self.root in current.parents:
                raise AssertionError("owner scan repeated")
            return original_lstat(path, *args, **kwargs)
        with patch.object(Path, "lstat", autospec=True, side_effect=guard):
            handoff = self.backend.native_handoff(self.workflow)
        self.assertFalse(handoff["owner_folder_rechecked"])


if __name__ == "__main__":
    unittest.main()
