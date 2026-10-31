"""G140 manifest drift, ZIP tampering and release-assertion regressions.

Synthetic only. Does not contain or upload owner-private G103/G139 files.
"""
from __future__ import annotations

import hashlib
import io
import json
from unittest.mock import patch
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


class G148ExactG147OwnerPairTests(unittest.TestCase):
    """All files synthetic, pins monkeypatched; no G147 private bytes in public repo."""
    def setUp(self):
        from unittest.mock import patch
        import flowpilot_artifact_manifest_gate as gate
        self.gate = gate
        entries = {
            "flowpilot-3/SKILL.md": (
                b"---\nname: flowpilot-3\ndescription: Test fixture only.\n---\n"
                b"# hackathon-original\nChatGPT third-party registered rights check\n"
                b"[cap](references/CAPABILITY_AND_PLAN_CONTRACT.md)\n"
                b"[safety](references/SAFETY_AND_SCENARIOS.md)\n"),
            "flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md": b"# synthetic capability\n",
            "flowpilot-3/references/SAFETY_AND_SCENARIOS.md": b"# synthetic safety\n",
        }
        buff = io.BytesIO()
        with ZipFile(buff, "w", compression=ZIP_DEFLATED) as z:
            for name, raw in entries.items():
                z.writestr(name, raw)
        self.z = buff.getvalue()
        self.pdf = b"%PDF-1.4\nG148_SYNTHETIC_FIXTURE_ONLY\n%%EOF"
        self.pins = {name: hashlib.sha256(b).hexdigest() for name, b in entries.items()}
        self.pins["zip"] = hashlib.sha256(self.z).hexdigest()
        self.pins["pdf"] = hashlib.sha256(self.pdf).hexdigest()
        self.manifest = {
            "schema": "g147-exact-owner-review-v1",
            "owner_review_only": True, "release_gate": "HOLD",
            "first_party_checker_executed": False,
            "registered_uliya_expert_verified": False,
            "real_nas_verified": False, "devpost_submitted": False,
            "package_member_count": 3,
            "substantive_english_word_count": 330, "pdf_pages": 1,
            "package_members": [{"name": name, "bytes": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest()}
                                for name, raw in entries.items()],
            "artifacts": {
                gate._G147_BASE + ".pdf": {
                    "bytes": len(self.pdf), "sha256": self.pins["pdf"]},
                gate._G147_BASE + ".zip": {
                    "bytes": len(self.z), "sha256": self.pins["zip"]},
            },
        }
        patcher = patch.object(gate, "_G147_EXPECTED", self.pins)
        patcher.start()
        self.addCleanup(patcher.stop)

    def verify(self, pdf=None, z=None, manifest=None):
        return self.gate.verify_g147_candidate(
            self.pdf if pdf is None else pdf,
            self.z if z is None else z,
            json.dumps(self.manifest if manifest is None else manifest).encode())

    def test_g147_exact_synthetic_structure_and_sha_pass_is_not_release(self):
        r = self.verify()
        self.assertEqual(r["status"], "G147_EXACT_LOCAL_PAIR_VERIFIED_NOT_OFFICIAL")
        self.assertEqual(r["markdown_member_count"], 3)
        self.assertFalse(r["official_checker_executed"])
        self.assertFalse(r["pdf_text_verified"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_changed_pdf_bits_even_with_forged_manifest_are_refused(self):
        raw = self.pdf.replace(b"G148_SYNTHETIC", b"G149_SYNTHETIC")
        forged = json.loads(json.dumps(self.manifest))
        forged["artifacts"][self.gate._G147_BASE + ".pdf"] = {
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        with self.assertRaisesRegex(ArtifactRefused, "PINNED_PAIR"):
            self.verify(pdf=raw, manifest=forged)

    def test_replaced_reference_with_forged_manifest_refused(self):
        files = {
            "flowpilot-3/SKILL.md": b"---\nname: flowpilot-3\ndescription: altered\n---\n",
            "flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md": b"x",
            "flowpilot-3/references/SAFETY_AND_SCENARIOS.md": b"y",
        }
        bio = io.BytesIO()
        with ZipFile(bio, "w") as z:
            for k, v in files.items(): z.writestr(k, v)
        with self.assertRaisesRegex(ArtifactRefused, "PINNED_PAIR"):
            self.verify(z=bio.getvalue())

    def test_manifest_stale_pdf_sha_and_false_checker_claim_refused(self):
        for key, value in (("first_party_checker_executed", True),
                           ("release_gate", "READY"),
                           ("pdf_pages", 2)):
            m = dict(self.manifest)
            m[key] = value
            with self.subTest(key=key), self.assertRaises(ArtifactRefused):
                self.verify(manifest=m)
        m = json.loads(json.dumps(self.manifest))
        m["artifacts"][self.gate._G147_BASE + ".pdf"]["sha256"] = "0"*64
        with self.assertRaisesRegex(ArtifactRefused, "STALE"):
            self.verify(manifest=m)

    def test_missing_or_duplicated_member_declared_rejected(self):
        m = json.loads(json.dumps(self.manifest))
        m["package_members"] = m["package_members"][:-1]
        with self.assertRaisesRegex(ArtifactRefused, "MEMBER"):
            self.verify(manifest=m)
        m["package_members"] = [self.manifest["package_members"][0]]*3
        with self.assertRaisesRegex(ArtifactRefused, "MEMBER"):
            self.verify(manifest=m)

    def test_double_json_key_cannot_approve(self):
        raw = json.dumps(self.manifest).encode()
        raw = raw.replace(b'"release_gate":', b'"release_gate": "READY", "release_gate":', 1)
        with self.assertRaisesRegex(ArtifactRefused, "DUPLICATE"):
            self.gate.verify_g147_candidate(self.pdf, self.z, raw)

    def test_default_g139_entrypoint_still_g140_and_bad_g147_paths_refused(self):
        # The new checker is opt-in, leaving the existing g139 contract untouched.
        self.assertTrue(callable(self.gate.verify_candidate))
        with self.assertRaises(ArtifactRefused):
            self.verify(z=b"bad")

    def test_invalid_pdf_flag_rejected(self):
        with self.assertRaisesRegex(ArtifactRefused, "INVALID_PDF_TEXT_FLAG"):
            self.gate.verify_g147_candidate(self.pdf, self.z,
                json.dumps(self.manifest).encode(), require_pdf_text="yes")



if __name__ == "__main__":
    unittest.main()
