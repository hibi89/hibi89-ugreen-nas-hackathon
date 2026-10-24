"""Test CI's mandatory same-work-closeout rule without GitHub calls."""
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
    def test_docs_only_do_not_trigger(self):
        self.assertFalse(mod.closeout_errors({"README.md","START_HERE.md"}))
    def test_feature_requires_all_handoff_files(self):
        errors=mod.closeout_errors({"src/projectready/example.py"})
        self.assertTrue(errors)
        self.assertTrue(any("LIVE_STATE.json" in line for line in errors))
    def test_full_closeout_passes(self):
        self.assertEqual([],mod.closeout_errors({"src/projectready/example.py"}|set(mod.REQUIRED)))
    def test_test_change_requires_handoff(self):
        self.assertTrue(mod.closeout_errors({"tests/test_case.py"}))
    def test_docs_architecture_change_requires_handoff(self):
        self.assertTrue(mod.closeout_errors({"docs/architecture/G6.md"}))
    def test_official_skill_change_requires_handoff(self):
        self.assertTrue(mod.closeout_errors({"SKILL.md"}))
    def test_only_textual_handoff_changes_do_not_require_source_gate(self):
        self.assertEqual([],mod.closeout_errors({"docs/roles/lead/LIVE_HANDOFF.md",
                                                 "docs/roles/lead/DAILY_PROGRESS.json"}))

    def test_workflow_only_ignored(self):
        self.assertEqual([],mod.closeout_errors({".github/workflows/closeout-synchronization.yml"}))
    def test_single_missing_document_fails(self):
        changes={"src/projectready/example.py"}|(set(mod.REQUIRED)-{"docs/roles/lead/WORK_TIME_LOG.md"})
        errors=mod.closeout_errors(changes)
        self.assertEqual(2,len(errors))
        self.assertIn("WORK_TIME_LOG.md",errors[-1])

if __name__=="__main__":
    unittest.main()
