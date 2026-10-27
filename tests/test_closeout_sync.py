"""2026-10-28: test lean UGREEN closeout while retaining high-impact checks."""
import importlib.util
import sys
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/"tools"/"check_handoff_sync.py"
spec=importlib.util.spec_from_file_location("handoff_checker",path)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

class HandoffSyncTests(unittest.TestCase):
    def test_docs_only(self):
        self.assertFalse(mod.closeout_errors({"README.md", "START_HERE.md"}))
    def test_regular_code_does_not_force_ten_documents(self):
        self.assertEqual([],mod.closeout_errors({"src/flowpilot/new.py"}))
    def test_test_and_tool_changes_no_bureaucratic_gate(self):
        self.assertEqual([],mod.closeout_errors({"tests/test_new.py","tools/flowpilot_new.py"}))
    def test_canonical_skill_requires_status_and_handoff(self):
        failures=mod.closeout_errors({"skill/flowpilot-nas/SKILL.md"})
        self.assertEqual(2,len(failures))
        self.assertTrue(any("STATUS.md" in x for x in failures))
        self.assertTrue(any("HANDOFF.md" in x for x in failures))
    def test_high_impact_both_documents_pass(self):
        self.assertEqual([],mod.closeout_errors(set(mod.REQUIRED)|{"skill/flowpilot-nas/SKILL.md"}))
    def test_one_missing_high_impact_doc_fails(self):
        failures=mod.closeout_errors({"skill/flowpilot-nas/SKILL.md","STATUS.md"})
        self.assertEqual(1,len(failures))
        self.assertIn("HANDOFF.md",failures[0])
    def test_master_json_without_render_fails(self):
        self.assertEqual(1,len(mod.closeout_errors({"data/master_progress.json"})))
    def test_master_json_with_render_passes(self):
        self.assertEqual([],mod.closeout_errors({"data/master_progress.json","MASTER_PROGRESS.md"}))
    def test_workflow_change_not_bureaucratic(self):
        self.assertEqual([],mod.closeout_errors({".github/workflows/closeout-synchronization.yml"}))

if __name__ == "__main__":
    unittest.main()
