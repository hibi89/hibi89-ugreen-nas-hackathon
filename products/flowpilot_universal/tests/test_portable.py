"""P85 portable product and negative-security tests; temporary synthetic data only."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from flowpilot_universal.engine import InputError
from flowpilot_universal.portable import build_archive, verify_archive, MANIFEST


SOURCE = Path(__file__).resolve().parents[1]


class PortableTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.output = self.base / "납품 후보.pyz"

    def test_source_archive_build_and_cli_execute(self):
        pyz, digest = build_archive(SOURCE, self.output)
        self.assertEqual(digest, hashlib.sha256(pyz.read_bytes()).hexdigest())
        self.assertEqual(verify_archive(pyz), digest)
        self.assertEqual((self.base / (pyz.name + ".sha256")).read_text(encoding="utf-8"),
                         f"{digest}  {pyz.name}\n")
        help_result = subprocess.run([sys.executable, str(pyz), "--help"],
                                     capture_output=True, text=True, timeout=15)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--manifest", help_result.stdout)

    def test_archive_reproducible_bytes(self):
        first, digest1 = build_archive(SOURCE, self.output)
        second, digest2 = build_archive(SOURCE, self.base / "again.pyz")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(digest1, digest2)

    def test_refuse_overwrite_source_and_symlink(self):
        build_archive(SOURCE, self.output)
        with self.assertRaises(InputError):
            build_archive(SOURCE, self.output)
        with self.assertRaises(InputError):
            build_archive(SOURCE, SOURCE / "secret.pyz")
        self.assertFalse((SOURCE / "secret.pyz").exists())
        link = self.base / "pointer.pyz"
        try:
            link.symlink_to(self.output)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(InputError):
            build_archive(SOURCE, link)

    def test_modified_code_hash_is_rejected(self):
        build_archive(SOURCE, self.output)
        poisoned = self.base / "poison.pyz"
        with ZipFile(self.output) as source, ZipFile(poisoned, "w") as target:
            for name in source.namelist():
                payload = source.read(name)
                if name.endswith("engine.py"):
                    payload += b"\n# unexpected mutation\n"
                target.writestr(name, payload)
        with self.assertRaises(InputError):
            verify_archive(poisoned)

    def test_manifest_change_is_rejected(self):
        build_archive(SOURCE, self.output)
        poisoned = self.base / "tamper.pyz"
        with ZipFile(self.output) as source, ZipFile(poisoned, "w") as target:
            for name in source.namelist():
                payload = source.read(name)
                if name == MANIFEST:
                    metadata = json.loads(payload)
                    metadata["release_approved"] = True
                    payload = json.dumps(metadata).encode()
                target.writestr(name, payload)
        with self.assertRaises(InputError):
            verify_archive(poisoned)

    def test_zip_traversal_and_duplicate_rejected(self):
        outside = self.base / "evil.pyz"
        with ZipFile(outside, "w") as zf:
            zf.writestr("../evil.py", "print('bad')")
        with self.assertRaises(InputError):
            verify_archive(outside)
        with ZipFile(outside, "w") as zf:
            zf.writestr("a", "A")
            # Duplicate ZIP member with same name is intentionally malicious.
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                zf.writestr("a", "B")
        with self.assertRaises(InputError):
            verify_archive(outside)

    def test_damaged_zip_rejected(self):
        self.output.write_bytes(b"NOT A ZIP")
        with self.assertRaises(InputError):
            verify_archive(self.output)

    def test_portable_end_to_end_readonly_scan(self):
        pyz, _ = build_archive(SOURCE, self.output)
        source = self.base / "업무 원본"
        report = self.base / "보고서"
        source.mkdir()
        report.mkdir()
        data = b"offline-delivery"
        (source / "ok.bin").write_bytes(data)
        manifest = self.base / "requirements.json"
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "expected_files": [{
                "path": "ok.bin",
                "sha256": hashlib.sha256(data).hexdigest()
            }]
        }), encoding="utf-8")
        target = report / "result.json"
        cp = subprocess.run(
            [sys.executable, str(pyz), "--root", str(source), "--manifest",
             str(manifest), "--json", str(target)],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["status"], "READY")
        self.assertEqual((source / "ok.bin").read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
