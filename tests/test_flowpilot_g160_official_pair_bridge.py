"""G160 bridge tests use no private owner bytes, authentic kit or vendor JS."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g160_official_pair_bridge as g160


class G160Test(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.owner = self.folder / "owner-private-review.zip"
        self.owner.write_bytes(b"synthetic-owner-private-review")
        self.kit = self.folder / "uliya-official-kit.zip"
        self.kit.write_bytes(b"synthetic-kit")
        self.verified = {"release_gate":"HOLD"}
        self.claims = {"release_gate":"HOLD","documentary_claims_cross_referenced":7}
        self.zip = b"synthetic-skill"
        self.pair_mock = patch.object(g160.pair, "verify_package", return_value=self.verified)
        self.claim_mock = patch.object(g160.claims, "review_package", return_value=self.claims)
        self.pair_mock.start(); self.claim_mock.start()
        self.addCleanup(self.pair_mock.stop); self.addCleanup(self.claim_mock.stop)

    def test_default_no_kit_never_calls_vendor(self):
        with patch.object(g160.official, "check", side_effect=AssertionError("vendor invoked")):
            report = g160.audit(self.owner)
        self.assertEqual(report["status"],"EXACT_OWNER_PAIR_VERIFIED_OFFICIAL_KIT_MISSING")
        self.assertFalse(report["official_checker_executed"])
        self.assertEqual(report["release_gate"],"HOLD")

    def test_native_flag_without_kit_refuses_before_vendor(self):
        with patch.object(g160.official, "check", side_effect=AssertionError("vendor invoked")):
            with self.assertRaisesRegex(g160.BridgeRefused,"OFFICIAL_KIT_REQUIRED"):
                g160.audit(self.owner, execute_official_native_code=True)

    def test_owner_pair_check_refuses_before_kit(self):
        with patch.object(g160.pair,"verify_package",side_effect=g160.pair.PairRefused("INVALID")):
            with patch.object(g160.official, "check",side_effect=AssertionError("vendor invoked")):
                with self.assertRaises(g160.pair.PairRefused):
                    g160.audit(self.owner,self.kit)

    def test_claim_gate_refuses_vendor(self):
        with patch.object(g160.claims,"review_package",return_value={"release_gate":"HOLD","documentary_claims_cross_referenced":6}):
            with patch.object(g160.official,"check",side_effect=AssertionError("vendor invoked")):
                with self.assertRaisesRegex(g160.BridgeRefused,"DOCUMENTARY_GATE"):
                    g160.audit(self.owner,self.kit)

    def test_wrong_kit_sha_refuses_without_vendor(self):
        with patch.object(g160.official,"check",side_effect=AssertionError("vendor invoked")):
            with self.assertRaisesRegex(g160.BridgeRefused,"KIT_SHA256"):
                g160.audit(self.owner,self.kit)

    def test_kit_symlink_refused(self):
        symlink=self.folder/"kit-link.zip"
        try:
            symlink.symlink_to(self.kit)
        except (OSError,NotImplementedError):
            self.skipTest("symlink disabled")
        with self.assertRaisesRegex(g160.BridgeRefused,"SYMLINK"):
            g160.audit(self.owner,symlink)

    def test_invalid_risk_flag_refused(self):
        with self.assertRaisesRegex(g160.BridgeRefused,"INVALID_RISK"):
            g160.audit(self.owner,execute_official_native_code="true")

    def test_inspect_requires_upstream_nonexecution_proof(self):
        kit=self.kit.read_bytes()
        with patch.object(g160.official,"VENDOR_ZIP_SHA",sha256(kit).hexdigest()), \
             patch.object(g160.ZipFile,"__init__",autospec=True) as zinit:
            # No authentic ZIP exists in public CI: refuse before invoking code.
            zinit.side_effect=ValueError("synthetic not a ZIP")
            with self.assertRaises(ValueError):
                g160.audit(self.owner,self.kit)

    def test_patched_authenticated_inspect_uses_exact_profile_and_hold(self):
        from unittest.mock import MagicMock
        fake_kit=self.kit.read_bytes()
        fake_inner=MagicMock()
        fake_inner.__enter__.return_value.read.return_value=b"synthetic-skill"
        fake_inner.__exit__.return_value=False
        with patch.object(g160.official,"VENDOR_ZIP_SHA",sha256(fake_kit).hexdigest()), \
             patch.object(g160.official,"G147_CANDIDATE_ZIP_SHA",sha256(b"synthetic-skill").hexdigest()), \
             patch.object(g160,"ZipFile",return_value=fake_inner), \
             patch.object(g160.official,"check",return_value={
                "status":"EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN",
                "official_checker_executed":False}) as checker:
            r=g160.audit(self.owner,self.kit)
        self.assertEqual(r["status"],"G158_AUTHENTIC_ULIYA_KIT_INSPECTED_NO_VENDOR_CODE")
        self.assertFalse(r["official_checker_executed"])
        self.assertEqual(checker.call_args.kwargs["candidate_profile"],"g147")
        self.assertEqual(checker.call_args.kwargs["mode"],"inspect")
        self.assertFalse(checker.call_args.kwargs["native_risk_approved"])

    def test_explicit_native_authorization_result_still_hold(self):
        from unittest.mock import MagicMock
        fake_kit=self.kit.read_bytes()
        z=MagicMock()
        z.__enter__.return_value.read.return_value=b"synthetic-skill"
        with patch.object(g160.official,"VENDOR_ZIP_SHA",sha256(fake_kit).hexdigest()), \
             patch.object(g160.official,"G147_CANDIDATE_ZIP_SHA",sha256(b"synthetic-skill").hexdigest()), \
             patch.object(g160,"ZipFile",return_value=z), \
             patch.object(g160.official,"check",return_value={
                 "status":"OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE",
                 "official_checker_executed":True,
                 "result":"OFFICIAL_WARN_OR_FAIL_HOLD","diagnostic_codes":["NOT_READY"]}) as checker:
            report=g160.audit(self.owner,self.kit,execute_official_native_code=True)
        self.assertEqual(report["status"],"G158_FIRST_PARTY_CHECKER_WARN_OR_FAIL_HOLD")
        self.assertEqual(report["release_gate"],"HOLD")
        self.assertTrue(report["official_checker_executed"])
        self.assertEqual(checker.call_args.kwargs["mode"],"native")
        self.assertTrue(checker.call_args.kwargs["native_risk_approved"])

    def test_synthetic_official_pass_never_releases(self):
        from unittest.mock import MagicMock
        kit=self.kit.read_bytes()
        z=MagicMock()
        z.__enter__.return_value.read.return_value=b"synthetic-skill"
        with patch.object(g160.official,"VENDOR_ZIP_SHA",sha256(kit).hexdigest()), \
             patch.object(g160.official,"G147_CANDIDATE_ZIP_SHA",sha256(b"synthetic-skill").hexdigest()), \
             patch.object(g160,"ZipFile",return_value=z), \
             patch.object(g160.official,"check",return_value={
                 "status":"OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE",
                 "official_checker_executed":True,"result":"OFFICIAL_STATIC_PASS_REVIEW_ONLY"}):
            result=g160.audit(self.owner,self.kit,execute_official_native_code=True)
        self.assertEqual(result["status"],"G158_FIRST_PARTY_CHECKER_STATIC_PASS_OWNER_REVIEW_ONLY")
        self.assertFalse(result["owner_rights_approved"])
        self.assertEqual(result["release_gate"],"HOLD")

    def test_bad_missing_private_archive_cli_redacted(self):
        secret=str(self.folder/"secret-private-file.zip")
        out=io.StringIO()
        with redirect_stdout(out):
            code=g160.main(["--review-package",secret])
        self.assertEqual(code,2)
        self.assertNotIn(secret,out.getvalue())
        self.assertIn('"release_gate": "HOLD"',out.getvalue())


if __name__ == "__main__":
    unittest.main()
