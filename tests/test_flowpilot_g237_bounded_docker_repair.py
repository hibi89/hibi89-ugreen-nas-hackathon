"""G237: real-error-driven synthetic repair policy, never owner file edits."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g237_bounded_docker_repair as g237
import flowpilot_g233_real_docker_smoke as g233
from flowpilot_g233_real_docker_smoke import SmokeRefused
from flowpilot_g235_typed_dag_docker import SOURCE, PLAN


class G237RealDockerRepairTests(unittest.TestCase):
    def test_manual_synthetic_flag_required_and_no_implicit_docker(self):
        with patch.object(g237,"run_bounded_repair",
                          side_effect=AssertionError("must not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as stream:
            self.assertEqual(g237.main([]), 2)
        data = json.loads(stream.getvalue())
        self.assertEqual(data["status"], "G237_EXPLICIT_SYNTHETIC_APPROVAL_REQUIRED")
        self.assertFalse(data["nas_verified"])

    def test_only_identified_real_exit_17_allows_one_copy(self):
        broken = g237.BROKEN_SOURCE.encode("ascii")
        result = g237.repair_one_synthetic_decimal(
            broken, diagnosed_exit=17, approved=True)
        self.assertEqual(result, SOURCE.encode("ascii"))
        self.assertNotEqual(g237.digest(result), g237.digest(broken))
        self.assertEqual(broken, g237.BROKEN_SOURCE.encode("ascii"))

    def test_no_approval_or_invalid_exit_refused(self):
        for exit_code in (None, 0, "17", True, 18, 127, -1):
            with self.subTest(exit_code=exit_code), self.assertRaises(SmokeRefused):
                g237.repair_one_synthetic_decimal(
                    g237.BROKEN_SOURCE.encode("ascii"),
                    diagnosed_exit=exit_code, approved=True)
        with self.assertRaises(SmokeRefused):
            g237.repair_one_synthetic_decimal(
                g237.BROKEN_SOURCE.encode("ascii"),
                diagnosed_exit=17, approved=False)

    def test_unknown_or_customer_csv_is_not_repaired(self):
        for data in (b"customer,amount_cents\nbob,3O0\n",
                     SOURCE.encode("ascii"),
                     g237.BROKEN_SOURCE.replace("alice,125", "alice,126").encode("ascii"),
                     (g237.BROKEN_SOURCE + "bob,3O0\n").encode("ascii"),
                     "customer data",
                     None):
            with self.subTest(data=str(data)[:40]), self.assertRaises(SmokeRefused):
                g237.repair_one_synthetic_decimal(data, diagnosed_exit=17,
                                                   approved=True)

    def test_docker_wait_exit_is_not_treated_as_success(self):
        for stage, observed in (("broken","17"),("repaired","0")):
            self.assertEqual(g237.require_exit(observed,stage), int(observed))
        for bad_stage, observed in (("broken","0"),("broken","17\n"),
                                    ("repaired","17"),("invalid","0"),
                                    ("broken",17),("broken","true"),
                                    ("broken","-17")):
            with self.subTest(stage=bad_stage, obs=observed), \
                 self.assertRaises(SmokeRefused):
                g237.require_exit(observed,bad_stage)

    def test_actual_failure_exit_attestation_checks_security_config(self):
        payload = {
            "HostConfig": {
                "NetworkMode": "none", "ReadonlyRootfs": True,
                "Privileged": False, "PidsLimit": 32,
                "Memory": 64*1024*1024, "NanoCpus": 250_000_000,
                "Binds": None, "Mounts": None, "Devices": None,
                "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges:true"]
            },
            "Config": {"User": "65534:65534", "Entrypoint": ["/check"]},
            "State": {"Running": False, "Status": "exited", "ExitCode": 17},
            "Mounts": [], "Image": "sha256:" + "a"*64
        }
        g233.verify_host_config(payload,started=True,expected_exit_code=17)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(payload,started=True,expected_exit_code=0)
        altered = json.loads(json.dumps(payload))
        altered["HostConfig"]["NetworkMode"] = "bridge"
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(altered,started=True,expected_exit_code=17)
        altered = json.loads(json.dumps(payload))
        altered["State"]["Status"] = "created"
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(altered,started=True,expected_exit_code=17)

    def test_invalid_expected_exit_fails_closed(self):
        for expected in (True, "17", 1, -1, None):
            with self.subTest(expected=expected), self.assertRaises(SmokeRefused):
                g233.verify_host_config({},started=True,expected_exit_code=expected)

    def test_only_four_fixed_typed_nodes_and_no_implicit_owner_paths(self):
        self.assertEqual(PLAN.count("\n"),4)
        self.assertEqual(g237.STAGES,("broken","repaired"))
        self.assertEqual(g237.EXPECTED_EXITS,{"broken":17,"repaired":0})
        self.assertEqual(g237.BROKEN_SOURCE.count("3O0"),1)
        self.assertNotIn("volumes", g237.APPROVAL)
        self.assertEqual(SOURCE.count("bob,300"),1)

    def test_missing_docker_refused_without_shell_execution(self):
        with patch.object(g237.shutil,"which",return_value=None), \
             patch.object(g237,"checked_run",side_effect=AssertionError("called")):
            with self.assertRaises(SmokeRefused):
                g237.run_bounded_repair()

    def test_digest_requires_bytes(self):
        self.assertEqual(len(g237.digest(b"test")),64)
        for input_value in ("test",None,True):
            with self.assertRaises(SmokeRefused):
                g237.digest(input_value)


if __name__ == "__main__":
    unittest.main()
