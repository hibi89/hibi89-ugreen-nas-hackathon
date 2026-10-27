"""G69 guided CLI: actual local, explicit consent and bounded missing-slot prompts.

No NAS, Uliya, real user data, or customer path access in test execution.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_goal_preview import run_guided_session, WorkflowRefused


class G69GuidedLocalCLI(unittest.TestCase):
    def setUp(self):
        box = tempfile.TemporaryDirectory()
        self.addCleanup(box.cleanup)
        self.root = Path(box.name)
        (self.root/"README.md").write_bytes(b"synthetic readme")
        (self.root/"final.pdf").write_bytes(b"synthetic final")
        (self.root/"final_v2.pdf").write_bytes(b"synthetic next")
        self.goal = "인계 확인하고 파일 누락 확인하고 버전 비교해줘"
        self.script = str(ROOT/"tools"/"flowpilot_goal_preview.py")

    def test_guided_new_session_collects_three_slots_and_runs_three_steps(self):
        asked, emitted = [], []
        values = iter([str(self.root), "README.md, final.pdf",
                       "final.pdf=final_v2.pdf", "APPROVE"])
        def ask(prompt):
            asked.append(prompt)
            return next(values)
        row = run_guided_session(self.goal, ask=ask, emit=emitted.append)
        self.assertEqual(len(asked), 4)
        self.assertEqual(row["executed_steps"], 3)
        self.assertTrue(row["owner_folder_metadata_accessed"])
        self.assertEqual(row["observed"][2]["items"][1]["state"],"VERSION_REVIEW")
        self.assertFalse(row["nas_verified"])
        self.assertTrue(emitted[0].startswith("FLOWPILOT_PREVIEW="))
        self.assertTrue(emitted[1].startswith("FLOWPILOT_RESULT="))

    def test_decline_never_accesses_owner_folder(self):
        emitted=[]
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("OWNER FOLDER ACCESSED")):
            row=run_guided_session("파일 확인",root=self.root,
                required=["README.md"],ask=lambda prompt:"NO",emit=emitted.append)
        self.assertEqual(row["status"],"DECLINED")
        self.assertEqual(row["executed_steps"],0)
        self.assertFalse(row["owner_folder_metadata_accessed"])
        self.assertFalse(row["file_contents_opened"])

    def test_consent_requires_exact_uppercase_keyword(self):
        for response in ("approve"," APPROVE","APPROVE ","yes",""):
            with self.subTest(response=response),patch(
                    "flowpilot_owner_local_audit._valid_root",
                    side_effect=AssertionError("ROOT TOUCHED")):
                row=run_guided_session("파일 확인",root=self.root,
                    required=["README.md"],ask=lambda prompt:response,
                    emit=lambda message:None)
                self.assertEqual(row["status"],"DECLINED")

    def test_prepopulated_fields_still_require_interactive_approval(self):
        questions=[]
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("ROOT TOUCHED")):
            row=run_guided_session("파일 확인",root=self.root,
                required=["README.md"],
                ask=lambda prompt:(questions.append(prompt) or "NO"),
                emit=lambda message:None)
        self.assertEqual(len(questions),1)
        self.assertIn("APPROVE",questions[0])
        self.assertEqual(row["status"],"DECLINED")

    def test_unsafe_goal_rejected_before_first_question(self):
        def forbidden(prompt):
            raise AssertionError("should not solicit consent to delete")
        with self.assertRaises(WorkflowRefused):
            run_guided_session("인계 확인하고 파일 삭제해줘",
                               ask=forbidden,emit=lambda line:None)

    def test_traversal_candidate_rejected_before_metadata_access(self):
        prompts=iter(["README.md=../credentials.env","APPROVE"])
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("ROOT TOUCHED")), self.assertRaises(WorkflowRefused):
            run_guided_session("파일 확인하고 버전 비교",root=self.root,
                required=["README.md"],ask=lambda prompt:next(prompts),
                emit=lambda line:None)

    def test_cli_e2e_stdout_has_only_redacted_result(self):
        data=f"{self.root}\nREADME.md, final.pdf\nfinal.pdf=final_v2.pdf\nAPPROVE\n"
        task=subprocess.run([sys.executable,self.script,"--goal",self.goal,
            "--interactive"],input=data,capture_output=True,text=True,timeout=15)
        self.assertEqual(task.returncode,0,task.stderr)
        values=[line.split("FLOWPILOT_RESULT=",1)[1] for line in task.stdout.splitlines()
                if "FLOWPILOT_RESULT=" in line]
        self.assertEqual(len(values),1)
        self.assertEqual(json.loads(values[0])["executed_steps"],3)
        self.assertNotIn(str(self.root),task.stdout)
        self.assertNotIn("final_v2.pdf",task.stdout)

    def test_cli_combined_interactive_and_preapproval_refused(self):
        task=subprocess.run([sys.executable,self.script,"--goal","파일 확인",
            "--interactive","--approve-local-metadata"],
            input="",capture_output=True,text=True,timeout=15)
        self.assertEqual(task.returncode,2)
        self.assertEqual(json.loads(task.stdout)["status"],"GOAL_REFUSED")

    def test_cli_missing_stdin_refuses_without_reading_any_files(self):
        task=subprocess.run([sys.executable,self.script,"--goal","파일 확인",
            "--interactive"],input="",capture_output=True,text=True,timeout=15)
        self.assertNotEqual(task.returncode,0)
        self.assertNotIn("PRESENT",task.stdout)
        self.assertNotIn(str(self.root),task.stdout)


if __name__=="__main__":
    unittest.main()
