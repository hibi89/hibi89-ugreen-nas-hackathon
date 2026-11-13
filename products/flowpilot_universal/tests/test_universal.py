"""Offline-only synthetic regression; never use customer data or real NAS."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flowpilot_universal.__main__ import main
from flowpilot_universal.engine import InputError, create_only, load_manifest, render_html, scan

class UniversalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "납품 자료"
        self.root.mkdir()
        self.out = self.base / "reports"
        self.out.mkdir()
        self.manifest = self.base / "requirements.json"
    def config(self, names, **extra):
        self.manifest.write_text(json.dumps({"schema_version": 1,
            "expected_files": [{"path": n} for n in names], **extra}), encoding="utf-8")
        return load_manifest(self.manifest)
    def test_ready_and_original_bytes(self):
        f = self.root / "계약서.txt"
        f.write_bytes(b"contract 123")
        original = f.read_bytes()
        report = scan(self.root, self.config([f.name]))
        self.assertEqual(report["status"], "READY")
        self.assertEqual(f.read_bytes(), original)
        self.assertEqual(report["files"][0]["sha256"], hashlib.sha256(original).hexdigest())
    def test_missing(self):
        self.assertEqual(scan(self.root, self.config(["missing.mp4"]))["status"], "BLOCKED")
    def test_bad_hash(self):
        (self.root / "a").write_bytes(b"a")
        conf = self.config(["a"])
        conf["expected_files"][0]["sha256"] = "f"*64
        self.assertEqual(scan(self.root, conf)["status"], "BLOCKED")
    def test_duplicate(self):
        (self.root / "a.txt").write_bytes(b"same")
        (self.root / "b.txt").write_bytes(b"same")
        r = scan(self.root, self.config(["a.txt"]))
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertIn("DUPLICATE_CONTENT_REVIEW", [i["code"] for i in r["issues"]])
    def test_versions(self):
        (self.root / "project-v1.txt").write_bytes(b"one")
        (self.root / "project-v2.txt").write_bytes(b"two")
        r = scan(self.root, self.config(["project-v1.txt", "project-v2.txt"]))
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertIn("VERSION_CANDIDATES_REVIEW", [i["code"] for i in r["issues"]])
    def test_case_collision(self):
        (self.root / "A.txt").write_bytes(b"1")
        (self.root / "a.TXT").write_bytes(b"2")
        # Case-colliding files exist on Linux; Windows is inherently case-insensitive.
        if len(list(self.root.iterdir())) == 2:
            self.assertEqual(scan(self.root, self.config(["A.txt"]))["status"], "INCOMPLETE")
    def test_symlink(self):
        (self.root / "a.txt").write_bytes(b"one")
        try:
            (self.root / "escape").symlink_to(self.manifest)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        self.assertEqual(scan(self.root, self.config(["a.txt"]))["status"], "INCOMPLETE")
    def test_symlink_directory(self):
        external = self.base / "external"
        external.mkdir()
        (external / "secret").write_bytes(b"private")
        try:
            (self.root / "linkdir").symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        r = scan(self.root, self.config(["public.txt"]))
        self.assertEqual(r["files_scanned"], 0)
        self.assertEqual(r["status"], "INCOMPLETE")
    def test_traversal_invalid(self):
        for name in ("../secret", "/etc/passwd", "C:\\x", "a/./b", "a//b", "foo:bar", "file. "):
            with self.subTest(name=name), self.assertRaises(InputError):
                self.config([name])
        with self.assertRaises(InputError):
            self.config(["Readme.TXT", "README.txt"])
    def test_limits(self):
        (self.root / "a").write_bytes(b"123")
        (self.root / "b").write_bytes(b"456")
        cfg = self.config(["a"], limits={"max_files": 1, "max_bytes": 2})
        self.assertEqual(scan(self.root, cfg)["status"], "INCOMPLETE")
    def test_unreadable(self):
        (self.root / "a").write_bytes(b"one")
        cfg = self.config(["a"])
        with patch("flowpilot_universal.engine._hash_file", side_effect=OSError("simulated")):
            self.assertEqual(scan(self.root, cfg)["status"], "INCOMPLETE")
    def test_manifest_contract(self):
        with self.assertRaises(InputError):
            self.config(["a"], unexpected=True)
        with self.assertRaises(InputError):
            self.config(["a"], limits={"max_files": 0})
        with self.assertRaises(InputError):
            self.config(["a"], title=42)
    def test_html_escaped(self):
        (self.root / "<script>.txt").write_bytes(b"x")
        r = scan(self.root, self.config(["<script>.txt"], title="<img src=x>"))
        page = render_html(r)
        self.assertNotIn("<script>.txt", page)
        self.assertNotIn("<img src=x>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("default-src 'none'", page)
    def test_create_only(self):
        r = scan(self.root, self.config(["x"]))
        target = self.out / "first.json"
        create_only(target, json.dumps(r), self.root)
        self.assertTrue(target.is_file())
        with self.assertRaises(InputError):
            create_only(target, "overwrite", self.root)
        with self.assertRaises(InputError):
            create_only(self.root / "inside.json", "secret", self.root)
    def test_cli_exit_codes(self):
        (self.root / "found").write_bytes(b"x")
        self.config(["found"])
        p, h = self.out / "a.json", self.out / "a.html"
        args = ["--root", str(self.root), "--manifest", str(self.manifest)]
        self.assertEqual(main(args + ["--json", str(p), "--html", str(h)]), 0)
        self.assertEqual(main(args + ["--json", str(p)]), 2)
        self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["status"], "READY")
        self.config(["missing"])
        self.assertEqual(main(args + ["--json", str(self.out / "b.json")]), 2)

if __name__ == "__main__":
    unittest.main()
