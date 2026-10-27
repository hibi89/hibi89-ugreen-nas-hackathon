"""G69 guided CLI regression: consent, refusal and local metadata."""
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_goal_preview import run_guided_session, WorkflowRefused

class GuidedSessionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "README.md").write_bytes(b"temporary")

    def test_approved_local_metadata(self):
        output = []
        answers = iter([str(self.root), "README.md", "APPROVE"])
        result = run_guided_session("파일 확인",
            ask=lambda prompt: next(answers), emit=output.append)
        self.assertEqual(result["executed_steps"], 1)
        self.assertTrue(result["owner_folder_metadata_accessed"])
        self.assertEqual(result["next_action"], "REVIEW_LOCAL_FINDINGS")
        self.assertEqual(result["finding_counts"]["PRESENT"], 1)
        self.assertEqual(result["review_queue"], [])
        self.assertFalse(result["review_required"])
        self.assertEqual(result["review_item_count"], 0)
        self.assertNotIn(str(self.root), "\n".join(output))

    def test_missing_file_is_indexed_in_redacted_review_queue(self):
        output = []
        answers = iter([str(self.root), "missing.pdf", "APPROVE"])
        result = run_guided_session("파일 확인",
            ask=lambda prompt: next(answers), emit=output.append)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["next_action"], "RESOLVE_BLOCKED_CHECKS")
        self.assertEqual(result["finding_counts"]["MISSING"], 1)
        self.assertEqual(result["review_queue"], [
            {"step": 1, "item_index": 1, "state": "MISSING"}
        ])
        self.assertEqual(sum(result["finding_counts"].values()), 1)
        self.assertTrue(result["review_required"])
        self.assertEqual(result["review_item_count"], 1)
        self.assertNotIn("missing.pdf", "\\n".join(output))
        self.assertNotIn(str(self.root), "\\n".join(output))

    def test_version_review_queue_and_counts_agree(self):
        (self.root / "final.pdf").write_bytes(b"v1")
        (self.root / "final_v2.pdf").write_bytes(b"v2")
        output = []
        answers = iter([str(self.root), "final.pdf",
                        "final.pdf=final_v2.pdf", "APPROVE"])
        result = run_guided_session("버전 비교",
            ask=lambda prompt: next(answers), emit=output.append)
        self.assertEqual(result["finding_counts"]["VERSION_REVIEW"], 1)
        self.assertEqual(result["review_queue"], [
            {"step": 1, "item_index": 1, "state": "VERSION_REVIEW"}
        ])
        self.assertEqual(sum(result["finding_counts"].values()), 1)
        self.assertTrue(result["review_required"])
        self.assertEqual(result["review_item_count"], 1)
        self.assertNotIn("final.pdf", "\\n".join(output))
        self.assertNotIn(str(self.root), "\\n".join(output))

    def test_declined_without_root_access(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            answers = iter([str(self.root), "README.md", "NO"])
            result = run_guided_session("파일 확인",
                ask=lambda prompt: next(answers), emit=lambda message: None)
        self.assertEqual(result["status"], "DECLINED")
        self.assertEqual(result["next_action"], "NO_ACTION")
        self.assertEqual(sum(result["finding_counts"].values()), 0)
        self.assertEqual(result["review_queue"], [])
        self.assertEqual(result["executed_steps"], 0)

    def test_missing_inputs_provide_next_action_without_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            result = process_goal("파일 확인")
        self.assertEqual(result["status"], "WAITING_USER")
        self.assertEqual(result["next_action"], "PROVIDE_MISSING_INPUTS")
        self.assertEqual(result["executed_steps"], 0)

    def test_complete_unapproved_plan_requests_approval(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            result = process_goal("파일 확인", root=self.root,
                required=["README.md"], metadata_consent=False)
        self.assertEqual(result["status"], "WAITING_APPROVAL")
        self.assertEqual(result["next_action"], "APPROVE_LOCAL_METADATA_OR_DECLINE")
        self.assertFalse(result["owner_folder_metadata_accessed"])

    def test_unsafe_goal_refused_before_prompt(self):
        with self.assertRaises(WorkflowRefused):
            run_guided_session("파일 삭제해줘",
                ask=lambda prompt: self.fail("unexpected prompt"))


    def test_three_stage_version_review(self):
        (self.root / "final.pdf").write_bytes(b"v1")
        (self.root / "final_v2.pdf").write_bytes(b"v2")
        answers = iter([str(self.root), "README.md,final.pdf",
                        "final.pdf=final_v2.pdf", "APPROVE"])
        output = []
        result = run_guided_session("인계 확인하고 파일 누락 확인하고 버전 비교",
            ask=lambda prompt: next(answers), emit=output.append)
        self.assertEqual(result["executed_steps"], 3)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertNotIn("final_v2.pdf", "\n".join(output))

    def test_unsafe_relative_path_refused_before_access(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            answers = iter([str(self.root), "../secret.env"])
            with self.assertRaises(WorkflowRefused):
                run_guided_session("파일 확인",
                    ask=lambda prompt: next(answers), emit=lambda message: None)

    def test_case_sensitive_consent(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            answers = iter([str(self.root), "README.md", "approve"])
            result = run_guided_session("파일 확인",
                ask=lambda prompt: next(answers), emit=lambda message: None)
        self.assertEqual(result["status"], "DECLINED")


    def test_cli_subprocess_approved(self):
        script = str(ROOT / "tools" / "flowpilot_goal_preview.py")
        cmd = [sys.executable, script, "--goal", "파일 확인", "--interactive"]
        completed = subprocess.run(cmd,
            input=str(self.root) + "\nREADME.md\nAPPROVE\n",
            capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("FLOWPILOT_PREVIEW=", completed.stdout)
        self.assertIn("FLOWPILOT_RESULT=", completed.stdout)
        self.assertIn("NEEDS_REVIEW", completed.stdout)
        self.assertNotIn(str(self.root), completed.stdout)

    def test_cli_subprocess_declined(self):
        script = str(ROOT / "tools" / "flowpilot_goal_preview.py")
        completed = subprocess.run(
            [sys.executable, script, "--goal", "파일 확인", "--interactive"],
            input=str(self.root) + "\nREADME.md\nNO\n",
            capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"status": "DECLINED"', completed.stdout)
        self.assertNotIn(str(self.root), completed.stdout)

    def test_cli_subprocess_no_flag_bypass(self):
        script = str(ROOT / "tools" / "flowpilot_goal_preview.py")
        completed = subprocess.run(
            [sys.executable, script, "--goal", "파일 확인", "--interactive",
             "--approve-local-metadata"],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("GOAL_REFUSED", completed.stdout)

    def test_explicit_empty_version_mapping_without_version_goal_refused(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("파일 확인", root=self.root,
                    required=["README.md"], candidates={},
                    metadata_consent=True)

    def test_version_candidates_without_version_goal_refused_before_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("파일 확인", root=self.root,
                    required=["README.md"],
                    candidates={"README.md": ["README_v2.md"]},
                    metadata_consent=True)

    def test_duplicate_version_candidates_refused_before_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("버전 비교", root=self.root,
                    required=["README.md"],
                    candidates={"README.md": ["README.md", "README.md"]},
                    metadata_consent=True)

    def test_self_referential_candidate_refused_before_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("버전 비교", root=self.root,
                    required=["README.md"],
                    candidates={"README.md": ["README.md"]},
                    metadata_consent=True)

    def test_more_than_twenty_candidates_refused_before_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("버전 비교", root=self.root,
                    required=["README.md"],
                    candidates={"README.md": [f"candidate_{i}.txt" for i in range(21)]},
                    metadata_consent=True)

    def test_excessive_version_candidates_refused_before_access(self):
        from flowpilot_goal_preview import process_goal
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            with self.assertRaises(WorkflowRefused):
                process_goal("버전 비교", root=self.root,
                    required=["README.md"],
                    candidates={"README.md": [f"candidate_{i}.txt" for i in range(101)]},
                    metadata_consent=True)

if __name__ == "__main__":
    unittest.main()
