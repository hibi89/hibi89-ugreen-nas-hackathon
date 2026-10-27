"""G58 product-minimum offline CLI: five scenarios + consent/intent boundaries."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_mvp_cli import DEFAULT_REQUESTS, run_mvp


class FlowPilotRunnableMVPTests(unittest.TestCase):
    def test_all_five_synthetic_flows_have_executable_pipeline(self):
        self.assertEqual(len(DEFAULT_REQUESTS), 5)
        for name in DEFAULT_REQUESTS:
            with self.subTest(name=name):
                result = run_mvp(name)
                self.assertEqual(result["mode"], "SYNTHETIC_OFFLINE_MVP_ONLY")
                self.assertNotEqual(result["status"], "READY")
                self.assertFalse(result["actual_nas_verified"])
                self.assertFalse(result["registered_agent_invoked"])
                self.assertEqual(result["release_gate"], "HOLD")

    def test_complete_fixture_reports_two_present_without_nas_ready(self):
        r = run_mvp("complete_synthetic_handoff")
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual([x["state"] for x in r["required_items"]],
                         ["PRESENT", "PRESENT"])
        self.assertEqual([x["step"] for x in r["planned_expert_steps_not_executed"]],
                         ["inventory", "versions", "report"])

    def test_missing_required_blocks_only_in_claimed_complete_fixture(self):
        r = run_mvp("missing_required_synthetic")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["required_items"][-1]["state"], "MISSING")

    def test_two_version_candidates_require_review(self):
        r = run_mvp("conflicting_versions_synthetic")
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual(r["required_items"][0]["state"], "VERSION_REVIEW")

    def test_denied_or_truncated_listing_is_not_absence(self):
        r = run_mvp("truncated_or_denied_synthetic")
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual(r["required_items"][0]["state"], "NOT_CHECKED")

    def test_symlink_unverified_is_not_present(self):
        r = run_mvp("symlink_unknown_synthetic")
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertEqual(r["required_items"][0]["state"], "NOT_CHECKED")

    def test_korean_goal_selects_readonly_pipeline(self):
        r = run_mvp("complete_synthetic_handoff", "납품 파일 확인해줘")
        self.assertEqual(r["goal_type"], "HANDOFF_AUDIT")
        self.assertEqual(r["status"], "NEEDS_REVIEW")

    def test_mutating_goal_cannot_get_planned_steps(self):
        r = run_mvp("complete_synthetic_handoff", "파일 옮겨줘")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["planned_expert_steps_not_executed"], [])
        self.assertEqual(r["required_items"], [])

    def test_unknown_goal_asks_user_instead_of_running(self):
        r = run_mvp("complete_synthetic_handoff", "create a new application")
        self.assertEqual(r["status"], "WAITING_USER")
        self.assertEqual(r["planned_expert_steps_not_executed"], [])

    def test_document_intent_not_authorized_by_default(self):
        r = run_mvp("complete_synthetic_handoff", "summarize document")
        self.assertEqual(r["goal_type"], "SUMMARIZE_SELECTED")
        self.assertNotIn("document", [x["step"]
                                      for x in r["planned_expert_steps_not_executed"]])
        self.assertTrue(r["questions"])

    def test_invalid_scenario_or_large_request_refused(self):
        with self.assertRaises(ValueError):
            run_mvp("not-a-scenario")
        with self.assertRaises(ValueError):
            run_mvp("complete_synthetic_handoff", "X" * 2049)

    def test_cli_subprocess_emits_machine_readable_json(self):
        script = ROOT / "tools" / "flowpilot_mvp_cli.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--scenario", "conflicting_versions_synthetic"],
            capture_output=True, text=True, timeout=15, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual(result["required_items"][0]["state"], "VERSION_REVIEW")
        self.assertFalse(result["devpost_submitted"])


if __name__ == "__main__":
    unittest.main()
