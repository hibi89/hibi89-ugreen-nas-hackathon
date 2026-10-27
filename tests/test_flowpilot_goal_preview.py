"""G68: real local goal -> missing slots -> plan -> evidence, safe and bounded."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from flowpilot_goal_preview import parse_goal, process_goal, WorkflowRefused

class G68GoalPreviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/"README.md").write_bytes(b"disposable local")
        (self.root/"final.pdf").write_bytes(b"v1")
        (self.root/"final_v2.pdf").write_bytes(b"v2")
        self.goal = "인계 확인하고 파일 누락 확인하고 버전 비교해줘"

    def test_conversational_three_stage_plan_order(self):
        self.assertEqual(parse_goal(self.goal),
            ["check handoff deliverables", "check required files", "compare versions"])

    def test_asks_slots_without_root_access_even_with_consent(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT TOUCHED")):
            result = process_goal(self.goal, metadata_consent=True)
        self.assertEqual(result["status"], "WAITING_USER")
        self.assertEqual(result["missing_inputs"],
            ["local_root","required_relative_paths","version_candidate_mapping"])
        self.assertEqual(result["executed_steps"], 0)

    def test_second_stage_is_dynamic_from_goal(self):
        result = process_goal("필수 파일 확인하고 최종본 비교해주세요",
                              root=self.root, required=["README.md","final.pdf"],
                              candidates={"final.pdf":["final_v2.pdf"]})
        self.assertEqual(result["planned_steps"],2)
        self.assertEqual(result["status"],"WAITING_APPROVAL")
        self.assertEqual(result["executed_steps"],0)
        self.assertFalse(result["owner_folder_metadata_accessed"])

    def test_actual_local_metadata_multistep(self):
        result = process_goal(self.goal,root=self.root,
                              required=["README.md","final.pdf"],
                              candidates={"final.pdf":["final_v2.pdf"]},
                              metadata_consent=True)
        self.assertEqual(result["executed_steps"],3)
        self.assertEqual(result["status"],"NEEDS_REVIEW")
        self.assertTrue(result["owner_folder_metadata_accessed"])
        self.assertEqual(result["observed"][2]["items"][1]["state"],"VERSION_REVIEW")
        self.assertFalse(result["nas_verified"])

    def test_missing_required_stops_before_later_stage(self):
        result=process_goal("파일 누락 확인하고 버전 비교",
                             root=self.root,required=["missing.md"],
                             candidates={"missing.md":["final_v2.pdf"]},
                             metadata_consent=True)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["executed_steps"],1)

    def test_refuses_unrecognized_or_dangerous_sentence_without_partial_execution(self):
        for goal in ("파일 삭제해줘","인계 확인하고 파일 삭제해줘",
                     "파일 확인하고 외부 전송해줘","인계 확인 그리고 NAS 업로드",
                     "please delete files", "인계 확인하고 인계 확인", "버전 비교;"):
            with self.subTest(goal=goal), self.assertRaises(WorkflowRefused):
                parse_goal(goal)

    def test_preflight_all_steps_before_approved_root_inspection(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT TOUCHED")):
            with self.assertRaises(WorkflowRefused):
                process_goal(self.goal, root=self.root, required=["README.md"],
                             candidates={"README.md":["../secrets.env"]},
                             metadata_consent=True)

    def test_no_consent_never_touches_folder(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("ROOT TOUCHED")):
            result=process_goal(self.goal, root=self.root,
                                required=["README.md","final.pdf"],
                                candidates={"final.pdf":["final_v2.pdf"]})
        self.assertEqual(result["status"],"WAITING_APPROVAL")

    def test_no_private_paths_in_runtime_result(self):
        result=process_goal(self.goal,root=self.root,
                            required=["README.md","final.pdf"],
                            candidates={"final.pdf":["final_v2.pdf"]},
                            metadata_consent=True)
        raw=json.dumps(result,ensure_ascii=False)
        self.assertNotIn("README.md",raw)
        self.assertNotIn(str(self.root),raw)
        self.assertNotIn("final_v2.pdf",raw)

    def test_cli_end_to_end_and_rejected_goal(self):
        script=str(ROOT/"tools"/"flowpilot_goal_preview.py")
        cmd=[sys.executable,script,"--goal",self.goal,"--root",str(self.root),
             "--required","README.md","--required","final.pdf",
             "--candidate","final.pdf=final_v2.pdf","--approve-local-metadata"]
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["executed_steps"],3)
        self.assertNotIn(str(self.root),run.stdout)
        denied=subprocess.run([sys.executable,script,"--goal","삭제해줘",
                                "--approve-local-metadata"],capture_output=True,text=True,timeout=15)
        self.assertEqual(denied.returncode,2)
        self.assertEqual(json.loads(denied.stdout)["status"],"GOAL_REFUSED")

if __name__=="__main__":
    unittest.main()
