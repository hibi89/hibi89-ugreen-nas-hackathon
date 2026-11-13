"""First-party offline manifest checklist editor: synthetic unit/security tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from flowpilot_universal.engine import InputError, load_manifest, scan
from flowpilot_universal.manifest_editor import (
    create_approved_manifest, parse_checklist, render_manifest,
)


class ManifestEditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "자료 원본"
        self.out = self.base / "요구사항"
        self.root.mkdir()
        self.out.mkdir()
        (self.root / "계약서 final.txt").write_bytes(b"approved original")

    def test_approved_korean_schema_reads_and_scans(self):
        digest = hashlib.sha256(b"approved original").hexdigest()
        path = self.out / "계약 검수.json"
        create_approved_manifest("고객 승인 납품 목록",
                                 f"계약서 final.txt\t{digest}\n",
                                 path, self.root, approved=True)
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema_version"], 1)
        self.assertEqual(raw["expected_files"][0]["sha256"], digest)
        parsed = load_manifest(path)
        self.assertEqual(scan(self.root, parsed)["status"], "READY")
        self.assertEqual((self.root / "계약서 final.txt").read_bytes(), b"approved original")

    def test_parsed_comments_and_optional_sha(self):
        rows = parse_checklist("# vendor list\n\nfolder/자료.pdf\nREADME.md\t" + "AB"*32 + "\n")
        self.assertEqual(rows[0], {"path": "folder/자료.pdf", "sha256": None})
        self.assertEqual(rows[1]["sha256"], "ab"*32)

    def test_consent_explicit_no_file_created(self):
        path = self.out / "manifest.json"
        with self.assertRaises(InputError):
            create_approved_manifest("Title", "readme.md", path, self.root)
        self.assertFalse(path.exists())
        with self.assertRaises(InputError):
            render_manifest("Title", "readme.md", approved=False)

    def test_reject_duplicate_and_case_collision(self):
        for text in ("Readme.txt\nreadme.TXT\n", "a/b.txt\na/b.txt\n"):
            with self.subTest(text=text), self.assertRaises(InputError):
                parse_checklist(text)

    def test_reject_unsafe_paths(self):
        for name in ("../outside", "a/../outside", "/absolute", r"..\outside",
                     "CON", "COM1.txt", "bad?.txt", "foo:bar", "folder//a.txt",
                     "file.txt ", "x\n../outside"):
            with self.subTest(name=name), self.assertRaises(InputError):
                parse_checklist(name)

    def test_reject_invalid_hash_extra_tabs_and_input_limit(self):
        for text in ("a.txt\twrong\n", "a.txt\t" + "g"*64,
                     "a.txt\t" + "a"*64 + "\tmore", "a.txt\n" * 90_000):
            with self.subTest(n=len(text)), self.assertRaises(InputError):
                parse_checklist(text)

    def test_reject_empty_manifest_title(self):
        for title in ("", "   ", "a"*161):
            with self.subTest(title=title), self.assertRaises(InputError):
                render_manifest(title, "README.md", approved=True)

    def test_never_overwrite_existing_manifest(self):
        target = self.out / "manifest.json"
        target.write_bytes(b"valuable original")
        with self.assertRaises(InputError):
            create_approved_manifest("Docs", "README.md", target, self.root, approved=True)
        self.assertEqual(target.read_bytes(), b"valuable original")

    def test_refuse_create_inside_scanned_root(self):
        target = self.root / "requirements.json"
        with self.assertRaises(InputError):
            create_approved_manifest("Docs", "README.md", target, self.root, approved=True)
        self.assertFalse(target.exists())

    def test_refuse_json_outside_extension(self):
        target = self.out / "requirements.txt"
        with self.assertRaises(InputError):
            create_approved_manifest("Docs", "README.md", target, self.root, approved=True)
        self.assertFalse(target.exists())

    def test_refuse_symlink_destination(self):
        target = self.out / "requirements.json"
        external = self.base / "important"
        external.write_bytes(b"do not modify")
        try:
            target.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(InputError):
            create_approved_manifest("Docs", "README.md", target, self.root, approved=True)
        self.assertEqual(external.read_bytes(), b"do not modify")

    def test_refuse_source_folder_link(self):
        linked = self.base / "symlink-source"
        try:
            linked.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(InputError):
            create_approved_manifest("Docs", "README.md", self.out / "manifest.json",
                                     linked, approved=True)


if __name__ == "__main__":
    unittest.main()
