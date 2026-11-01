"""G181 consent regression: never execute the Uliya vendor Checker without approval.

Only CLI wiring is exercised. No official Kit, owner candidate or NAS is loaded.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_official_checker as checker


class G181ConsentCliTests(unittest.TestCase):
    def invoke(self, mode: str, *extra: str, pretend_clean: bool = True):
        buf = StringIO()
        args = ["--candidate-zip", "/missing-owner-g147.zip",
                "--official-kit-zip", "/missing-official-kit.zip",
                "--candidate-profile", "g147", "--mode", mode, *extra]
        with patch.object(checker, "check", return_value={
            "result": "OFFICIAL_STATIC_PASS_REVIEW_ONLY" if pretend_clean else "NOT_EXECUTED",
        }) as called, redirect_stdout(buf):
            code = checker.main(args)
        return code, json.loads(buf.getvalue()), called

    def test_inspect_without_optin_remains_allowed_but_cannot_be_pass(self):
        exit_code, report, called = self.invoke("inspect", pretend_clean=False)
        self.assertEqual(exit_code, 2)
        called.assert_called_once()
        self.assertEqual(called.call_args.kwargs["mode"], "inspect")

    def test_docker_denied_before_private_or_vendor_bytes_are_read(self):
        exit_code, report, called = self.invoke("docker")
        self.assertEqual(exit_code, 2)
        called.assert_not_called()
        self.assertFalse(report["official_checker_executed"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_native_old_flag_alone_cannot_bypass_new_vendor_consent(self):
        exit_code, report, called = self.invoke(
            "native", "--accept-native-code-execution-risk")
        self.assertEqual(exit_code, 2)
        called.assert_not_called()
        self.assertFalse(report["official_checker_executed"])

    def test_native_new_flag_alone_cannot_bypass_native_risk_consent(self):
        exit_code, report, called = self.invoke(
            "native", "--accept-official-code-execution-risk")
        self.assertEqual(exit_code, 2)
        called.assert_not_called()
        self.assertFalse(report["official_checker_executed"])

    def test_docker_explicit_flag_enters_existing_pinned_validation_gate(self):
        exit_code, report, called = self.invoke(
            "docker", "--accept-official-code-execution-risk")
        self.assertEqual(exit_code, 0)
        called.assert_called_once()
        self.assertEqual(called.call_args.kwargs["mode"], "docker")
        self.assertEqual(called.call_args.kwargs["candidate_profile"], "g147")
        self.assertFalse(called.call_args.kwargs["native_risk_approved"])

    def test_native_requires_both_flags_and_remains_subject_to_sha_validation(self):
        exit_code, report, called = self.invoke(
            "native", "--accept-official-code-execution-risk",
            "--accept-native-code-execution-risk")
        self.assertEqual(exit_code, 0)
        called.assert_called_once()
        self.assertTrue(called.call_args.kwargs["native_risk_approved"])
        self.assertEqual(called.call_args.kwargs["candidate_profile"], "g147")


if __name__ == "__main__":
    unittest.main()
