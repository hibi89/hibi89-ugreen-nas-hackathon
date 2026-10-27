"""G69 guided CLI regression: consent, refusal and local metadata."""
import sys
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
        self.assertNotIn(str(self.root), "\n".join(output))

    def test_declined_without_root_access(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("unexpected access")):
            answers = iter([str(self.root), "README.md", "NO"])
            result = run_guided_session("파일 확인",
                ask=lambda prompt: next(answers), emit=lambda message: None)
        self.assertEqual(result["status"], "DECLINED")
        self.assertEqual(result["executed_steps"], 0)

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

if __name__ == "__main__":
    unittest.main()
