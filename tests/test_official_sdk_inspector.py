"""Offline tests for ZIP metadata-only inspector; no network or NAS."""
import importlib.util
import io
import sys
import unittest
import zipfile
from pathlib import Path

INSPECT = Path(__file__).resolve().parents[1] / "tools" / "inspect_official_sdk.py"
spec = importlib.util.spec_from_file_location("official_sdk_inspector", INSPECT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def make_zip(contents):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, data in contents.items():
            archive.writestr(path, data)
    return buffer.getvalue()

class SDKInspectTests(unittest.TestCase):
    def test_counts_metadata_without_dumping_content(self):
        binary=make_zip({"uliya-skill-kit/SKILL.md":"PRIVATE-DONT-LOG-THIS", "uliya-skill-kit/docs/cli-reference.md":"CLI-SECRET", "uliya-skill-kit/LICENSE.md":"test"})
        report=module.inspect_zip_bytes(binary)
        self.assertEqual(report["file_count"],3)
        self.assertTrue(report["license_filename_present"])
        self.assertTrue(report["documentation_filename_keywords_present"]["cli"])
        self.assertNotIn("PRIVATE-DONT-LOG",str(report))
        self.assertFalse(report["cli_signatures_verified"])
    def test_rejects_traversal(self):
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(make_zip({"../secret.txt":"x"}))
    def test_rejects_backslash(self):
        # ZipFile.writestr() normalizes backslashes on Windows. Replace the
        # two raw ZIP filename occurrences to preserve an unsafe fixture.
        raw = make_zip({"a/b": "x"})
        self.assertEqual(raw.count(b"a/b"), 2)
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(raw.replace(b"a/b", b"a\\b"))

    def test_rejects_central_local_name_mismatch(self):
        raw = make_zip({"a/b": "x"})
        central = raw.index(b"PK\x01\x02")
        tampered = raw[:central] + raw[central:].replace(
            b"a/b", b"a\\b", 1
        )
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(tampered)

    def test_rejects_absolute(self):
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(make_zip({"/etc/key":"x"}))
    def test_bad_zip_rejected(self):
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(b"not ZIP")
    def test_empty_zip_binary_rejected(self):
        with self.assertRaises(module.UnsafePackage):
            module.inspect_zip_bytes(b"")
    def test_rejects_large_member(self):
        original=module.MAX_FILE
        module.MAX_FILE=3
        try:
            with self.assertRaises(module.UnsafePackage):
                module.inspect_zip_bytes(make_zip({"x.md":"1234"}))
        finally:
            module.MAX_FILE=original

if __name__=="__main__":
    unittest.main()
