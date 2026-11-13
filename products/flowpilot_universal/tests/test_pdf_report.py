"""Korean PDF: readable, local create-only, ledger SHA and no source writes."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from flowpilot_universal.engine import InputError
from flowpilot_universal.pdf_report import ensure_pdf_support, render_pdf, create_pdf_only
from flowpilot_universal.session import run_session, verify_history_entry, HISTORY_FILE


class PdfReportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base / "납품 원본"
        self.output = self.base / "검사 증거"
        self.root.mkdir()
        self.output.mkdir()
        (self.root / "계약서.txt").write_bytes(b"original immutable data")
        self.manifest = self.base / "요구.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "title": "한국어 납품 검수",
            "expected_files": [{"path": "계약서.txt"}]
        }, ensure_ascii=False), encoding="utf-8")
        ensure_pdf_support()

    def test_korean_pdf_roundtrip_and_ledger(self):
        result = run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        self.assertEqual(result.status, "READY")
        self.assertTrue(result.pdf_path.is_file())
        doc = PdfReader(result.pdf_path)
        self.assertGreaterEqual(len(doc.pages), 1)
        text = " ".join(page.extract_text() for page in doc.pages)
        self.assertIn("계약서.txt", text)
        self.assertIn("한국어 납품 검수", text)
        self.assertIn("READY", text)
        self.assertEqual(verify_history_entry(self.output, result.session_id)["reports_verified"], 3)
        self.assertEqual((self.root / "계약서.txt").read_bytes(), b"original immutable data")
        with closing(sqlite3.connect(self.output / HISTORY_FILE)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM pdf_evidence").fetchone()[0], 1)

    def test_pdf_tamper_rejected(self):
        result = run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        with result.pdf_path.open("ab") as file:
            file.write(b"\n% altered after evidence created\n")
        with self.assertRaises(InputError):
            verify_history_entry(self.output, result.session_id)

    def test_pdf_missing_rejected(self):
        result = run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        result.pdf_path.unlink()
        with self.assertRaises(InputError):
            verify_history_entry(self.output, result.session_id)

    def test_legacy_json_html_history_preserved(self):
        old = run_session(self.root, self.manifest, self.output, consent=True)
        self.assertIsNone(old.pdf_path)
        self.assertEqual(verify_history_entry(self.output, old.session_id)["reports_verified"], 2)
        newer = run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        self.assertEqual(verify_history_entry(self.output, newer.session_id)["reports_verified"], 3)
        self.assertEqual(verify_history_entry(self.output, old.session_id)["reports_verified"], 2)

    def test_pdf_destination_not_overwritten(self):
        result = run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        data = result.pdf_path.read_bytes()
        with self.assertRaises(InputError):
            create_pdf_only(result.pdf_path, data, self.root)
        self.assertEqual(result.pdf_path.read_bytes(), data)

    def test_pdf_cannot_write_inside_root(self):
        report = {"title": "Test", "status": "READY", "root": str(self.root),
                  "files": [], "issues": [], "files_scanned": 0}
        target = self.root / "inside.pdf"
        with self.assertRaises(InputError):
            create_pdf_only(target, render_pdf(report), self.root)
        self.assertFalse(target.exists())

    def test_multipage_korean_with_html_escaped_text(self):
        report = {"title": "<script>한글 문서</script>",
                  "status": "NEEDS_REVIEW", "root": str(self.root),
                  "files_scanned": 125,
                  "issues": [{"code": "RESUME_CACHE_REVIEW", "path": "."}],
                  "files": [{"path": f"긴_파일명_{i:03d}_사본.txt", "size": i, "sha256": "b"*64}
                            for i in range(125)]}
        target = self.output / "many-pages.pdf"
        create_pdf_only(target, render_pdf(report), self.root)
        doc = PdfReader(target)
        self.assertGreater(len(doc.pages), 1)
        text = "".join(p.extract_text() for p in doc.pages)
        self.assertIn("NEEDS_REVIEW", text)
        self.assertIn("한글 문서", text)
        self.assertIn("<script>한글 문서</script>", text)  # Literal text, not executable ReportLab markup

    def test_missing_pdf_dependency_refuses_before_scan(self):
        with patch("flowpilot_universal.session.ensure_pdf_support", side_effect=InputError("font absent")):
            with self.assertRaises(InputError):
                run_session(self.root, self.manifest, self.output, consent=True, pdf=True)
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
