"""G165 true local filesystem metadata and real HTTP approval boundary."""
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

TOKEN = "k" * 48


class G165Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "owner-selected-synthetic-root"
        self.root.mkdir()
        (self.root / "README.md").write_bytes(b"owner-side synthetic fixture")
        self.db = Path(self.tmp.name) / "new-backend.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)

    def test_g248_readonly_version_goal_preview_has_typed_plan_no_access(self):
        (self.root/"final.pdf").write_bytes(b"synthetic v1")
        (self.root/"final_v2.pdf").write_bytes(b"synthetic v2")
        gate=MetadataGate(self.root)
        from flowpilot_task_compiler import compile_goal
        for request in ("review versions","버전 비교해줘"):
            with self.subTest(request=request):
                with patch("flowpilot_g165_local_metadata_api.inspect_owner_folder",
                           wraps=__import__("flowpilot_g165_local_metadata_api").inspect_owner_folder) as inspector:
                    pre=gate.begin(request,["final.pdf"],
                                   versions={"final.pdf":["final_v2.pdf"]})
                self.assertEqual(inspector.call_count,1)
                self.assertEqual(inspector.call_args.kwargs["metadata_consent"],False)
                self.assertEqual(pre["selected_intent"],"REVIEW_VERSIONS")
                self.assertEqual(pre["status"],"WAITING_APPROVAL")
                self.assertEqual(pre["typed_review_plan"],
                                 compile_goal(request)["steps"])
                self.assertEqual(len(pre["typed_review_plan"]),4)
                self.assertFalse(pre["approved_local_metadata_access"])
                self.assertIsNone(pre["inspection_result"])
                self.assertNotIn(str(self.root),json.dumps(pre))
                self.assertNotIn("final.pdf",json.dumps(pre))
                out=gate.approve(pre["review_id"],pre["scope_sha256"],
                                 "APPROVE_LOCAL_METADATA_READ_ONLY")
                self.assertEqual(out["status"],"LOCAL_METADATA_BLOCKED")
                self.assertEqual(out["selected_intent"],"REVIEW_VERSIONS")
                self.assertEqual(out["inspection_result"],
                                 [{"index":1,"state":"VERSION_REVIEW"}])
                self.assertFalse(out["nas_verified"])
                self.assertFalse(out["file_contents_opened"])
                self.assertEqual(gate.get(pre["review_id"]),out)
                with self.assertRaisesRegex(MetadataRefused,"CONSUMED"):
                    gate.approve(pre["review_id"],pre["scope_sha256"],
                                 "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertEqual((self.root/"final.pdf").read_bytes(),b"synthetic v1")
        self.assertEqual((self.root/"final_v2.pdf").read_bytes(),b"synthetic v2")

    def test_g248_unknown_goal_and_missing_candidate_fail_before_local_access(self):
        gate=MetadataGate(self.root)
        with patch("flowpilot_g165_local_metadata_api.inspect_owner_folder",
                   side_effect=AssertionError("NO_METADATA_ALLOWED")):
            for bad in ("review versions and delete all","review versions; upload",
                        "compare versions and move files"):
                with self.assertRaises(MetadataRefused):
                    gate.begin(bad,["README.md"],versions={"README.md":["other.md"]})
            with self.assertRaisesRegex(MetadataRefused,"G248_EXACT_VERSION_CANDIDATES_REQUIRED"):
                gate.begin("review versions",["README.md"])
        self.assertEqual(len(gate._reviews),0)

    def test_preview_no_fs_metadata_even_when_root_not_present(self):
        unknown = self.root / "not-created"
        gate = MetadataGate(unknown)
        with patch.object(Path, "lstat", side_effect=AssertionError("access before approval")), \
             patch.object(Path, "stat", side_effect=AssertionError("access before approval")):
            plan = gate.begin("check required files", ["README.md", "missing.pdf"])
        self.assertEqual(plan["status"], "WAITING_APPROVAL")
        self.assertIsNone(plan["inspection_result"])
        self.assertFalse(plan["approved_local_metadata_access"])

    def test_true_readonly_lstat_and_redacted_results(self):
        gate = MetadataGate(self.root)
        plan = gate.begin("check required files", ["README.md", "missing.pdf"])
        before = (self.root / "README.md").read_bytes()
        found = gate.approve(plan["review_id"], plan["scope_sha256"],
                             "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertEqual(found["status"], "LOCAL_METADATA_BLOCKED")
        self.assertEqual(found["required_count"], 2)
        self.assertEqual(found["inspection_result"],
                         [{"index": 1, "state": "PRESENT"}, {"index": 2, "state": "MISSING"}])
        self.assertEqual(before, (self.root / "README.md").read_bytes())
        self.assertNotIn("README.md", json.dumps(found))
        self.assertNotIn(str(self.root), json.dumps(found))
        self.assertEqual(gate.get(plan["review_id"]), found)
        with self.assertRaisesRegex(MetadataRefused, "CONSUMED"):
            gate.approve(plan["review_id"], plan["scope_sha256"],
                         "APPROVE_LOCAL_METADATA_READ_ONLY")

    def test_exact_sha_and_explicit_string_required(self):
        gate = MetadataGate(self.root)
        plan = gate.begin("check required files", ["README.md"])
        for sha,ack in [(plan["scope_sha256"], "APPROVE_SYNTHETIC_ONLY"),
                        ("0"*64, "APPROVE_LOCAL_METADATA_READ_ONLY")]:
            with self.assertRaisesRegex(MetadataRefused, "EXACT_LOCAL_METADATA_APPROVAL"):
                gate.approve(plan["review_id"], sha, ack)
        ok = gate.approve(plan["review_id"],plan["scope_sha256"],
                          "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertEqual(ok["status"], "LOCAL_METADATA_FINDINGS_READY")

    def test_cancel_before_access_and_replay_denied(self):
        gate = MetadataGate(self.root)
        plan = gate.begin("check required files", ["README.md"])
        canceled=gate.cancel(plan["review_id"])
        self.assertEqual(canceled["status"],"CANCELED")
        self.assertEqual(canceled["required_count"],1)
        with self.assertRaisesRegex(MetadataRefused,"CONSUMED"):
            gate.approve(plan["review_id"],plan["scope_sha256"],
                         "APPROVE_LOCAL_METADATA_READ_ONLY")

    def test_reject_dangerous_scope_no_access(self):
        gate = MetadataGate(self.root)
        for names in (["../sensitive"], ["/etc/passwd"], ["README.md","README.md"],
                      [], ["README.md","x\\x00.txt"]):
            with self.assertRaises(MetadataRefused):
                gate.begin("check required files",names)
        with self.assertRaisesRegex(MetadataRefused,"UNSUPPORTED"):
            gate.begin("delete everything",["README.md"])

    def test_no_metadata_root_configured(self):
        gate = MetadataGate(None)
        with self.assertRaisesRegex(MetadataRefused, "LOCAL_ROOT_NOT_CONFIGURED"):
            gate.begin("check required files", ["README.md"])

    def test_symlink_root_refused_on_approval(self):
        link = Path(self.tmp.name) / "symlink-root"
        try: link.symlink_to(self.root, target_is_directory=True)
        except (NotImplementedError,OSError): self.skipTest("symlink unavailable")
        gate = MetadataGate(link)
        plan = gate.begin("check required files", ["README.md"])
        result = gate.approve(plan["review_id"],plan["scope_sha256"],
                              "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertEqual(result["status"], "INSPECTION_REFUSED")

    def test_symlink_child_is_not_reported_present(self):
        secret = Path(self.tmp.name) / "out-of-scope.txt"
        secret.write_bytes(b"secret no reads allowed")
        link=self.root / "shortcut.txt"
        try: link.symlink_to(secret)
        except (NotImplementedError,OSError): self.skipTest("symlink unavailable")
        gate=MetadataGate(self.root)
        plan=gate.begin("check required files", ["shortcut.txt"])
        result=gate.approve(plan["review_id"],plan["scope_sha256"],
                            "APPROVE_LOCAL_METADATA_READ_ONLY")
        self.assertNotEqual(result["status"],"LOCAL_METADATA_FINDINGS_READY")
        self.assertEqual(secret.read_bytes(),b"secret no reads allowed")

    def test_real_http_preview_approve_retrieve_and_reject(self):
        server=create_server(self.backend,TOKEN,port=0)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def request(method,path,body=None,auth=True,origin=None):
            conn=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
            headers={"Host":f"127.0.0.1:{server.server_port}"}
            if auth: headers["Authorization"]="Bearer "+TOKEN
            if origin:headers["Origin"]=origin
            data=json.dumps(body).encode() if body is not None else None
            if data is not None:headers["Content-Type"]="application/json"
            try:
                conn.request(method,path,body=data,headers=headers)
                resp=conn.getresponse()
                return resp.status,json.loads(resp.read())
            finally:conn.close()
        args={"goal":"check required files","required":["README.md","absent.pdf"]}
        self.assertEqual(request("POST","/v1/local-metadata/preview",args,auth=False)[0],403)
        self.assertEqual(request("POST","/v1/local-metadata/preview",args,
                                 origin="https://evil.example")[0],403)
        code,pre=request("POST","/v1/local-metadata/preview",args)
        self.assertEqual(code,200)
        self.assertEqual(pre["status"],"WAITING_APPROVAL")
        rid=pre["review_id"]
        self.assertEqual(request("GET",f"/v1/local-metadata/reviews/{rid}")[1]["status"],
                         "WAITING_APPROVAL")
        bad={"review_id":rid,"scope_sha256":pre["scope_sha256"],
             "acknowledgement":"APPROVE_EXECUTION"}
        self.assertEqual(request("POST","/v1/local-metadata/approve",bad)[0],403)
        bad["acknowledgement"]="APPROVE_LOCAL_METADATA_READ_ONLY"
        code,out=request("POST","/v1/local-metadata/approve",bad)
        self.assertEqual(code,200)
        self.assertEqual(out["status"],"LOCAL_METADATA_BLOCKED")
        self.assertFalse(out["file_contents_opened"])
        self.assertEqual(request("GET",f"/v1/local-metadata/reviews/{rid}")[1]["status"],
                         "LOCAL_METADATA_BLOCKED")
        self.assertEqual(request("POST","/v1/local-metadata/approve",bad)[0],409)
        self.assertEqual(request("POST","/v1/local-metadata/approve",
                                 {**bad,"root":"C:/private"})[0],400)


if __name__=="__main__":
    unittest.main()
