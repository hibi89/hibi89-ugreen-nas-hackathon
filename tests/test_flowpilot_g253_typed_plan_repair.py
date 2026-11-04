"""G253 typed-plan corruption repair; no real NAS or owner sources."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g253_typed_plan_repair as g253
import flowpilot_g233_real_docker_smoke as g233
from flowpilot_g235_typed_dag_docker import PLAN, SOURCE
from flowpilot_g233_real_docker_smoke import SmokeRefused


class G253TypedPlanRepairTests(unittest.TestCase):
    def test_no_approval_never_runs_docker(self):
        with patch.object(g253, "run_synthetic_plan_repair",
                          side_effect=AssertionError("unexpected docker")), \
             patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(g253.main([]), 2)
        payload = json.loads(output.getvalue())
        self.assertFalse(payload["nas_verified"])
        self.assertEqual(payload["release_gate"], "HOLD")

    def test_exact_known_plan_repair_only(self):
        original = g253.BROKEN_PLAN.encode("ascii")
        fixed = g253.repair_only_fixed_plan(
            original, diagnosed_exit=11, approved=True)
        self.assertEqual(fixed, PLAN.encode("ascii"))
        self.assertEqual(original, g253.BROKEN_PLAN.encode("ascii"))
        self.assertEqual(SOURCE.count("alice,"), 2)

    def test_no_other_plan_or_customer_graph_repaired(self):
        variants = [
            PLAN.encode("ascii"),
            b"owner script\n",
            g253.BROKEN_PLAN.replace("group_sum", "delete_files").encode("ascii"),
            (g253.BROKEN_PLAN + "shell_command\n").encode("ascii"),
            g253.BROKEN_PLAN.encode("ascii") + b"\x00",
            None, True, g253.BROKEN_PLAN,
        ]
        for item in variants:
            with self.subTest(value=repr(item)[:40]), self.assertRaises(SmokeRefused):
                g253.repair_only_fixed_plan(item, diagnosed_exit=11, approved=True)

    def test_exit_requires_actual_failure_code_and_flag(self):
        broken = g253.BROKEN_PLAN.encode("ascii")
        for observed in (0, 17, "11", True, -1, None):
            with self.subTest(observed=observed), self.assertRaises(SmokeRefused):
                g253.repair_only_fixed_plan(
                    broken, diagnosed_exit=observed, approved=True)
        with self.assertRaises(SmokeRefused):
            g253.repair_only_fixed_plan(broken, diagnosed_exit=11, approved=False)

    def test_unexpected_container_exits_refused(self):
        self.assertEqual(g253.require_exit("11", "bad_plan"), 11)
        self.assertEqual(g253.require_exit("0", "repaired_plan"), 0)
        for stage, raw in (("bad_plan", "0"), ("bad_plan", 11),
                           ("bad_plan", "11\n"), ("repaired_plan", "11"),
                           ("other", "0"), ("bad_plan", True)):
            with self.subTest(stage=stage, raw=raw), self.assertRaises(SmokeRefused):
                g253.require_exit(raw, stage)

    def test_verifier_accepts_only_explicit_failed_plan_exit(self):
        record = {
            "HostConfig": {"NetworkMode": "none", "ReadonlyRootfs": True,
                           "Privileged": False, "PidsLimit": 32,
                           "Memory": 64*1024*1024, "NanoCpus": 250_000_000,
                           "Binds": None, "Mounts": None, "Devices": None,
                           "CapDrop": ["ALL"],
                           "SecurityOpt": ["no-new-privileges:true"]},
            "Config": {"User": "65534:65534", "Entrypoint": ["/check"]},
            "State": {"Running": False, "Status": "exited", "ExitCode": 11},
            "Mounts": [], "Image": "sha256:" + "a"*64,
        }
        g233.verify_host_config(record, started=True, expected_exit_code=11)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(record, started=True, expected_exit_code=0)
        record["HostConfig"]["NetworkMode"] = "bridge"
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(record, started=True, expected_exit_code=11)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(record, started=True, expected_exit_code=10)

    def test_docker_missing_does_not_start_subprocess(self):
        with patch.object(g253.shutil, "which", return_value=None), \
             patch.object(g253, "checked_run",
                          side_effect=AssertionError("unexpected command")):
            with self.assertRaises(SmokeRefused):
                g253.run_synthetic_plan_repair()

    def test_synthetic_scope_only_and_no_real_rights(self):
        self.assertEqual(g253.STAGES, ("bad_plan", "repaired_plan"))
        self.assertEqual(g253.BROKEN_PLAN.count(g253.BROKEN_NODE), 1)
        self.assertEqual(len(g253.sha(PLAN.encode("ascii"))), 64)
        for item in ("text", None, True):
            with self.assertRaises(SmokeRefused):
                g253.sha(item)


if __name__ == "__main__":
    unittest.main()
