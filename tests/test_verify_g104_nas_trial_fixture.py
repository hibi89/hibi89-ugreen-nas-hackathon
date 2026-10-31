"""G104 exact fixture file-set + SHA guard negative tests."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify_g104_nas_trial_fixture as gate


def archive(members: dict[str, bytes]) -> bytes:
    out = BytesIO()
    with ZipFile(out, "w") as z:
        for name, value in members.items():
            z.writestr(name, value)
    return out.getvalue()


class G104ExactFixtureGuard(unittest.TestCase):
    def setUp(self):
        self.valid = archive({name: b"synthetic data\n" for name in sorted(gate.FILES)})

    def test_exact_byte_fixture_validates_without_nas_claim(self):
        out = gate.verify_archive(self.valid, expected_sha=sha256(self.valid).hexdigest())
        self.assertEqual(out["files"], 8)
        self.assertFalse(out["real_nas_test_executed"])
        self.assertFalse(out["owner_approved_upload"])
        self.assertEqual(out["release_gate"], "HOLD")

    def test_wrong_sha_refused(self):
        with self.assertRaisesRegex(gate.FixtureRefused, "SHA"):
            gate.verify_archive(self.valid)

    def test_missing_file_refused_even_with_new_sha(self):
        x = archive({name: b"X" for name in gate.FILES if not name.endswith("summary.md")})
        with self.assertRaisesRegex(gate.FixtureRefused, "entries"):
            gate.verify_archive(x, expected_sha=sha256(x).hexdigest())

    def test_unapproved_executable_member_refused(self):
        x = archive({**{name: b"X" for name in gate.FILES}, "test.py": b"print('x')"})
        with self.assertRaisesRegex(gate.FixtureRefused, "entries"):
            gate.verify_archive(x, expected_sha=sha256(x).hexdigest())

    def test_cli_missing_path_refuses_without_creating_anything(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(gate.main([str(Path(tmp)/"missing.zip")]), 2)


if __name__ == "__main__":
    unittest.main()
