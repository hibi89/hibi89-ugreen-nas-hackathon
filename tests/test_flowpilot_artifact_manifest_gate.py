"""G140 manifest drift, ZIP tampering and release-assertion regressions.

Synthetic only. Does not contain or upload owner-private G103/G139 files.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_artifact_manifest_gate import ArtifactRefused, verify_candidate

PDF_NAME = "FlowPilot3_G139_ALTERNATE_OWNER_REVIEW_NOT_SUBMITTED.pdf"
ZIP_NAME = "FlowPilot3_G139_ALTERNATE_OWNER_REVIEW_NOT_SUBMITTED.zip"
SKILL = b"---\nname: flowpilot-3\ndescription: Synthetic unit test only.\n---\n# Synthetic\nRead [reference](references/GUIDE.md).\n"


class G140ArtifactGateTests(unittest.TestCase):
    def setup_fixture(self, extra=None):
        members = {"flowpilot-3/SKILL.md": SKILL,
                   "flowpilot-3/references/GUIDE.md": b"# Synthetic guide\n"}
        if extra:
            members.update(extra)
        buff = io.BytesIO()
        with ZipFile(buff, "w", compression=ZIP_DEFLATED) as z:
            for name, raw in members.items():
                z.writestr(name, raw)
        zip_bytes = buff.getvalue()
        # PDF structural byte smoke only: valid rendering intentionally not asserted.
        pdf = b"%PDF-1.4\nSYNTHETIC_TEST_ONLY\n%%EOF\n"
        manifest = {
            "schema": "g139-alternate-review-v1",
            "owner_review_only": True,
            "official_checker": "NOT_RUN",
            "live_nas": "NOT_RUN",
            "devpost": "NOT_SUBMITTED",
            "substantive_english_words": 10,
            "pdf_pages": 1,
            "artifacts": {
                PDF_NAME: {"bytes": len(pdf), "sha256": hashlib.sha256(pdf).hexdigest()},
                ZIP_NAME: {"bytes": len(zip_bytes), "sha256": hashlib.sha256(zip_bytes).hexdigest()},
            },
            "skill_members": [{"name": n, "bytes": len(b)} for n,b in members.items()],
            "uncompressed_zip_bytes": sum(map(len, members.values())),
        }
        return pdf, zip_bytes, manifest

    def call(self, pdf, z, manifest):
        return verify_candidate(pdf, z, json.dumps(manifest).encode())

    def test_exact_bytes_match_only_local_not_release(self):
        pdf, z, m = self.setup_fixture()
        result = self.call(pdf, z, m)
        self.assertEqual(result["status"], "LOCAL_BYTES_AND_MARKDOWN_STRUCTURE_MATCH")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertFalse(result["official_checker_executed"])
        self.assertTrue(result["pdf_text_and_visual_not_checked_by_this_gate"])

    def test_stale_pdf_manifest_refused(self):
        pdf, z, m = self.setup_fixture()
        m["artifacts"][PDF_NAME]["bytes"] += 4
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_stale_pdf_sha_refused(self):
        pdf, z, m = self.setup_fixture()
        m["artifacts"][PDF_NAME]["sha256"] = "0"*64
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_zip_replacement_refused(self):
        pdf, z, m = self.setup_fixture()
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z+b"modified", m)

    def test_unreferenced_markdown_refused(self):
        pdf, z, m = self.setup_fixture(extra={"flowpilot-3/references/UNLINKED.md": b"# Absent\n"})
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_traversal_zip_member_refused(self):
        pdf, z, m = self.setup_fixture(extra={"flowpilot-3/references/../escape.md": b"unsafe"})
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_disallowed_executable_zip_member_refused(self):
        pdf, z, m = self.setup_fixture(extra={"flowpilot-3/run.sh": b"echo foo"})
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_claimed_official_success_refused(self):
        pdf, z, m = self.setup_fixture()
        m["official_checker"] = "static-pass"
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)
        m["official_checker"] = "NOT_RUN"
        m["owner_approved_release"] = True
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_inconsistent_member_bytes_refused(self):
        pdf, z, m = self.setup_fixture()
        m["skill_members"][0]["bytes"] = 0
        with self.assertRaises(ArtifactRefused):
            self.call(pdf, z, m)

    def test_rejects_duplicate_json_keys(self):
        pdf, z, m = self.setup_fixture()
        raw = json.dumps(m).encode()
        raw = raw.replace(b'"schema":', b'"schema": "bogus", "schema":', 1)
        with self.assertRaises(ArtifactRefused):
            verify_candidate(pdf, z, raw)

    def test_corrupt_pdf_magic_refused(self):
        pdf, z, m = self.setup_fixture()
        with self.assertRaises(ArtifactRefused):
            self.call(b"not really a PDF", z, m)

if __name__ == "__main__":
    unittest.main()
