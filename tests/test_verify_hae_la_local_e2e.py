"""G81 owner-local exact HAE archive gate: negative and no-execution cases."""
from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_hae_la_local_e2e import AcceptanceRefused, validate_binary, run_acceptance

BYTES = b"not a Python archive" * 100


class OwnerLocalAcceptTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "hae-integrated.pyz"
        self.path.write_bytes(BYTES)
        self.digest = sha256(BYTES).hexdigest()

    def test_no_execution_consent_refuses_even_matching_archive(self):
        with self.assertRaisesRegex(AcceptanceRefused, "approval"):
            validate_binary(self.path, self.digest, False)
        self.assertEqual(self.path.read_bytes(), BYTES)

    def test_wrong_sha_refuses_without_mutation(self):
        with self.assertRaisesRegex(AcceptanceRefused, "does not match"):
            validate_binary(self.path, "0"*64, True)
        self.assertEqual(self.path.read_bytes(), BYTES)

    def test_invalid_pin_format_refused(self):
        for sha in ("", "123", "ABC"*21+"a", "z"*64):
            with self.subTest(sha=sha), self.assertRaises(AcceptanceRefused):
                validate_binary(self.path, sha, True)

    def test_wrong_extension_refused(self):
        other = self.path.with_suffix(".zip")
        other.write_bytes(BYTES)
        with self.assertRaisesRegex(AcceptanceRefused, ".pyz"):
            validate_binary(other, self.digest, True)

    def test_symlink_archive_refused(self):
        link = self.path.parent / "pointer.pyz"
        try:
            link.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink unavailable on this runner")
        with self.assertRaisesRegex(AcceptanceRefused, "regular"):
            validate_binary(link, self.digest, True)

    def test_matching_file_verified_only_not_executed(self):
        actual, digest = validate_binary(self.path, self.digest, True)
        self.assertEqual(digest, self.digest)
        self.assertEqual(actual, self.path.resolve())
        self.assertEqual(self.path.read_bytes(), BYTES)

    def test_nonexistent_bundle_refused(self):
        with self.assertRaisesRegex(AcceptanceRefused, "regular"):
            validate_binary(self.path.parent / "missing.pyz", self.digest, True)


if __name__ == "__main__":
    unittest.main()
