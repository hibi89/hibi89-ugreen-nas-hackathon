"""G232: real bounded multi-stage text → one consent → SQLite → council/report.

All filesystem operations use disposable, owner-selected LOCAL test roots.
No NAS, Uliya Expert, customer files, LLMs or external network.
"""
from __future__ import annotations

from contextlib import closing
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
from flowpilot_g165_local_metadata_api import MetadataGate, MetadataRefused
from flowpilot_g227_metadata_receipts import (
    ACK, MetadataReceiptRefused, _serialize, _sha, from_completed_review,
)
from flowpilot_local_backend import Backend, create_server

TOKEN = "g232" * 12
INPUT = ("파일 확인: README.md; 버전 비교: final.pdf => final_v2.pdf;"
         " 납품 확인: handoff.md")


class TextPipelineTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "consented-disposable-local-folder"
        self.root.mkdir()
        (self.root / "README.md").write_bytes(b"raw-private-fixture")
        (self.root / "final_v2.pdf").write_bytes(b"v2-byte-content")
        (self.root / "handoff.md").write_bytes(b"handoff")
        self.db = Path(temp.name) / "test.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)
        self.workflow = self.backend.create("check required files",
                                             "req_" + "g"*12)["workflow_id"]
        self.other = self.backend.create("check required files",
                                          "req_" + "h"*12)["workflow_id"]

    def scoped(self, instructions=INPUT):
        return self.backend.begin_text_preview(self.workflow, instructions)

    def approved(self, instructions=INPUT):
        pre = self.scoped(instructions)
        result = self.backend.metadata.approve(
            pre["review_id"], pre["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY",
        )
        return pre, result

    def save(self, pre):
        return self.backend.save_metadata_receipt(
            self.workflow, pre["review_id"], pre["scope_sha256"], ACK
        )

    def test_three_stages_real_local_file_check_are_persisted_and_reported(self):
        pre, observed = self.approved()
        self.assertEqual(pre["parsed_actions_count"], 3)
        self.assertEqual(pre["bound_workflow_id"], self.workflow)
        self.assertEqual(pre["required_count"], 3)
        self.assertEqual(pre["version_candidate_count"], 1)
        self.assertEqual([row["state"] for row in observed["inspection_result"]],
                         ["PRESENT", "VERSION_REVIEW", "PRESENT"])
        self.assertNotIn("README.md", json.dumps(observed))
        self.assertNotIn("final_v2.pdf", json.dumps(observed))
        receipt = self.save(pre)
        self.assertEqual(len(receipt["record"]["stage_layout"]), 3)
        self.assertEqual(receipt["record"]["stage_layout"][1]["kind"], "REVIEW_VERSIONS")
        council = self.backend.local_council(self.workflow)
        self.assertEqual(council["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual([s["verdict"] for s in council["stage_reviews"]],
                         ["PASS_LOCAL", "REVIEW", "PASS_LOCAL"])
        report = self.backend.local_operator_report(self.workflow)
        self.assertIn("Stage 2 (REVIEW_VERSIONS): REVIEW", report["report_markdown"])
        self.assertIn("RELEASE HOLD", report["report_markdown"])
        for secret in ("README.md", "final_v2.pdf", "final.pdf",
                       "raw-private-fixture", str(self.root)):
            self.assertNotIn(secret, self.db.read_bytes().decode("utf-8", "ignore"))
            self.assertNotIn(secret, json.dumps(report))
        reopened = Backend(self.db, create=False)
        self.assertEqual(reopened.local_operator_report(self.workflow), report)
        self.assertFalse(report["real_nas_verified"])

    def test_one_consent_and_explicit_save_ack_required(self):
        pre = self.scoped()
        self.assertFalse(pre["approved_local_metadata_access"])
        self.assertIsNone(pre["inspection_result"])
        with self.assertRaises(MetadataReceiptRefused):
            self.save(pre)
        with self.assertRaisesRegex(MetadataRefused, "EXACT_LOCAL_METADATA_APPROVAL_REQUIRED"):
            self.backend.metadata.approve(
                pre["review_id"], "0"*64, "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.backend.metadata.approve(
            pre["review_id"], pre["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY")
        with self.assertRaisesRegex(Exception, "METADATA_SAVE_APPROVAL_REQUIRED"):
            self.backend.save_metadata_receipt(
                self.workflow, pre["review_id"], pre["scope_sha256"],
                "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertEqual(self.save(pre), self.save(pre))

    def test_cannot_cross_bind_approved_review_to_second_workflow(self):
        pre, _ = self.approved()
        with self.assertRaisesRegex(MetadataReceiptRefused, "TEXT_WORKFLOW_BINDING_MISMATCH"):
            self.backend.save_metadata_receipt(
                self.other, pre["review_id"], pre["scope_sha256"], ACK)
        self.save(pre)

    def test_scope_preview_does_not_touch_filesystem(self):
        gate = MetadataGate(self.root)
        with patch.object(Path, "lstat", side_effect=AssertionError("read before approval")), \
             patch.object(Path, "stat", side_effect=AssertionError("read before approval")):
            pre = gate.begin_text(self.workflow, INPUT)
        self.assertEqual(pre["status"], "WAITING_APPROVAL")
        self.assertEqual(pre["version_candidate_count"], 1)

    def test_bounded_grammar_and_unsafe_paths_refused(self):
        for instructions in (
            "please check files", "파일 삭제: README.md",
            "파일 확인: README.md; upload: final.pdf",
            "파일 확인: ../secret.txt",
            "파일 확인: NUL.txt",
            "파일 확인: README.md; 버전 비교: final.pdf => README.md",
            "파일 확인: README.md; 파일 확인: README.md",
            "버전 비교: final.pdf",
            "파일 확인: README.md;" * 9,
            "파일 확인: " + "x"*2000,
        ):
            with self.subTest(instructions=instructions[:30]), \
                 self.assertRaises(MetadataRefused):
                self.scoped(instructions)

    def test_legacy_single_scope_record_stays_valid(self):
        pre = self.backend.metadata.begin("check required files", ["README.md"])
        self.backend.metadata.approve(
            pre["review_id"], pre["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY")
        saved = self.save(pre)
        self.assertNotIn("stage_layout", saved["record"])
        council = self.backend.local_council(self.workflow)
        self.assertEqual(council["stage_reviews"], [])
        self.assertEqual(self.backend.local_operator_report(self.workflow)["release_gate"], "HOLD")

    def test_invalid_layout_fails_before_persistence(self):
        pre, observed = self.approved()
        for layout in (
            [{"stage_index":1, "kind":"REQUIRED_FILES","start_index":2,"item_count":3}],
            [{"stage_index":1, "kind":"RUN_SHELL","start_index":1,"item_count":3}],
            [{"stage_index":1, "kind":"REQUIRED_FILES","start_index":1,"item_count":1}],
        ):
            with self.subTest(layout=layout):
                mutated = dict(observed)
                mutated["stage_layout"] = layout
                with self.assertRaises(MetadataReceiptRefused):
                    from_completed_review(self.workflow, pre["scope_sha256"], mutated)

    def test_tampered_persisted_layout_is_not_trusted(self):
        pre, _ = self.approved()
        saved = self.save(pre)
        damaged = dict(saved["record"])
        damaged["stage_layout"] = [{
            "stage_index": 1, "kind": "WRITE_NAS",
            "start_index": 1, "item_count": damaged["item_count"],
        }]
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute(
                "UPDATE fp_backend_local_metadata_evidence "
                "SET payload_json=?,payload_sha=? WHERE workflow_id=?",
                (_serialize(damaged), _sha(damaged), self.workflow),
            )
            conn.commit()
        with self.assertRaises(MetadataReceiptRefused):
            self.backend.local_operator_report(self.workflow)

    def test_report_does_not_open_source_files_or_touch_database(self):
        pre, _ = self.approved()
        self.save(pre)
        before = self.db.read_bytes()
        with patch.object(self.backend.metadata, "get",
                          side_effect=AssertionError("no new metadata lookup")):
            report = self.backend.local_operator_report(self.workflow)
        self.assertEqual(report["status"], "OWNER_LOCAL_REPORT_READY_NOT_NAS")
        self.assertEqual(before, self.db.read_bytes())

    def test_http_preview_to_save_to_report_with_bearer_auth(self):
        server = create_server(self.backend, TOKEN, port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        def call(method, path, payload=None, *, authorized=True):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port,
                                              timeout=4)
            headers = {"Host":f"127.0.0.1:{server.server_port}"}
            if authorized:
                headers["Authorization"] = "Bearer " + TOKEN
            data = None if payload is None else json.dumps(payload).encode("utf-8")
            if data is not None:
                headers["Content-Type"] = "application/json"
            try:
                conn.request(method,path,body=data,headers=headers)
                response = conn.getresponse()
                return response.status, json.loads(response.read())
            finally:
                conn.close()
        path = "/v1/local-metadata/text-preview"
        data = {"workflow_id":self.workflow,"instructions":INPUT}
        self.assertEqual(call("POST",path,data,authorized=False)[0],403)
        self.assertEqual(call("POST",path,{**data,"customer_secret":"NO"})[0],400)
        code,pre = call("POST",path,data)
        self.assertEqual(code,200)
        self.assertEqual(pre["parsed_actions_count"],3)
        self.assertNotIn("final_v2.pdf",json.dumps(pre))
        _,approved = call("POST","/v1/local-metadata/approve",{
            "review_id":pre["review_id"],"scope_sha256":pre["scope_sha256"],
            "acknowledgement":"APPROVE_LOCAL_METADATA_READ_ONLY",
        })
        self.assertEqual(approved["inspection_result"][1]["state"],"VERSION_REVIEW")
        url="/v1/workflows/"+self.workflow+"/local-metadata"
        self.assertEqual(call("POST",url,{
            "review_id":pre["review_id"],"scope_sha256":pre["scope_sha256"],
            "acknowledgement":ACK,
        })[0],200)
        status,readback=call("GET","/v1/workflows/"+self.workflow+"/local-report")
        self.assertEqual(status,200)
        self.assertIn("Stage 2",readback["report_markdown"])
        self.assertNotIn("README.md",json.dumps(readback))

if __name__ == "__main__":
    unittest.main()
