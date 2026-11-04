"""G259: real CLI exit status must match fresh G226+Kit source admission.

Historical code G257 returned exit 0 even when current Skill was omitted.
These tests exercise a deliberately pre-trial CLI, not actual registered NAS.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g257_native_trial_matrix as cli


def args_in(root: Path, include_skill: bool = True):
    k=root / "kit.zip"
    r=root / "g256.json"
    s=root / "g226.zip"
    k.write_bytes(b"test only kit bytes")
    r.write_text('{"test":"only"}',encoding="utf-8")
    s.write_bytes(b"test only candidate source")
    argv=["--official-kit",str(k),"--g256-private-receipt",str(r)]
    if include_skill:
        argv += ["--candidate-skill",str(s)]
    return argv


class G259ActualCLIExitGateTests(unittest.TestCase):
    def test_missing_current_skill_fails_without_private_file_read(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(cli,"prepare_trial",side_effect=AssertionError("must not call")), \
                 patch("sys.stdout",new_callable=io.StringIO) as stdout:
                self.assertEqual(cli.main(args_in(Path(temp),False)),2)
            body=json.loads(stdout.getvalue())
            self.assertEqual(body["status"],"G259_CURRENT_G226_SKILL_REQUIRED")
            self.assertFalse(body["current_skill_rechecked"])
            self.assertFalse(body["nas_verified"])

    def test_actual_preflight_refusal_preserves_fail_closed_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(cli,"prepare_trial",side_effect=cli.TrialReadinessRefused(
                 "NEVER LOG THIS OWNER PATH /volume1/private")), \
                 patch("sys.stdout",new_callable=io.StringIO) as stdout:
                self.assertEqual(cli.main(args_in(Path(temp))),2)
            body=json.loads(stdout.getvalue())
            self.assertEqual(body["status"],"G257_OFFLINE_TRIAL_READINESS_REFUSED")
            self.assertNotIn("/volume1/private",stdout.getvalue())
            self.assertFalse(body["nas_verified"])

    def test_unbound_or_forged_status_never_exit_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            for status in ("AWAITING_CURRENT_G226_SKILL_BYTES",
                           "SYNTHETIC_TRIAL_PLAN_ONLY",
                           "SOURCE_BOUND_OFFLINE_TRIAL_PLAN_READY",
                           "CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY"):
                fake={
                    "status":status,"current_skill_rechecked":False,
                    "current_skill_instruction_sha256":[],
                    "may_activate_nas_trial":False,
                    "nas_verified":False,"release_gate":"HOLD"}
                with self.subTest(status=status), \
                     patch.object(cli,"prepare_trial",return_value=fake), \
                     patch("sys.stdout",new_callable=io.StringIO) as stdout:
                    self.assertEqual(cli.main(args_in(Path(temp))),2)
                    self.assertEqual(json.loads(stdout.getvalue())["status"],
                                     "G259_REAL_SOURCE_BOUND_OFFLINE_PREFLIGHT_INCOMPLETE")

    def test_overclaimed_runtime_or_release_never_exit_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            for field,value in [
                ("nas_verified",True),
                ("may_activate_nas_trial",True),
                ("release_gate","APPROVED"),
                ("current_skill_instruction_sha256",[]),
                ("current_skill_rechecked",False),
            ]:
                packet={
                    "status":"CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY",
                    "current_skill_rechecked":True,
                    "current_skill_instruction_sha256":["a"*64,"b"*64],
                    "may_activate_nas_trial":False,
                    "nas_verified":False,"release_gate":"HOLD"}
                packet[field]=value
                with self.subTest(field=field), \
                     patch.object(cli,"prepare_trial",return_value=packet), \
                     patch("sys.stdout",new_callable=io.StringIO):
                    self.assertEqual(cli.main(args_in(Path(temp))),2)

    def test_exact_source_bound_offline_only_status_can_exit_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            packet={
                "status":"CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY",
                "current_skill_rechecked":True,
                "current_skill_instruction_sha256":["a"*64,"b"*64],
                "may_activate_nas_trial":False,
                "nas_verified":False,"release_gate":"HOLD"}
            with patch.object(cli,"prepare_trial",return_value=packet), \
                 patch("sys.stdout",new_callable=io.StringIO) as stdout:
                self.assertEqual(cli.main(args_in(Path(temp))),0)
            out=json.loads(stdout.getvalue())
            self.assertFalse(out["nas_verified"])
            self.assertFalse(out["may_activate_nas_trial"])


if __name__=="__main__":
    unittest.main()
