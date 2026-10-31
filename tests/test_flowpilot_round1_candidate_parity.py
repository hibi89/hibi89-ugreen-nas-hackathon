"""G123 synthetic owner bundle byte parity, security, and release-hold regression."""
from __future__ import annotations
from copy import deepcopy
import hashlib
from io import BytesIO
import json
import subprocess
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from flowpilot_round1_candidate_parity import inspect_owner_review_bundle,CandidateRefused

SKILL=b"---\nname: flowpilot-3\ndescription: Original synthetic review flow\n---\n# ChatGPT and Codex third-party disclosure\n"
PDF=b"%PDF-1.4\n%synthetic\n%%EOF\n"
SOURCE={
    "status":"OWNER_REVIEW_NOT_SUBMITTED",
    "source_skill_sha256":hashlib.sha256(SKILL).hexdigest(),
    "questions":[{"question":f"question-{i}","answer":"One short synthetic answer."}
                 for i in range(1,11)],
    "substantive_word_count":40,
    "disclosure":"ChatGPT and Codex assisted this test; no third-party redistributed.",
    "devpost_submitted":False,"real_nas_verified":False,"release_gate":"HOLD",
}


def zip_bytes(rows:list[tuple[str,bytes]])->bytes:
    b=BytesIO()
    with ZipFile(b,"w") as f:
        for name,data in rows:
            f.writestr(name,data)
    return b.getvalue()


def make_bundle(*,source=None,manifest_edit=None,zip_files=None,pdf=PDF):
    local=deepcopy(SOURCE if source is None else source)
    zip_data=zip_bytes(zip_files if zip_files is not None else [("flowpilot-3/SKILL.md",SKILL)])
    manifest={
        "schema":"flowpilot-g103-owner-review-v1","status":"NOT_SUBMITTED",
        "release_gate":"HOLD","source_skill_sha256":hashlib.sha256(SKILL).hexdigest(),
        "source_skill_bytes":len(SKILL),
        "submission_zip_sha256":hashlib.sha256(zip_data).hexdigest(),
        "submission_zip_bytes":len(zip_data),
        "pdf_sha256":hashlib.sha256(pdf).hexdigest(),
        "pdf_bytes":len(pdf),"substantive_words":40,
        "official_checker_executed":False,
        "nas_verified":False,"right_and_license_cleared":False,
    }
    if manifest_edit:
        manifest_edit(manifest)
    out=zip_bytes([
        ("FlowPilot3_G103_SKILL_OWNER_REVIEW_NOT_SUBMITTED.zip",zip_data),
        ("FlowPilot3_G103_ROUND1_PROPOSAL_OWNER_REVIEW_NOT_SUBMITTED.pdf",pdf),
        ("G103_MANIFEST.json",json.dumps(manifest).encode()),
        ("G103_ROUND1_PROPOSAL_SOURCE.json",json.dumps(local).encode()),
    ])
    return out,{"skill":hashlib.sha256(SKILL).hexdigest(),
                "zip":hashlib.sha256(zip_data).hexdigest(),
                "pdf":hashlib.sha256(pdf).hexdigest()}

class CandidateParityTests(unittest.TestCase):
    def test_synthetic_exact_bundle_no_release_even_on_pass(self):
        raw,pins=make_bundle()
        result=inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
        self.assertEqual(result["status"],"G103_BYTE_PARITY_AND_STRUCTURE_PASS_NOT_OFFICIAL")
        self.assertEqual(result["proposal_question_count"],10)
        self.assertEqual(result["whitespace_words"],40)
        self.assertEqual(result["conservative_token_words"],40)
        self.assertEqual(result["release_gate"],"HOLD")
        self.assertFalse(result["official_uliya_checker_executed"])
        self.assertFalse(result["native_nas_verified"])
        self.assertFalse(result["pdf_visual_and_text_parity_independently_verified_here"])
    def test_synthetic_cannot_claim_real_g103_identity(self):
        raw,_=make_bundle()
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw)
    def test_rejects_archive_mismatch_and_corrupt_pdf(self):
        raw,pins=make_bundle()
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=dict(pins,pdf="f"*64))
        raw,pins=make_bundle(pdf=b"NOT A PDF")
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_reject_unsupported_executable_in_skill_zip(self):
        raw,pins=make_bundle(zip_files=[("flowpilot-3/SKILL.md",SKILL),("setup.py",b"print('oops')")])
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_reject_skill_frontmatter_mismatch(self):
        bad=SKILL.replace(b"flowpilot-3",b"other-skill")
        raw,pins=make_bundle(zip_files=[("flowpilot-3/SKILL.md",bad)])
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_release_assertion_cannot_be_injected(self):
        for field,value in (("official_checker_executed",True),("nas_verified",True),
                            ("right_and_license_cleared",True),("release_gate","READY"),
                            ("status","SUBMITTED")):
            with self.subTest(field=field):
                raw,pins=make_bundle(manifest_edit=lambda m:m.__setitem__(field,value))
                with self.assertRaises(CandidateRefused):
                    inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_missing_or_duplicate_proposal_question_refused(self):
        for mutate in ("short","duplicate","blank"):
            source=deepcopy(SOURCE)
            if mutate=="short":source["questions"].pop()
            if mutate=="duplicate":source["questions"][1]["question"]=source["questions"][0]["question"]
            if mutate=="blank":source["questions"][0]["answer"]=""
            raw,pins=make_bundle(source=source)
            with self.subTest(mutate=mutate),self.assertRaises(CandidateRefused):
                inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_source_manifest_wrong_word_count_refused(self):
        source=deepcopy(SOURCE)
        source["substantive_word_count"]=800
        raw,pins=make_bundle(source=source)
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_conservative_word_cap_blocks_misdeclared_low_count(self):
        source=deepcopy(SOURCE)
        source["questions"][0]["answer"]=" ".join(["realword"]*520)
        raw,pins=make_bundle(source=source)
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_disclosure_absence_refused(self):
        source=deepcopy(SOURCE)
        source["disclosure"]="Secret without AI tool acknowledgement"
        raw,pins=make_bundle(source=source)
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
    def test_raw_private_values_never_echoed(self):
        raw,pins=make_bundle()
        result=inspect_owner_review_bundle(raw,synthetic_test_profile=pins)
        self.assertNotIn("Original synthetic",json.dumps(result))
        self.assertNotIn("One short synthetic",json.dumps(result))
    def test_duplicate_outer_zip_entry_refused(self):
        raw,pins=make_bundle()
        data=BytesIO()
        with ZipFile(BytesIO(raw)) as z:
            with ZipFile(data,"w") as dest:
                for name in z.namelist():
                    dest.writestr(name,z.read(name))
                dest.writestr("G103_MANIFEST.json",b"{}")
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(data.getvalue(),synthetic_test_profile=pins)
    def test_unknown_synthetic_pin_schema_refused(self):
        raw,pins=make_bundle()
        with self.assertRaises(CandidateRefused):
            inspect_owner_review_bundle(raw,synthetic_test_profile=dict(pins,extra="secret"))

if __name__=="__main__":
    unittest.main()
