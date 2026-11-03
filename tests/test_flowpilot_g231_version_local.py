"""G231: real selected local version-candidate metadata with explicit consent."""
from __future__ import annotations
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_g165_local_metadata_api import MetadataGate, MetadataRefused
from flowpilot_local_backend import Backend, create_server
from flowpilot_g227_metadata_receipts import ACK

TOKEN = "v" * 48


class VersionCandidateLocalEndToEnd(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/"local-only-version-fixture"
        self.root.mkdir()
        (self.root/"spec.md").write_bytes(b"original local only")
        (self.root/"spec_v2.md").write_bytes(b"candidate metadata only")
        self.db=Path(tmp.name)/"db.sqlite"
        self.backend=Backend(self.db,create=True,metadata_root=self.root)
        self.wf=self.backend.create("check required files","req_"+"e"*12)["workflow_id"]

    def gate(self, required, versions):
        ticket=self.backend.metadata.begin("check required files", required, versions=versions)
        outcome=self.backend.metadata.approve(ticket["review_id"],ticket["scope_sha256"],
                                              "APPROVE_LOCAL_METADATA_READ_ONLY")
        return ticket,outcome

    def test_exact_and_candidate_are_review_not_ready(self):
        source=(self.root/"spec.md").read_bytes()
        ticket,result=self.gate(["spec.md"],{"spec.md":["spec_v2.md"]})
        self.assertEqual(ticket["version_candidate_count"],1)
        self.assertEqual(result["inspection_result"],[{"index":1,"state":"VERSION_REVIEW"}])
        self.assertEqual(result["status"],"LOCAL_METADATA_BLOCKED")
        self.assertNotIn("spec_v2.md",json.dumps(result))
        self.assertNotIn("spec.md",json.dumps(result))
        saved=self.backend.save_metadata_receipt(self.wf,ticket["review_id"],
                                                 ticket["scope_sha256"],ACK)
        self.assertEqual(saved["record"]["findings"][0]["state"],"VERSION_REVIEW")
        evaluation=self.backend.local_council(self.wf)
        self.assertEqual(evaluation["status"],"LOCAL_REVIEW_REQUIRED")
        self.assertEqual(evaluation["counts"]["VERSION_REVIEW"],1)
        self.assertEqual(evaluation["roles"][3]["status"],"REVIEW")
        self.assertEqual(self.backend.local_operator_report(self.wf)["release_gate"],"HOLD")
        self.assertEqual(source,(self.root/"spec.md").read_bytes())

    def test_no_candidate_keeps_exact_present(self):
        (self.root/"spec_v2.md").unlink()
        _,result=self.gate(["spec.md"],{"spec.md":["spec_v2.md"]})
        self.assertEqual(result["inspection_result"][0]["state"],"PRESENT")

    def test_candidate_only_blocks_latest_version_inference(self):
        (self.root/"spec.md").unlink()
        _,result=self.gate(["spec.md"],{"spec.md":["spec_v2.md"]})
        self.assertEqual(result["inspection_result"][0]["state"],"VERSION_REVIEW")

    def test_no_exact_and_no_candidate_is_missing(self):
        (self.root/"spec.md").unlink()
        (self.root/"spec_v2.md").unlink()
        _,result=self.gate(["spec.md"],{"spec.md":["spec_v2.md"]})
        self.assertEqual(result["inspection_result"][0]["state"],"MISSING")

    def test_preapproval_never_accesses_owner_filesystem(self):
        with patch.object(Path,"lstat",side_effect=AssertionError("early filesystem touch")),\
             patch.object(Path,"stat",side_effect=AssertionError("early filesystem touch")):
            proposed=self.backend.metadata.begin("check required files",
                                                  ["spec.md"],versions={"spec.md":["spec_v2.md"]})
            self.assertEqual(proposed["status"],"WAITING_APPROVAL")
        self.assertEqual(proposed["version_candidate_count"],1)

    def test_bad_versions_and_aliases_fail_closed(self):
        bad=[
            {"unknown.md":["spec_v2.md"]},
            {"spec.md":["spec.md"]},
            {"spec.md":["../private"]},
            {"spec.md":["NUL.txt"]},
            {"spec.md":["spec_v2.md","spec_v2.md"]},
            {"spec.md":"spec_v2.md"},
            {"spec.md":[]},
        ]
        for version in bad:
            with self.subTest(version=version):
                with self.assertRaises(MetadataRefused):
                    self.backend.metadata.begin("check required files",["spec.md"],versions=version)
        with self.assertRaises(MetadataRefused):
            self.backend.metadata.begin("check required files",["spec.md"],versions={"spec.md":[f"file_{i}.md" for i in range(21)]})

    def test_versions_are_part_of_scope_hash_and_cancel_revokes(self):
        plain=self.backend.metadata.begin("check required files",["spec.md"])
        version=self.backend.metadata.begin("check required files",["spec.md"],
                                            versions={"spec.md":["spec_v2.md"]})
        self.assertNotEqual(plain["scope_sha256"],version["scope_sha256"])
        with self.assertRaisesRegex(MetadataRefused,"EXACT_LOCAL_METADATA_APPROVAL_REQUIRED"):
            self.backend.metadata.approve(version["review_id"],plain["scope_sha256"],
                                          "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.backend.metadata.cancel(version["review_id"])
        with self.assertRaisesRegex(MetadataRefused,"REVIEW_ALREADY_CONSUMED"):
            self.backend.metadata.approve(version["review_id"],version["scope_sha256"],
                                          "APPROVE_LOCAL_METADATA_READ_ONLY")

    def test_version_candidate_symlink_is_not_checked(self):
        outside=self.root.parent/"outside.txt"
        outside.write_bytes(b"do not follow")
        (self.root/"spec_v2.md").unlink()
        try:
            (self.root/"spec_v2.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Local symlink unavailable")
        _,result=self.gate(["spec.md"],{"spec.md":["spec_v2.md"]})
        self.assertEqual(result["inspection_result"][0]["state"],"NOT_CHECKED")
        self.assertEqual(outside.read_bytes(),b"do not follow")

    def test_real_http_preview_approval_and_count_without_leaks(self):
        server=create_server(self.backend,TOKEN,port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        def call(path,data,authorized=True):
            conn=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=4)
            headers={"Host":f"127.0.0.1:{server.server_port}","Content-Type":"application/json"}
            if authorized:headers["Authorization"]="Bearer "+TOKEN
            try:
                conn.request("POST",path,body=json.dumps(data),headers=headers)
                response=conn.getresponse()
                return response.status,json.loads(response.read())
            finally:conn.close()
        request={"goal":"check required files","required":["spec.md"],
                 "versions":{"spec.md":["spec_v2.md"]}}
        self.assertEqual(call("/v1/local-metadata/preview",request,False)[0],403)
        self.assertEqual(call("/v1/local-metadata/preview",{**request,"root":"C:/private"})[0],400)
        code,pre=call("/v1/local-metadata/preview",request)
        self.assertEqual(code,200)
        self.assertEqual(pre["version_candidate_count"],1)
        self.assertNotIn("spec_v2.md",json.dumps(pre))
        approved={"review_id":pre["review_id"],"scope_sha256":pre["scope_sha256"],
                  "acknowledgement":"APPROVE_LOCAL_METADATA_READ_ONLY"}
        code,found=call("/v1/local-metadata/approve",approved)
        self.assertEqual(code,200)
        self.assertEqual(found["inspection_result"][0]["state"],"VERSION_REVIEW")
        self.assertEqual(call("/v1/local-metadata/approve",approved)[0],409)

if __name__=="__main__":
    unittest.main()
