"""G255 static + behavior tests; real Docker only in G233 CI, never on owner NAS."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g233_real_docker_smoke as g233
import flowpilot_g255_timeout_recovery as g255
from flowpilot_g235_typed_dag_docker import C_SOURCE, PLAN, SOURCE
from flowpilot_g233_real_docker_smoke import SmokeRefused, SmokeTimedOut


def inspected(exit_code):
    return {
        "HostConfig": {
            "NetworkMode":"none", "ReadonlyRootfs":True, "Privileged":False,
            "PidsLimit":32,"Memory":64*1024*1024,"NanoCpus":250_000_000,
            "Binds":None,"Mounts":None,"Devices":None,"CapDrop":["ALL"],
            "SecurityOpt":["no-new-privileges:true"]
        },
        "Config":{"User":"65534:65534","Entrypoint":["/check"]},
        "State":{"Running":False,"Status":"exited","ExitCode":exit_code},
        "Mounts":[],"Image":"sha256:" + "a"*64
    }


class G255RealTimeoutRecoveryTests(unittest.TestCase):
    def test_requires_explicit_synthetic_approval(self):
        with patch.object(g255,"run_real_timeout_recovery",
                          side_effect=AssertionError("must not run")), \
             patch("sys.stdout",new_callable=io.StringIO) as out:
            self.assertEqual(g255.main([]),2)
        self.assertEqual(json.loads(out.getvalue())["release_gate"],"HOLD")

    def test_recovery_requires_both_true_timeout_and_exact_kill(self):
        self.assertTrue(g255.authorize_recovery(
            timeout_seen=True,terminated_exit=137,approved=True))
        for seen,code,approved in [
            (False,137,True),(True,0,True),(True,17,True),
            (True,"137",True),(True,True,True),(True,137,False),
            (1,137,True),(None,137,True)]:
            with self.subTest(seen=seen,code=code,approved=approved):
                with self.assertRaises(SmokeRefused):
                    g255.authorize_recovery(timeout_seen=seen,
                                            terminated_exit=code,
                                            approved=approved)

    def test_timeout_class_only_on_subprocess_timeout(self):
        with patch.object(g233, "_local_docker_socket_ready",return_value=True), \
             patch.object(g233.subprocess,"run",side_effect=subprocess.TimeoutExpired(
                 cmd=["docker","wait","cid"],timeout=3)):
            with self.assertRaises(SmokeTimedOut):
                g233.checked_run(["docker","wait","synthetic"],timeout=3)
        with patch.object(g233, "_local_docker_socket_ready",return_value=True), \
             patch.object(g233.subprocess,"run",return_value=subprocess.CompletedProcess(
                 [],1,"","untrusted stderr")):
            with self.assertRaises(SmokeRefused) as caught:
                g233.checked_run(["docker","wait","synthetic"],timeout=3)
            self.assertNotIsInstance(caught.exception,SmokeTimedOut)
            self.assertNotIn("untrusted stderr",str(caught.exception))

    def test_docker_inspection_rejects_any_spoofed_hardening(self):
        g233.verify_host_config(inspected(137),started=True,
                                expected_exit_code=137)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(inspected(0),started=True,
                                    expected_exit_code=137)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(inspected(137),started=True,
                                    expected_exit_code=136)
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(inspected(137),started=True,
                                    expected_exit_code=True)
        weak=inspected(137)
        weak["HostConfig"]["ReadonlyRootfs"]=False
        with self.assertRaises(SmokeRefused):
            g233.verify_host_config(weak,started=True,expected_exit_code=137)

    def test_kill_exit_is_strict_text(self):
        self.assertEqual(g255.require_wait_terminated("137"),137)
        for item in (137,"137\n","0","143",True,None):
            with self.subTest(item=repr(item)),self.assertRaises(SmokeRefused):
                g255.require_wait_terminated(item)

    def test_only_two_code_owned_stages(self):
        self.assertEqual(g255.STAGES,("stalled","healthy"))
        self.assertEqual(g255.WAIT_TIMEOUT_SECONDS,3)
        self.assertIn("pause()",g255.STALL_SOURCE)
        self.assertEqual(PLAN.count("\n"),4)
        self.assertEqual(SOURCE.count("bob,300"),1)
        self.assertIn("SYNTHETIC_TYPED_DAG_COMPLETE",C_SOURCE)
        self.assertFalse(g255.STALL_SOURCE == C_SOURCE)

    def test_no_docker_or_compiler_never_invokes_commands(self):
        with patch.object(g255.shutil,"which",return_value=None), \
             patch.object(g255,"checked_run",
                          side_effect=AssertionError("unexpected execution")):
            with self.assertRaises(SmokeRefused):
                g255.run_real_timeout_recovery()

    def test_digest_and_improper_data_are_denied(self):
        self.assertEqual(len(g255.sha(b"safe")),64)
        for val in (True,None,"safe"):
            with self.assertRaises(SmokeRefused):
                g255.sha(val)


if __name__ == "__main__":
    unittest.main()
