"""G76: exported detached PDF may not silently differ from GitHub CI archive.

All passing fixtures are synthetic and parameterized; only pinned hashes
from exact G75 owner-review CI are accepted in the actual CLI.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import stat
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile
from contextlib import redirect_stdout

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from flowpilot3_export_integrity import (
    PDF, ZIP, MANIFEST, PREVIEW, AUDIT, SOURCE_MEMBER,
    IntegrityError, main, verify_archive,
)


def hash_of(value):
    return sha256(value).hexdigest()


def archive(files):
    result = BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for k, v in files.items():
            target.writestr(k, v)
    return result.getvalue()


def example():
    pdf = b"%PDF-1.4\nSynthetic PDF data\n%%EOF"
    skill = b"---\nname: flowpilot-nas\ndescription: synthetic only\n---\n"
    inner = archive({SOURCE_MEMBER: skill})
    png = b"\x89PNG\r\n\x1a\nexample preview"
    qa = b"synthetic-question-source"
    manifest = {
        "status": "OWNER_REVIEW_NOT_SUBMITTED",
        "source_skill_sha256": hash_of(skill), "qa_sha256": hash_of(qa),
        "pdf_sha256": hash_of(pdf), "zip_sha256": hash_of(inner),
        "pdf_bytes": len(pdf), "zip_bytes": len(inner),
        "zip_unpacked_bytes": len(skill), "pdf_pages": 1, "questions": 10,
        "substantive_english_words": 360, "skill_members": [SOURCE_MEMBER],
        "source_exact_match": True, "official_checker": "PINNED_STATIC_PASS_ONLY",
        "official_creator": "NOT_RUN", "nas_runtime": "NOT_RUN",
        "legal_rights_released": False, "devpost_submitted": False,
        "local_prototype_excluded_from_zip": True,
    }
    audit = {
        "status": "OWNER_REVIEW_PDF_GEOMETRY_PASS_NOT_RELEASE",
        "source_pdf_sha256": hash_of(pdf), "preview_png_sha256": hash_of(png),
        "pages": 1, "clipped_text_blocks_found": 0,
        "ten_questions_visible_in_extracted_text": True,
        "manual_visual_editorial_review": "PENDING",
        "official_creator": "NOT_RUN", "registered_nas_agent": "NOT_RUN",
        "devpost_submitted": False, "release_gate": "HOLD",
    }
    files = {
        PDF: pdf, ZIP: inner,
        MANIFEST: json.dumps(manifest).encode(),
        PREVIEW: png, AUDIT: json.dumps(audit).encode(),
    }
    pins = dict(expected_pdf=hash_of(pdf), expected_zip=hash_of(inner),
                expected_skill=hash_of(skill), expected_qa=hash_of(qa),
                expected_png=hash_of(png))
    return files, pins


class G76ExportIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.files, self.pins = example()

    def run_good(self, *, pdf=None, inner_zip=None):
        return verify_archive(archive(self.files), exported_pdf=pdf,
                              exported_skill_zip=inner_zip, **self.pins)

    def test_valid_synthetic_byte_parity_retains_release_hold(self):
        result = self.run_good(pdf=self.files[PDF], inner_zip=self.files[ZIP])
        self.assertEqual(result["status"], "G75_EXACT_EXPORTED_BYTES_VERIFIED_NOT_RELEASE")
        self.assertTrue(result["pdf_copy_verified"])
        self.assertTrue(result["skill_zip_copy_verified"])
        self.assertFalse(result["official_creator_execution_verified"])
        self.assertFalse(result["devpost_submitted"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_changed_individual_pdf_is_rejected(self):
        with self.assertRaisesRegex(IntegrityError, "Detached PDF"):
            self.run_good(pdf=self.files[PDF] + b"extra-but-pdf-might-open")

    def test_changed_individual_skill_zip_is_rejected(self):
        with self.assertRaisesRegex(IntegrityError, "Detached Skill ZIP"):
            self.run_good(inner_zip=self.files[ZIP] + b"extra")

    def test_mutated_original_pdf_inside_archive_is_rejected(self):
        self.files[PDF] += b"new"
        with self.assertRaises(IntegrityError):
            self.run_good()

    def test_extra_script_member_rejected(self):
        self.files["danger.py"] = b"print('not allowed')"
        with self.assertRaisesRegex(IntegrityError, "members differ"):
            self.run_good()

    def test_release_flag_forgery_rejected(self):
        forged = json.loads(self.files[MANIFEST])
        forged["legal_rights_released"] = True
        self.files[MANIFEST] = json.dumps(forged).encode()
        with self.assertRaisesRegex(IntegrityError, "Manifest claims"):
            self.run_good()

    def test_creator_invocation_forgery_rejected(self):
        forged = json.loads(self.files[MANIFEST])
        forged["official_creator"] = "VERIFIED"
        self.files[MANIFEST] = json.dumps(forged).encode()
        with self.assertRaisesRegex(IntegrityError, "Manifest claims"):
            self.run_good()

    def test_visual_qa_forged_manual_approval_rejected(self):
        forged = json.loads(self.files[AUDIT])
        forged["manual_visual_editorial_review"] = "APPROVED"
        self.files[AUDIT] = json.dumps(forged).encode()
        with self.assertRaisesRegex(IntegrityError, "Visual review"):
            self.run_good()

    def test_hash_only_does_not_accept_changed_inner_skill(self):
        altered = archive({SOURCE_MEMBER: b"changed"})
        self.files[ZIP] = altered
        # Even if the caller overrides the archive ZIP digest, nested pinned
        # Skill identity must still prevent silently importing a new Skill.
        with self.assertRaises(IntegrityError):
            verify_archive(archive(self.files), expected_zip=hash_of(altered),
                           **{k: v for k,v in self.pins.items() if k != "expected_zip"})

    def test_symlink_or_duplicate_member_refused(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for k, v in self.files.items():
                info = zipfile.ZipInfo(k)
                if k == PDF:
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, v)
        with self.assertRaises(IntegrityError):
            verify_archive(buf.getvalue(), **self.pins)
        buff = BytesIO()
        with zipfile.ZipFile(buff, "w") as z:
            for k,v in self.files.items():
                z.writestr(k, v)
            z.writestr(PDF, self.files[PDF])
        with self.assertRaises(IntegrityError):
            verify_archive(buff.getvalue(), **self.pins)

    def test_cli_returns_blocked_without_raw_path_echo(self):
        with TemporaryDirectory(prefix="flowpilot-g76-private-") as d:
            path = Path(d) / "raw-secrets-source.zip"
            path.write_bytes(archive(self.files))
            output = StringIO()
            with redirect_stdout(output):
                code = main(["--archive", str(path)])
            self.assertEqual(code, 2)
            reply = json.loads(output.getvalue())
            self.assertEqual(reply["status"], "BLOCKED_EXPORTED_ARTIFACT_INTEGRITY")
            self.assertNotIn(str(path), output.getvalue())
            self.assertNotIn("secrets", output.getvalue())


if __name__ == "__main__":
    unittest.main()
