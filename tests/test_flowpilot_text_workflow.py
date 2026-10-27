"""G64: executable bounded text instructions, never live UGREEN NAS."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_text_workflow import parse_instructions, run_text_workflow, WorkflowRefused

class G64TextWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_bytes(b"local fixture")
        (self.root / "final.pdf").write_bytes(b"v1")
        (self.root / "final_v2.pdf").write_bytes(b"v2")

    def test_english_two_step_real_local_io(self):
        row = run_text_workflow(self.root,
            "check files: README.md; compare versions: final.pdf => final_v2.pdf",
            metadata_consent=True)
        self.assertEqual(row["executed_steps"], 2)
        self.assertEqual([s["items"][0]["state"] for s in row["steps"]],
                         ["PRESENT", "VERSION_REVIEW"])
        self.assertEqual(row["status"], "NEEDS_REVIEW")
        self.assertFalse(row["nas_verified"])
        self.assertFalse(row["freeform_ai_interpretation_used"])

    def test_korean_two_step_real_local_io(self):
        row = run_text_workflow(self.root,
            "파일 확인: README.md; 버전 비교: final.pdf => final_v2.pdf",
            metadata_consent=True)
        self.assertEqual(row["executed_steps"], 2)
        self.assertEqual(row["steps"][1]["items"][0]["state"], "VERSION_REVIEW")

    def test_checklist_multiple_file_names(self):
        row = run_text_workflow(self.root, "필수 파일 확인: README.md, final.pdf",
                                metadata_consent=True)
        self.assertEqual([i["state"] for i in row["steps"][0]["items"]],
                         ["PRESENT", "PRESENT"])

    def test_handoff_label(self):
        row = run_text_workflow(self.root, "납품 확인: README.md",
                                metadata_consent=True)
        self.assertEqual(row["executed_steps"], 1)

    def test_no_consent_never_touches_owner_folder(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("TOUCHED")):
            row = run_text_workflow(self.root, "파일 확인: README.md")
        self.assertEqual(row["status"], "WAITING_APPROVAL")
        self.assertEqual(row["executed_steps"], 0)

    def test_unknown_second_stage_refused_before_read(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("TOUCHED")):
            with self.assertRaises(WorkflowRefused):
                run_text_workflow(self.root, "파일 확인: README.md; delete: final.pdf",
                                  metadata_consent=True)

    def test_unsafe_second_path_refused_before_read(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("TOUCHED")):
            with self.assertRaises(WorkflowRefused):
                run_text_workflow(self.root, "파일 확인: README.md; 파일 확인: ../secret.key",
                                  metadata_consent=True)

    def test_incomplete_comparison_refused(self):
        for command in ("compare versions: final.pdf",
                        "버전 비교: final.pdf => ",
                        "버전 비교: final.pdf, README.md => final_v2.pdf",
                        "check files: README.md => final_v2.pdf"):
            with self.subTest(command=command), self.assertRaises(WorkflowRefused):
                parse_instructions(command)

    def test_no_partial_parsing_of_unknown_words(self):
        for command in ("please delete README.md", "check files README.md",
                        "check files: README.md; upload files: final.pdf",
                        "파일 확인: README.md;", "파일 확인: README.md::"):
            with self.subTest(command=command), self.assertRaises(WorkflowRefused):
                parse_instructions(command)

    def test_max_stage_and_request_limits(self):
        with self.assertRaises(WorkflowRefused):
            parse_instructions(";".join(["check files: README.md"]*9))
        with self.assertRaises(WorkflowRefused):
            parse_instructions("check files: " + "a"*4097)

    def test_filename_redacted_in_results(self):
        row = run_text_workflow(self.root, "check files: README.md",
                                metadata_consent=True)
        data = json.dumps(row)
        self.assertNotIn("README.md", data)
        self.assertNotIn(str(self.root), data)

    def test_first_missing_stage_skips_remaining(self):
        row = run_text_workflow(self.root,
            "check files: missing.txt; check files: README.md", metadata_consent=True)
        self.assertEqual(row["executed_steps"], 1)
        self.assertEqual(row["status"], "BLOCKED")

    def test_cli_korean_multi_step_e2e(self):
        cmd=[sys.executable, str(ROOT/"tools/flowpilot_text_workflow.py"),
             "--root", str(self.root),
             "--instructions", "파일 확인: README.md; 버전 비교: final.pdf => final_v2.pdf",
             "--approve-local-metadata"]
        process=subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        row=json.loads(process.stdout)
        self.assertEqual(row["executed_steps"], 2)
        self.assertEqual(row["steps"][1]["items"][0]["state"], "VERSION_REVIEW")
        self.assertNotIn("README.md",process.stdout)
        self.assertNotIn(str(self.root),process.stdout)

    def test_cli_rejected_write_command(self):
        cmd=[sys.executable, str(ROOT/"tools/flowpilot_text_workflow.py"),
             "--root", str(self.root),
             "--instructions", "파일 삭제: README.md", "--approve-local-metadata"]
        process=subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 2)
        row=json.loads(process.stdout)
        self.assertEqual(row["status"], "TEXT_WORKFLOW_REFUSED")
        self.assertEqual(row["release_gate"], "HOLD")

if __name__ == "__main__":
    unittest.main()
