"""G190: direct Python API cannot bypass vendor-code execution consent.

Synthetic only. No vendor JavaScript, Docker, NAS, network or real owner archives.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_official_checker as gate


class G190CheckerEntrypointConsentTests(unittest.TestCase):
    def setUp(self):
        self.missing_candidate = Path("/g190-nonexistent/private-candidate.zip")
        self.missing_kit = Path("/g190-nonexistent/vendor.zip")

    def test_direct_docker_refused_before_private_archive_read(self):
        with patch.object(gate, "_read_pinned", side_effect=AssertionError("read happened")) as read, \
             patch.object(gate, "_execute", side_effect=AssertionError("vendor executed")):
            with self.assertRaisesRegex(gate.VerificationRefused, "explicit owner approval"):
                gate.check(self.missing_candidate, self.missing_kit,
                           mode="docker", candidate_profile="g188")
        read.assert_not_called()

    def test_direct_native_separate_approval_even_if_native_flag_true(self):
        with patch.object(gate, "_read_pinned", side_effect=AssertionError("read happened")) as read:
            with self.assertRaisesRegex(gate.VerificationRefused, "explicit owner approval"):
                gate.check(self.missing_candidate, self.missing_kit, mode="native",
                           candidate_profile="g188", native_risk_approved=True)
        read.assert_not_called()

    def test_truthy_untyped_approval_is_not_owner_consent(self):
        for forged in (1, "yes", "true", [], {"approved": True}):
            with self.subTest(forged=forged):
                with patch.object(gate, "_read_pinned",
                                  side_effect=AssertionError("read happened")) as read:
                    with self.assertRaisesRegex(gate.VerificationRefused, "explicit owner approval"):
                        gate.check(self.missing_candidate, self.missing_kit, mode="docker",
                                   candidate_profile="g188", official_risk_approved=forged)
                read.assert_not_called()

    def test_native_requires_distinct_native_risk_approval(self):
        with patch.object(gate, "_read_pinned", side_effect=AssertionError("read happened")) as read:
            with self.assertRaisesRegex(gate.VerificationRefused, "Native execution requires"):
                gate.check(self.missing_candidate, self.missing_kit, mode="native",
                           candidate_profile="g188", official_risk_approved=True)
        read.assert_not_called()

    def test_official_consent_does_not_bypass_sha_or_missing_source(self):
        with self.assertRaisesRegex(gate.VerificationRefused, "Missing, nonregular"):
            gate.check(self.missing_candidate, self.missing_kit, mode="docker",
                       candidate_profile="g188", official_risk_approved=True)

    def test_inspect_still_enters_read_only_validation_without_code_execution(self):
        with patch.object(gate, "_read_pinned",
                          side_effect=gate.VerificationRefused("synthetic no input")) as read, \
             patch.object(gate, "_execute", side_effect=AssertionError("vendor executed")):
            with self.assertRaisesRegex(gate.VerificationRefused, "synthetic no input"):
                gate.check(self.missing_candidate, self.missing_kit, mode="inspect",
                           candidate_profile="g188")
        read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
