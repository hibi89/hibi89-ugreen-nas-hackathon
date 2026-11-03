"""G230 real local filesystem → saved receipt → council/owner report via HTTP."""
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
from flowpilot_g230_local_council import (
    CouncilRefused, evaluate_local_receipt, owner_report,
)
from flowpilot_g227_metadata_receipts import ACK, _serialize, _sha
from flowpilot_local_backend import Backend, BackendRefused, create_server

TOKEN = "t" * 48


class LocalCouncilIntegrationTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "safe-owner-local"
        self.root.mkdir()
        (self.root / "expected.txt").write_bytes(b"private-test-bytes")
        self.db = Path(tmp.name) / "owner-new.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)
        self.wf = self.backend.create("check required files", "req_" + "c"*16)["workflow_id"]

    def save(self, required):
        planned = self.backend.metadata.begin("check required files", required)
        observed = self.backend.metadata.approve(
            planned["review_id"], planned["scope_sha256"],
            "APPROVE_LOCAL_METADATA_READ_ONLY")
        return self.backend.save_metadata_receipt(
            self.wf, observed["review_id"], observed["scope_sha256"], ACK)

    def test_present_real_local_files_four_roles_and_owner_report(self):
        before = (self.root / "expected.txt").read_bytes()
        saved = self.save(["expected.txt"])
        review = self.backend.local_council(self.wf)
        self.assertEqual(review["status"], "LOCAL_CHECKLIST_COMPLETE_NOT_NAS")
        self.assertEqual([r["role"] for r in review["roles"]],
                         ["Architect", "Security", "Builder", "QA"])
        self.assertTrue(all(r["status"] == "PASS_LOCAL" for r in review["roles"]))
        self.assertFalse(review["registered_expert_invoked"])
        self.assertFalse(review["independent_ai_council_invoked"])
        self.assertFalse(review["real_nas_verified"])
        self.assertEqual(review["proposed_correction"]["kind"], "NONE")
        self.assertEqual(review["local_receipt_sha256"], saved["record_sha256"])
        report = self.backend.local_operator_report(self.wf)
        self.assertEqual(report["status"], "OWNER_LOCAL_REPORT_READY_NOT_NAS")
        self.assertIn("RELEASE HOLD", report["report_markdown"])
        self.assertNotIn("expected.txt", json.dumps(report))
        self.assertNotIn("private-test-bytes", json.dumps(report))
        self.assertEqual(before, (self.root / "expected.txt").read_bytes())
        self.assertEqual(report, Backend(self.db, create=False).local_operator_report(self.wf))

    def test_missing_real_local_file_blocks_and_only_proposes_fix(self):
        self.save(["expected.txt", "not-present.pdf"])
        review = self.backend.local_council(self.wf)
        self.assertEqual(review["status"], "LOCAL_BLOCKED_MISSING_FILES")
        self.assertEqual(review["counts"]["MISSING"], 1)
        self.assertEqual(review["roles"][2]["status"], "BLOCKED")
        self.assertEqual(review["proposed_correction"]["item_indexes"], [2])
        self.assertEqual(review["proposed_correction"]["repair_count"], 0)
        self.assertFalse(review["proposed_correction"]["filesystem_modified"])
        self.assertFalse((self.root / "not-present.pdf").exists())
        self.assertIn("REVIEW_INDEXED_LOCAL_ITEMS",
                      self.backend.local_operator_report(self.wf)["owner_actions_required"])

    def test_no_saved_receipt_and_wrong_template_fail_closed(self):
        with self.assertRaisesRegex(Exception, "METADATA_EVIDENCE_NOT_FOUND"):
            self.backend.local_council(self.wf)
        csv = self.backend.create("고객별 매출 보고서 만들어줘",
                                  "req_" + "d"*16)["workflow_id"]
        with self.assertRaisesRegex(BackendRefused, "METADATA_TEMPLATE_REQUIRED"):
            self.backend.local_operator_report(csv)

    def test_no_extra_scan_or_mutation_during_report(self):
        self.save(["expected.txt"])
        initial = self.db.read_bytes()
        with patch.object(self.backend.metadata, "get",
                          side_effect=AssertionError("Unexpected read approval access")):
            self.assertEqual(self.backend.local_council(self.wf)["roles"][0]["role"],
                             "Architect")
            self.assertEqual(self.backend.local_operator_report(self.wf)["release_gate"],
                             "HOLD")
        self.assertEqual(initial, self.db.read_bytes())

    def test_tampered_hash_refuses_council_and_report(self):
        self.save(["expected.txt"])
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE fp_backend_local_metadata_evidence SET payload_sha=?",
                       ("0"*64,))
            db.commit()
        for action in (self.backend.local_council,
                       self.backend.local_operator_report):
            with self.assertRaisesRegex(Exception, "METADATA_EVIDENCE_HASH_MISMATCH"):
                action(self.wf)

    def test_uncertain_state_requires_review_not_all_present(self):
        saved = self.save(["expected.txt"])
        new = dict(saved["record"])
        new["findings"] = [{"index": 1, "state": "NOT_CHECKED"}]
        new["inspection_status"] = "LOCAL_METADATA_BLOCKED"
        with closing(sqlite3.connect(self.db)) as db:
            db.execute(
                "UPDATE fp_backend_local_metadata_evidence "
                "SET payload_json=?,payload_sha=? WHERE workflow_id=?",
                (_serialize(new), _sha(new), self.wf),
            )
            db.commit()
        council = self.backend.local_council(self.wf)
        self.assertEqual(council["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(council["roles"][3]["status"], "REVIEW")
        self.assertEqual(council["proposed_correction"]["kind"],
                         "OWNER_VERIFY_UNCERTAIN_ITEMS")

    def test_invalid_receipt_cannot_spoof_live_nas(self):
        self.save(["expected.txt"])
        record = self.backend.metadata_receipt(self.wf)
        bad = {**record, "verified_actual_nas": True}
        with self.assertRaises(CouncilRefused):
            evaluate_local_receipt(bad, workflow_id=self.wf,
                                   plan_sha256=self.backend.get(self.wf)["plan_sha256"])
        with self.assertRaises(CouncilRefused):
            owner_report({"schema": "flowpilot-local-council-g230-v1",
                          "status": "READY_FOR_NAS", "release_gate": "HOLD"})

    def test_actual_loopback_http_council_and_report_auth(self):
        self.save(["expected.txt", "not-present.pdf"])
        server = create_server(self.backend, TOKEN, port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        def get(route, *, valid=True):
            conn = http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=4)
            headers = {"Host": f"127.0.0.1:{server.server_port}"}
            if valid:
                headers["Authorization"] = "Bearer " + TOKEN
            try:
                conn.request("GET",route,headers=headers)
                res = conn.getresponse()
                return res.status, json.loads(res.read())
            finally:
                conn.close()
        before = self.db.read_bytes()
        for suffix in ("local-council", "local-report"):
            route = f"/v1/workflows/{self.wf}/{suffix}"
            self.assertEqual(get(route, valid=False)[0], 403)
            code, result = get(route)
            self.assertEqual(code, 200)
            self.assertEqual(result["release_gate"], "HOLD")
            self.assertFalse(result["real_nas_verified"])
            self.assertNotIn("expected.txt",json.dumps(result))
        self.assertEqual(before, self.db.read_bytes())

if __name__ == "__main__":
    unittest.main()
