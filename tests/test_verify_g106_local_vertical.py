"""G106 tests: actual tempfile files + actual OS lstat, never Uliya/NAS."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE / "src"))
import verify_g104_nas_trial_fixture as verify
import verify_g106_local_vertical as v


def fixture_zip(*, symlink=False):
    out = BytesIO()
    with ZipFile(out, "w") as z:
        for name in sorted(verify.FILES):
            info = ZipInfo(name)
            info.create_system = 3
            info.external_attr = ((0o120777 if symlink and name.endswith("/handoff/summary.md")
                                   else 0o100644) << 16)
            z.writestr(info, b"synthetic only; no actual user data\n")
    return out.getvalue()


class G106LocalRealOS(unittest.TestCase):
    def setUp(self):
        self.raw = fixture_zip()
        p = patch.object(verify, "PIN", sha256(self.raw).hexdigest())
        p.start()
        self.addCleanup(p.stop)

    def test_all_four_modes_physically_lstat_synthetic_files(self):
        got = v.run_exact_fixture(self.raw)
        self.assertEqual(got["status"], "G106_REAL_LOCAL_OS_METADATA_VERTICAL_PASS_NOT_NAS")
        self.assertEqual(got["extracted_nonrestricted_files_only"], 5)
        self.assertEqual(got["modes"]["CHECK_REQUIRED"]["items"]["handoff/signoff.md"], "MISSING")
        self.assertEqual(got["modes"]["REVIEW_VERSIONS"]["items"]["handoff/review-v1.md"], "VERSION_REVIEW")
        self.assertEqual(got["modes"]["HANDOFF_AUDIT"]["status"], "BLOCKED")
        self.assertNotIn("document", got["modes"]["SUMMARIZE_SELECTED"]["planned_steps_not_executed"])
        self.assertFalse(got["document_content_read_by_agent"])
        self.assertFalse(got["real_nas_test_executed"])

    def test_partial_scan_never_claims_missing(self):
        got = v.run_exact_fixture(self.raw)["modes"]["PARTIAL_SCAN_NEGATIVE"]
        self.assertEqual(got["status"], "NEEDS_REVIEW")
        self.assertEqual(set(got["items"].values()), {"NOT_CHECKED"})

    def test_changed_input_sha_fails_before_extraction(self):
        with self.assertRaises(verify.FixtureRefused):
            v.run_exact_fixture(self.raw + b"tampered")

    def test_symlink_in_allowlisted_member_refused(self):
        bad = fixture_zip(symlink=True)
        with patch.object(verify, "PIN", sha256(bad).hexdigest()):
            with self.assertRaises(v.LocalVerticalRefused):
                v.run_exact_fixture(bad)

    def test_empty_and_nonzip_inputs_fail(self):
        for blob in (b"", b"PK\x03\x04"):
            with self.subTest(blob=blob), self.assertRaises((ValueError, RuntimeError)):
                v.run_exact_fixture(blob)

    def test_restricted_file_and_overdeep_not_probed(self):
        got = v.run_exact_fixture(self.raw)
        self.assertNotIn(".env", got["physically_probed_relative_paths"])
        self.assertNotIn("deep/level2/level3/beyond_depth.md",
                         got["physically_probed_relative_paths"])


if __name__ == "__main__":
    unittest.main()
