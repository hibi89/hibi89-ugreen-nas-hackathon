"""Offline-only Round 1 candidate ZIP; real PDF is verified by dedicated CI."""
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from round1_candidate_bundle import draft_bundle,sha256,validate_candidate_zip,validate_pdf
from round1_package_audit import PackageError


class CandidateBundleTests(unittest.TestCase):
    def setUp(self):
        self.skill=ROOT/"skill/projectready-nas"
    def test_official_current_skill_4_markdown_files(self):
        archive, manifest=draft_bundle(self.skill)
        self.assertEqual(manifest["zip_member_count"],4)
        self.assertTrue(manifest["zip_contains_markdown_only"])
        self.assertEqual(manifest["sha256_zip"],sha256(archive))
        self.assertEqual(manifest["official_uliya_checker"],"NOT_RUN")
        self.assertEqual(manifest["devpost_submission"],"NOT_SUBMITTED")
        self.assertEqual(manifest["proposal_answer_words"],351)
        self.assertIsNone(manifest["pdf"])
    def test_reproducible_binary(self):
        a,_=draft_bundle(self.skill)
        b,_=draft_bundle(self.skill)
        self.assertEqual(a,b)
    def test_reject_member_swap(self):
        archive,_=draft_bundle(self.skill)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            files={n:z.read(n) for n in z.namelist()}
        first=next(iter(files))
        files[first]=b"replacement"
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,"w") as z:
            for n,c in files.items():z.writestr(n,c)
        with self.assertRaises(ValueError):
            validate_candidate_zip(self.skill,buff.getvalue())
    def test_refuses_extra_archive_member(self):
        archive,_=draft_bundle(self.skill)
        buff=io.BytesIO(archive)
        with zipfile.ZipFile(buff,"a") as z:
            z.writestr("projectready-nas/private.json","sensitive")
        with self.assertRaises(ValueError):
            validate_candidate_zip(self.skill,buff.getvalue())
    def test_reject_pdf_without_real_parsing(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.pdf"
            path.write_bytes(b"%PDF-1.4\n%%EOF")
            with self.assertRaises((ValueError,RuntimeError)):
                validate_pdf(path,[{"prompt":"hi","number":1,"answer":"hello"}])
    def test_candidate_not_equal_submit_or_nas_validated(self):
        _,m=draft_bundle(self.skill)
        self.assertEqual(m["entrant_approval"],"PENDING")
        self.assertEqual(m["live_nas_validation"],"NOT_RUN")
        self.assertEqual(m["license_and_dataflow_review"],"NOT_CLEARED")


if __name__=="__main__":
    unittest.main()
