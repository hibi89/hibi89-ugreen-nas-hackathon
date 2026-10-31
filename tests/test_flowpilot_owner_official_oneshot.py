"""G150: no access to external network or real owner artifacts in CI."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_owner_official_oneshot as g150


class G150Test(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        for name in (g150.PDF_FILE, g150.ZIP_FILE, g150.MANIFEST_FILE):
            (self.directory / name).write_bytes(b"synthetic no owner data")
        self.pair = {"status": "G147_EXACT_LOCAL_PAIR_VERIFIED_NOT_OFFICIAL",
                     "pdf_text_verified": False}

    def test_default_is_offline_local_pair_only(self):
        with patch.object(g150, "verify_owner_pair", return_value=self.pair), \
             patch.object(g150, "_download_authenticated_kit",
                          side_effect=AssertionError("unexpected network")), \
             patch.object(g150.official, "check",
                          side_effect=AssertionError("vendor executed")):
            r = g150.run(self.directory)
        self.assertEqual(r["status"], "G147_LOCAL_PRECHECK_ONLY_NO_NETWORK")
        self.assertFalse(r["official_checker_executed"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_native_without_download_approval_refuses_before_any_input(self):
        with patch.object(g150, "verify_owner_pair",
                          side_effect=AssertionError("read owner input")):
            with self.assertRaises(g150.OwnerCheckRefused):
                g150.run(self.directory, execute_official_native_code=True)

    def test_real_file_no_valid_sha_fails_before_network(self):
        with patch.object(g150, "_download_authenticated_kit",
                          side_effect=AssertionError("unexpected network")):
            with self.assertRaises(g150.local_gate.ArtifactRefused):
                g150.run(self.directory, download_official_kit=True)

    def test_vendor_download_valid_sha_and_cap_with_fake_bytes_only(self):
        data = b"synthetic-vendor-not-real-kit"
        class Response(io.BytesIO):
            def geturl(self):
                return g150.VENDOR_URL
        with patch.object(g150.official, "VENDOR_ZIP_SHA",
                          g150.sha256(data).hexdigest()), \
             patch.object(g150.urllib.request, "build_opener") as op:
            op.return_value.open.return_value.__enter__.return_value = Response(data)
            actual = g150._download_authenticated_kit()
        self.assertEqual(data, actual)
        self.assertEqual(op.call_args.args[0], g150._OfficialHostOnly)

    def test_vendor_mismatch_fails_closed(self):
        class Response(io.BytesIO):
            def geturl(self): return g150.VENDOR_URL
        with patch.object(g150.urllib.request, "build_opener") as op:
            op.return_value.open.return_value.__enter__.return_value = Response(b"wrong")
            with self.assertRaisesRegex(g150.OwnerCheckRefused, "SHA256"):
                g150._download_authenticated_kit()

    def test_official_kit_authenticated_but_no_native_risk_consents_inspect_only(self):
        with patch.object(g150, "verify_owner_pair", return_value=self.pair), \
             patch.object(g150, "_download_authenticated_kit",
                          return_value=b"synthetic authenticated"), \
             patch.object(g150.official, "check",
                          return_value={"official_checker_executed": False}) as check:
            r = g150.run(self.directory, download_official_kit=True)
        self.assertEqual(r["status"], "G147_VENDOR_BYTES_AUTHENTIC_LOCAL_CHECKER_NOT_RUN")
        self.assertFalse(r["official_checker_executed"])
        self.assertEqual(check.call_args.kwargs["mode"], "inspect")
        self.assertEqual(check.call_args.kwargs["candidate_profile"], "g147")

    def test_native_explicit_authorization_only_after_exact_precheck(self):
        vendor_result = {
            "status": "OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE",
            "official_checker_executed": True,
            "result": "OFFICIAL_WARN_OR_FAIL_HOLD",
            "checker_summary": {"errors": 0, "warnings": 1, "info": 0},
            "diagnostic_codes": ["DELEGATION_NEEDS_NAS"],
            "checker_exit_code": 0,
            "checker_stderr_present": False,
        }
        with patch.object(g150, "verify_owner_pair", return_value=self.pair), \
             patch.object(g150, "_download_authenticated_kit",
                          return_value=b"synthetic authenticated"), \
             patch.object(g150.official, "check", return_value=vendor_result) as check:
            r = g150.run(self.directory, download_official_kit=True,
                         execute_official_native_code=True)
        self.assertEqual(r["status"], "G147_OFFICIAL_CHECKER_EXECUTED_OWNER_REVIEW_ONLY")
        self.assertTrue(r["official_checker_executed"])
        self.assertEqual(r["diagnostic_codes"], ["DELEGATION_NEEDS_NAS"])
        self.assertFalse(r["devpost_submitted"])
        self.assertEqual(r["release_gate"], "HOLD")
        self.assertEqual(check.call_args.kwargs["mode"], "native")
        self.assertTrue(check.call_args.kwargs["native_risk_approved"])

    def test_remote_redirect_domain_refused(self):
        from unittest.mock import MagicMock
        req = MagicMock()
        redirect = g150._OfficialHostOnly()
        with self.assertRaises(g150.OwnerCheckRefused):
            redirect.redirect_request(req, None, 302, "redirect", {},
                                      "https://evil.example.com/a")

    def test_wrong_final_download_origin_refused(self):
        class Response(io.BytesIO):
            def geturl(self): return "https://untrusted.example/kit.zip"
        with patch.object(g150.urllib.request, "build_opener") as op:
            op.return_value.open.return_value.__enter__.return_value = Response(b"x")
            with self.assertRaisesRegex(g150.OwnerCheckRefused, "REDIRECT"):
                g150._download_authenticated_kit()

    def test_download_size_cap_rejected_without_network(self):
        class Response(io.BytesIO):
            def geturl(self): return g150.VENDOR_URL
        with patch.object(g150, "VENDOR_MAX", 3), \
             patch.object(g150.urllib.request, "build_opener") as op:
            op.return_value.open.return_value.__enter__.return_value = Response(b"123456")
            with self.assertRaisesRegex(g150.OwnerCheckRefused, "SIZE_LIMIT"):
                g150._download_authenticated_kit()

    def test_cli_refusal_no_private_text_or_path(self):
        class Boom(g150.OwnerCheckRefused): pass
        with patch.object(g150, "run", side_effect=Boom("top secret path")):
            with patch.object(g150, "print") as out:
                rc = g150.main(["--folder", str(self.directory)])
        self.assertEqual(rc, 2)
        self.assertNotIn("top secret", out.call_args.args[0])
        self.assertNotIn(str(self.directory), out.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
