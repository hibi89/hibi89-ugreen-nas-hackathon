"""G85 UGREEN main-repo invocation contract tests (private engine replaced by fixture)."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import run_g85_native_backend as entry


class G85PublicEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="g85-entry-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.ugreen = self.base / "public"
        self.ugreen.mkdir()
        self.hae = self.base / "private-hae"
        (self.hae / "tools").mkdir(parents=True)
        self.la = self.base / "private-la"
        (self.la / "lightning_azent").mkdir(parents=True)
        (self.la / "lightning_azent" / "__init__.py").write_text("", encoding="utf-8")
        self.runner = self.hae / "tools" / "g84_verify_ugreen_native.py"
        self.patcher = patch.object(entry, "UGREEN_ROOT", self.ugreen)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def write_runner(self, status: str, code: int = 0):
        self.runner.write_text(
            "import json, sys\n"
            f"print(json.dumps({{'status': {status!r}, 'sqlite_business_rows': 2}}))\n"
            f"sys.exit({code})\n", encoding="utf-8"
        )

    def test_unapproved_does_not_run_private_script(self):
        report = entry.run_native(self.hae, self.la, False)
        self.assertEqual(report["status"], "G85_CONSENT_REQUIRED")
        self.assertFalse(report["native_verified"])

    def test_missing_source_is_blocked(self):
        report = entry.run_native(self.hae, self.la, True)
        self.assertEqual(report["status"], "G85_PRIVATE_SOURCE_MISSING")
        self.assertFalse(report["native_verified"])

    def test_private_acceptance_is_forwarded_as_evidence_not_nas(self):
        self.write_runner(entry.PASS)
        report = entry.run_native(self.hae, self.la, True)
        self.assertEqual(report["status"], "G85_UGREEN_NATIVE_BACKEND_E2E_PASS")
        self.assertEqual(report["backend_receipt"]["sqlite_business_rows"], 2)
        self.assertTrue(report["native_verified"])
        self.assertFalse(report["real_nas_verified"])

    def test_nonzero_exit_cannot_be_certified(self):
        self.write_runner(entry.PASS, code=2)
        report = entry.run_native(self.hae, self.la, True)
        self.assertEqual(report["status"], "G85_NATIVE_BACKEND_NOT_VERIFIED")
        self.assertFalse(report["native_verified"])

    def test_wrong_status_cannot_be_certified(self):
        self.write_runner("G84_NATIVE_E2E_NOT_VERIFIED")
        report = entry.run_native(self.hae, self.la, True)
        self.assertEqual(report["status"], "G85_NATIVE_BACKEND_NOT_VERIFIED")

    def test_invalid_json_is_fail_closed(self):
        self.runner.write_text("print('not-json')\n", encoding="utf-8")
        report = entry.run_native(self.hae, self.la, True)
        self.assertEqual(report["status"], "G85_NATIVE_BACKEND_NOT_VERIFIED")
        self.assertEqual(report["error_type"], "JSONDecodeError")


if __name__ == "__main__":
    unittest.main()
