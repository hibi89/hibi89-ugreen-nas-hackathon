"""Offline unsigned Windows folder archive verification with synthetic fake EXE only."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from verify_delivery_archive import build_candidate, extract_verified, verify_candidate


class ArchiveCandidateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / "FlowPilotUniversal"
        self.source.mkdir()
        (self.source / "FlowPilotUniversal.exe").write_bytes(b"synthetic-executable-only")
        sub = self.source / "_internal"
        sub.mkdir()
        (sub / "python311.dll").write_bytes(b"fake-package-runtime")
        self.target = self.base / "candidate.zip"

    def test_build_verify_relocate_preserves_exact_bundle(self):
        digest = build_candidate(self.source, self.target)
        self.assertEqual(digest, verify_candidate(self.target))
        extracted = extract_verified(self.target, self.base / "relocated")
        self.assertEqual((extracted / "FlowPilotUniversal.exe").read_bytes(),
                         b"synthetic-executable-only")
        self.assertEqual((extracted / "_internal" / "python311.dll").read_bytes(),
                         b"fake-package-runtime")
        self.assertEqual((self.source / "FlowPilotUniversal.exe").read_bytes(),
                         b"synthetic-executable-only")

    def test_no_overwrite_and_no_existing_extraction(self):
        build_candidate(self.source, self.target)
        original = self.target.read_bytes()
        with self.assertRaises(ValueError):
            build_candidate(self.source, self.target)
        self.assertEqual(self.target.read_bytes(), original)
        output = self.base / "relocated"
        output.mkdir()
        with self.assertRaises(ValueError):
            extract_verified(self.target, output)

    def test_source_change_detected_during_verification(self):
        build_candidate(self.source, self.target)
        forged = self.base / "tamper.zip"
        with zipfile.ZipFile(self.target) as source, zipfile.ZipFile(forged, "w") as dest:
            for name in source.namelist():
                raw = source.read(name)
                if name.endswith("python311.dll"):
                    raw += b"mutation"
                dest.writestr(name, raw)
        with self.assertRaises(ValueError):
            verify_candidate(forged)

    def test_path_traversal_rejected_without_extract(self):
        forged = self.base / "bad.zip"
        with zipfile.ZipFile(forged, "w") as dest:
            dest.writestr("../outside.exe", b"attack")
            dest.writestr("FLOWPILOT_CANDIDATE_SHA256.json", "{}")
        with self.assertRaises(ValueError):
            verify_candidate(forged)
        self.assertFalse((self.base / "outside.exe").exists())

    def test_missing_executable_rejected(self):
        (self.source / "FlowPilotUniversal.exe").unlink()
        with self.assertRaises(ValueError):
            build_candidate(self.source, self.target)

    def test_symlinked_source_rejected(self):
        outside = self.base / "secret.dat"
        outside.write_bytes(b"secret")
        try:
            (self.source / "secret.dat").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            build_candidate(self.source, self.target)
        self.assertEqual(outside.read_bytes(), b"secret")

    def test_archive_inside_exe_folder_refused(self):
        with self.assertRaises(ValueError):
            build_candidate(self.source, self.source / "candidate.zip")

    def test_malformed_zip_rejected(self):
        self.target.write_bytes(b"not a zip")
        with self.assertRaises(zipfile.BadZipFile):
            verify_candidate(self.target)


if __name__ == "__main__":
    unittest.main()
