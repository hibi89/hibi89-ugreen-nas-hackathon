"""Actual OS lstat/goal tests; runs on disposable local files in CI."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from tools.flowpilot_real_os_demo import run_real_local_demo, RealLocalDemoRefused


class RealOSFlowPilotDemoTests(unittest.TestCase):
    def test_five_scenarios_perform_real_os_observations(self):
        result = run_real_local_demo()
        self.assertEqual(result["status"], "PASS_REAL_OS_LSTAT_SYNTHETIC_DEMO")
        self.assertEqual(result["scenario_count"], 5)
        self.assertTrue(result["observations_from_real_os"])
        self.assertTrue(result["all_test_fixtures_disposed"])
        self.assertFalse(result["private_hae_executed"])
        self.assertFalse(result["actual_nas_verified"])
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertEqual([r["os_metadata_steps_executed"]
                          for r in result["scenarios"]], [1, 2, 3, 1, 1])

    def test_version_collision_is_real_os_observation_not_simulated_pass(self):
        row = run_real_local_demo()
        case = next(r for r in row["scenarios"] if r["scenario"] == "three_intents")
        self.assertEqual(case["finding_counts"]["VERSION_REVIEW"], 1)
        self.assertEqual(case["planned_intents"], 3)

    def test_missing_required_file_blocks_without_customer_data(self):
        row = run_real_local_demo()
        case = next(r for r in row["scenarios"] if r["scenario"] == "missing_file")
        self.assertEqual(case["status"], "BLOCKED")
        self.assertEqual(case["finding_counts"]["MISSING"], 1)

    def test_results_never_disclose_fixture_names_paths_or_contents(self):
        raw = json.dumps(run_real_local_demo(), ensure_ascii=False)
        for forbidden in ("README.md", "README_final.md", "missing.md",
                          "disposable test fixture", "customer-secret"):
            self.assertNotIn(forbidden, raw)

    def test_unapproved_preview_never_performs_os_inspection(self):
        from tools.flowpilot_real_os_demo import process_goal as real_process
        def guarded(*args, **kwargs):
            row = real_process(*args, **kwargs)
            if kwargs.get("metadata_consent") is False:
                self.assertEqual(row["executed_steps"], 0)
                self.assertFalse(row["owner_folder_metadata_accessed"])
            return row
        with patch("tools.flowpilot_real_os_demo.process_goal", side_effect=guarded):
            self.assertEqual(run_real_local_demo()["scenario_count"], 5)

    def test_tampered_observation_is_rejected_instead_of_pass(self):
        from tools.flowpilot_real_os_demo import process_goal as original
        def tampered(*args, **kwargs):
            row = original(*args, **kwargs)
            if kwargs.get("metadata_consent"):
                row["file_contents_opened"] = True
            return row
        with patch("tools.flowpilot_real_os_demo.process_goal", side_effect=tampered):
            with self.assertRaisesRegex(RealLocalDemoRefused, "UNVERIFIED_OS_OBSERVATION"):
                run_real_local_demo()


if __name__ == "__main__":
    unittest.main()
