"""P85 adversarial local-only scanner input and bounded-read checks."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowpilot_universal import engine
from flowpilot_universal.engine import InputError, load_manifest, scan


class SecurityRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "인가된 납품"
        self.root.mkdir()
        self.manifest = self.base / "requirements.json"
        (self.root / "납품.txt").write_bytes(b"abc")
        self.manifest.write_text(
            json.dumps({"schema_version": 1, "expected_files": [{"path": "납품.txt"}]}),
            encoding="utf-8"
        )

    def test_json_duplicate_keys_rejected(self):
        self.manifest.write_text(
            '{"schema_version":1,"schema_version":1,"expected_files":[{"path":"납품.txt"}]}',
            encoding="utf-8")
        with self.assertRaises(InputError):
            load_manifest(self.manifest)

    def test_duplicate_nested_key_rejected(self):
        self.manifest.write_text(
            '{"schema_version":1,"expected_files":[{"path":"납품.txt","path":"evil"}]}',
            encoding="utf-8")
        with self.assertRaises(InputError):
            load_manifest(self.manifest)

    def test_manifest_oversized_refused(self):
        self.manifest.write_bytes(b" " * (engine.MANIFEST_LIMIT + 1))
        with self.assertRaises(InputError):
            load_manifest(self.manifest)

    def test_nonportable_paths_refused(self):
        bad = ["CON", "nul.txt", "COM1/a.txt", "a<bad", "a*b", "a?b", "a|b",
               "x\\ny", "LPT9/report", "foo>.txt"]
        for name in bad:
            with self.subTest(name=name):
                self.manifest.write_text(json.dumps({
                    "schema_version": 1, "expected_files": [{"path": name}]
                }), encoding="utf-8")
                with self.assertRaises(InputError):
                    load_manifest(self.manifest)

    def test_manifest_symlink_rejected(self):
        symlink = self.base / "pointer.json"
        try:
            symlink.symlink_to(self.manifest)
        except (OSError, NotImplementedError):
            self.skipTest("test runner cannot create symlinks")
        with self.assertRaises(InputError):
            load_manifest(symlink)

    def test_manifest_replaced_on_open_rejected(self):
        original = engine.os.open
        def swapped(path, flags, *args, **kwargs):
            if Path(path) == self.manifest:
                self.manifest.write_bytes(b"changed")
            return original(path, flags, *args, **kwargs)
        with patch("flowpilot_universal.engine.os.open", side_effect=swapped):
            with self.assertRaises(InputError):
                load_manifest(self.manifest)

    def test_file_grow_while_hashing_is_incomplete(self):
        manifest = load_manifest(self.manifest)
        old_open = engine.os.open
        def mutate(path, flags, *args, **kwargs):
            fd = old_open(path, flags, *args, **kwargs)
            if Path(path).name == "납품.txt":
                (self.root / "납품.txt").write_bytes(b"abcd")
            return fd
        with patch("flowpilot_universal.engine.os.open", side_effect=mutate):
            result = scan(self.root, manifest)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("FILE_UNREADABLE_OR_CHANGED", {r["code"] for r in result["issues"]})

    def test_empty_file_digest_and_ready(self):
        (self.root / "납품.txt").write_bytes(b"")
        manifest = load_manifest(self.manifest)
        result = scan(self.root, manifest)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["files"][0]["size"], 0)


if __name__ == "__main__":
    unittest.main()
