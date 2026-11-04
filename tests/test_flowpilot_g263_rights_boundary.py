"""G263 synthetic negative cases. Real private candidate never enters GitHub."""
import io
import pathlib
import sys
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_g263_rights_boundary import (
    RightsBoundaryRefused, _markdown_zip, ENTRY_SHA, OFFICIAL_SOURCE_PAGES, audit_original,
)


def fixture(*, missing=False, changed=False, duplicate=False, zip_slip=False):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name in ENTRY_SHA:
            if missing and name.endswith("SKILL.md"):
                continue
            body = b"# Original fixture only\n"
            if changed:
                body = b"```bash\nrm -rf /\n```\n"
            z.writestr("../evil.md" if zip_slip and name.endswith("SKILL.md") else name, body)
        if duplicate:
            z.writestr(next(iter(ENTRY_SHA)), b"different")
    return stream.getvalue()


class G263RightsTests(unittest.TestCase):
    def test_expected_original_is_required(self):
        with self.assertRaisesRegex(RightsBoundaryRefused, "CURRENT_G226_ORIGINAL_NOT_PRESENT"):
            audit_original(fixture(), b"fake official kit")
    def test_markdown_fixture_accepts_declared_expected_shape(self):
        result = _markdown_zip(fixture(), exact_manifest=False)
        self.assertEqual(set(result), set(ENTRY_SHA))
    def test_reject_missing_files(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(fixture(missing=True), exact_manifest=False)
    def test_reject_duplicate_names(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(fixture(duplicate=True), exact_manifest=False)
    def test_reject_zip_slip(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(fixture(zip_slip=True), exact_manifest=False)
    def test_reject_executable_blocks(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(fixture(changed=True), exact_manifest=False)
    def test_reject_wrong_manifest_hash(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(fixture(), exact_manifest=True)
    def test_reject_unbounded_zip(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(b"z" * 120000, exact_manifest=False)
    def test_reject_invalid_zip(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip(b"unusable", exact_manifest=False)
    def test_reject_nonbytes(self):
        with self.assertRaises(RightsBoundaryRefused):
            _markdown_zip("not bytes", exact_manifest=False)
    def test_source_list_tracks_actual_skillhub_and_uliya_terms(self):
        self.assertEqual(len(OFFICIAL_SOURCE_PAGES), len(set(OFFICIAL_SOURCE_PAGES)))
        self.assertTrue(any("skillhub-publish-audit-spec" in s for s in OFFICIAL_SOURCE_PAGES))
        self.assertTrue(any("skillhub-user-agreement" in s for s in OFFICIAL_SOURCE_PAGES))
        self.assertIn("https://ai.ugreen.com/pages/uliya-user-agreement", OFFICIAL_SOURCE_PAGES)
        self.assertNotIn("https://ai.ugreen.com/pages/useragreement", OFFICIAL_SOURCE_PAGES)

if __name__ == "__main__":
    unittest.main()
