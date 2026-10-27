"""G63: functional local OS multi-step workflow, not Uliya/NAS."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_local_workflow import run_workflow, WorkflowRefused

class G63SequentialLocalWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_bytes(b"synthetic local data")
        (self.root / "review.pdf").write_bytes(b"v1")
    def recipe(self, *steps):
        return {"schema": "flowpilot-local-readonly-v1", "steps": list(steps)}
    def step(self, goal="check required files", required=None):
        return {"goal": goal, "required": ["README.md"] if required is None else required}
    def test_two_actual_local_checks_without_file_content(self):
        r = run_workflow(self.root, self.recipe(self.step(),
            self.step("check handoff deliverables", ["review.pdf"])), metadata_consent=True)
        self.assertEqual(r["executed_steps"], 2)
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual([s["items"][0]["state"] for s in r["steps"]], ["PRESENT", "PRESENT"])
        self.assertFalse(r["owner_folder_contents_opened"])
        self.assertFalse(r["nas_verified"])
        self.assertNotIn("README.md", json.dumps(r))
    def test_blocked_first_stage_skips_second(self):
        r = run_workflow(self.root, self.recipe(self.step(required=["absent.txt"]),
            self.step()), metadata_consent=True)
        self.assertEqual((r["status"], r["executed_steps"]), ("BLOCKED", 1))
    def test_no_consent_does_not_inspect_root(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("access")):
            r = run_workflow(self.root, self.recipe(self.step()))
        self.assertEqual((r["status"], r["executed_steps"]), ("WAITING_APPROVAL", 0))
    def test_mutating_later_step_blocks_all_before_access(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("access")):
            with self.assertRaises(WorkflowRefused):
                run_workflow(self.root, self.recipe(self.step(),
                    self.step("delete files")), metadata_consent=True)
    def test_traversal_in_later_step_blocks_before_access(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=AssertionError("access")):
            with self.assertRaises(WorkflowRefused):
                run_workflow(self.root, self.recipe(self.step(),
                    self.step(required=["../secret.txt"])), metadata_consent=True)
    def test_schema_limits_and_extra_fields_rejected(self):
        for spec in (self.recipe(), self.recipe(*(self.step() for _ in range(9))),
                self.recipe({"goal":"check files","required":["README.md"],"upload":True}),
                self.recipe(self.step(required=[f"f{i}.txt" for i in range(101)]))):
            with self.subTest(spec=str(spec)[:30]), self.assertRaises(WorkflowRefused):
                run_workflow(self.root, spec, metadata_consent=True)
    def test_filesystem_error_is_fail_closed_and_redacted(self):
        with patch("flowpilot_owner_local_audit._valid_root", side_effect=OSError("SECRET")):
            r = run_workflow(self.root, self.recipe(self.step()), metadata_consent=True)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["steps"][0]["status"], "NOT_CHECKED")
        self.assertNotIn("SECRET", json.dumps(r))
    def test_cli_real_two_step_smoke(self):
        path = self.root / "recipe.json"
        path.write_text(json.dumps(self.recipe(self.step(),
            self.step("compare versions", ["review.pdf"]))), encoding="utf-8")
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_local_workflow.py"),
            "--root", str(self.root), "--recipe", str(path), "--approve-local-metadata"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["executed_steps"], 2)
        self.assertNotIn("README.md", result.stdout)
        self.assertNotIn(str(self.root), result.stdout)
    def test_cli_no_consent_has_zero_executed_steps(self):
        path = self.root / "recipe.json"
        path.write_text(json.dumps(self.recipe(self.step())), encoding="utf-8")
        cmd = [sys.executable, str(ROOT / "tools/flowpilot_local_workflow.py"),
            "--root", str(self.root), "--recipe", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "WAITING_APPROVAL")

if __name__ == "__main__":
    unittest.main()
