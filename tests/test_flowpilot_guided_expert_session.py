"""G121 Korean/English interactive NAS file plan and double permission gates."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"tests"))
from flowpilot_guided_expert_session import run_guided_expert,GuidedRefused,_load_pinned_kit
from test_sdk_parameter_matrix import fake
from flowpilot_multi_read_intake import SCHEMA as MULTI

GOAL="필수 파일 확인해줘"
ROOT_SECRET="/volume1/projects/SENSITIVE_CUSTOMER_FOLDER"
CHECK="README.md,release/SENSITIVE_CUSTOMER_DELIVERY.pdf"

def session(answers,*,goal=GOAL,kit=None,test_sha=None,receipts=None,fixture=False):
    it=iter(answers)
    output=[]
    prompts=[]
    loaded=[]
    def ask(q):
        prompts.append(q)
        return next(it)
    def loader():
        loaded.append(True)
        return kit
    result=run_guided_expert(
        goal,ask=ask,emit=output.append,kit_loader=loader if kit is not None else None,
        synthetic_only_test_sha=test_sha,normalized_receipts=receipts,
        run_local_fixture=fixture)
    body="\n".join(output)
    assert "SENSITIVE_CUSTOMER_FOLDER" not in body
    assert "SENSITIVE_CUSTOMER_DELIVERY.pdf" not in body
    return result,output,prompts,loaded

class G121GuidedExpertTests(unittest.TestCase):
    def setUp(self):
        self.kit,self.sha=fake()
        self.answers=[ROOT_SECRET,CHECK,"APPROVE_METADATA","ACK_UNKNOWN_PROCESSING"]
    def test_four_questions_two_separate_approvals_and_plan(self):
        row,output,prompts,loaded=session(self.answers,kit=self.kit,test_sha=self.sha)
        self.assertEqual(row["status"],"OFFLINE_GUIDED_REVIEW_READY_NOT_NAS")
        self.assertEqual(row["catalog_provenance"],"SYNTHETIC_CATALOG_TEST_ONLY")
        self.assertEqual(row["required_item_count"],2)
        self.assertEqual(len(prompts),4)
        self.assertEqual(len(loaded),1)
        self.assertTrue(output[0].startswith("FLOWPILOT_PREVIEW="))
        self.assertFalse(row["actual_uliya_expert_invoked"])
        self.assertFalse(row["actual_nas_verified"])
    def test_consent_refusal_never_reads_kit(self):
        for a,b in (("yes","ACK_UNKNOWN_PROCESSING"),
                    ("APPROVE_METADATA","yes"),
                    ("approve_metadata","ACK_UNKNOWN_PROCESSING"),
                    ("APPROVE_METADATA","DECLINE")):
            with self.subTest(a=a,b=b):
                row,_,prompts,loaded=session([ROOT_SECRET,CHECK,a,b],kit=self.kit,test_sha=self.sha)
                self.assertEqual(row["status"],"DECLINED_NO_ACTION")
                self.assertEqual(loaded,[])
                self.assertFalse(row["owner_folder_accessed"])
                if a!="APPROVE_METADATA":
                    self.assertEqual(len(prompts),3)
    def test_no_kit_redacted_useful_checklist(self):
        row,_,_,loaded=session(self.answers)
        self.assertEqual(row["status"],"AWAITING_PINNED_OFFICIAL_KIT")
        self.assertEqual(len(row["operator_runbook"]),8)
        self.assertEqual(loaded,[])
    def test_unsupported_intents_never_prompt(self):
        for goal,expected in (
            ("고객별 매출 보고서 만들어줘","LOCAL_TEMPLATE_ONLY_NATIVE_UNSUPPORTED"),
            ("NAS 전부 삭제해줘","BLOCKED_UNSUPPORTED_GOAL"),
            ("필수 파일 확인해줘 그리고 복사해줘","BLOCKED_UNSUPPORTED_GOAL"),
        ):
            row,_,prompts,loaded=session([],goal=goal,kit=self.kit)
            self.assertEqual(row["status"],expected)
            self.assertEqual(prompts,[])
            self.assertEqual(loaded,[])
    def test_bad_paths_fail_before_consent(self):
        for root,check in ((ROOT_SECRET,"../private.env"),
                           ("/volume1/../private",CHECK),
                           (ROOT_SECRET,"README.md,README.md"),
                           (ROOT_SECRET,".env"),("//NAS/project","README.md")):
            with self.subTest(check=check,root=root),self.assertRaises(GuidedRefused):
                session([root,check,"APPROVE_METADATA"],kit=self.kit)
    def test_unpinned_zip_fails_closed(self):
        row,_,_,loaded=session(self.answers,kit=self.kit)
        self.assertEqual(row["status"],"OFFICIAL_CATALOG_OR_RECEIPT_REFUSED")
        self.assertEqual(len(loaded),1)
    def test_synthetic_rehearsal_reuses_real_local_fixture(self):
        row,_,_,_=session(self.answers,kit=self.kit,test_sha=self.sha,fixture=True)
        self.assertEqual(row["local_synthetic_fixture_test"],"PASS_NOT_NAS")
        self.assertFalse(row["production_applied"])
    def test_receipt_claims_never_upgrade_nas(self):
        data=json.loads((ROOT/"docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json").read_text(encoding="utf-8"))
        data["authorized_root"]=ROOT_SECRET
        data["required_paths"]=["README.md","release/SENSITIVE_CUSTOMER_DELIVERY.pdf"]
        data["file_agent_report"]["authorized_root"]=ROOT_SECRET
        data["file_agent_report"]["observations"][1]["relative_path"]=data["required_paths"][1]
        row,output,_,_=session(self.answers,kit=self.kit,test_sha=self.sha,
                               receipts={"schema":MULTI,"receipts":[data]})
        self.assertEqual(row["status"],"OFFLINE_GUIDED_REVIEW_READY_NOT_NAS")
        self.assertEqual(row["provisional_consistency"],"CONSISTENT_CLAIM_ONLY")
        self.assertFalse(row["actual_nas_verified"])
        self.assertNotIn(ROOT_SECRET,"\n".join(output))
    def test_mismatched_receipt_scope_refused(self):
        data=json.loads((ROOT/"docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json").read_text(encoding="utf-8"))
        row,_,_,_=session(self.answers,kit=self.kit,test_sha=self.sha,
                          receipts={"schema":MULTI,"receipts":[data]})
        self.assertEqual(row["status"],"OFFICIAL_CATALOG_OR_RECEIPT_REFUSED")
    def test_incomplete_dialogue_never_grants_consent(self):
        with self.assertRaises(GuidedRefused):
            session([ROOT_SECRET,CHECK],kit=self.kit)
    def test_invalid_kit_local_bytes_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"kit.zip"
            path.write_bytes(self.kit)
            with self.assertRaises(GuidedRefused):
                _load_pinned_kit(path)
    def test_cli_no_kit_korean_input_windows_compatible(self):
        p=subprocess.run(
            [sys.executable,str(ROOT/"tools/flowpilot_guided_expert_session.py"),
             "--goal",GOAL],
            input="\n".join(self.answers)+"\n",text=True,
            capture_output=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("AWAITING_PINNED_OFFICIAL_KIT",p.stdout)
        self.assertNotIn("SENSITIVE_CUSTOMER_FOLDER",p.stdout)
        self.assertNotIn("SENSITIVE_CUSTOMER_DELIVERY",p.stdout)
    def test_strict_pinned_catalog_gate_is_not_registration(self):
        row,_,_,_=session(self.answers,kit=self.kit,test_sha=self.sha)
        self.assertEqual(row["next_action"],"VERIFY_LIVE_EXPERT_SIGNATURE_PERMISSIONS_AND_RESULT_SCHEMA")
        self.assertEqual(row["release_gate"],"HOLD")

if __name__=="__main__":
    unittest.main()
