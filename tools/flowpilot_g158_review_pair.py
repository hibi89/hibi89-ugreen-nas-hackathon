"""G158: private, non-submittable owner review pairing of exact G157 PDF and G147 Skill ZIP.

Public source has no private bytes. This is NOT an official Uliya/Devpost checker.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import stat
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

import flowpilot_g157_proposal_review_gate as proposal
import flowpilot_g154_owner_offline_bundle as owner

PDF_NAME = "FlowPilot3_G157_JUDGE_FACING_PROPOSAL_DRAFT_NOT_SUBMITTED.pdf"
SKILL_NAME = owner.ZIP
MANIFEST_NAME = "G158_OWNER_REVIEW_PAIR_MANIFEST_NOT_SUBMITTED.json"
README_NAME = "README_OWNER_REVIEW_ONLY.txt"
PDF_ENTRY = "candidate/" + PDF_NAME
SKILL_ENTRY = "candidate/" + SKILL_NAME
PACKAGE_ENTRIES = (PDF_ENTRY, SKILL_ENTRY, MANIFEST_NAME, README_NAME)
SKILL_PIN = owner.PINS[owner.ZIP]
PDF_PIN = proposal.G157_SHA256
LEGACY_G147_PDF_PIN = proposal.G147_SHA256
SCHEMA = "flowpilot-g158-unapproved-review-pair-v1"
MAX_BUNDLE = 1_200_000
README = (
    "G158 OWNER-REVIEW PAIR ONLY - NOT A DEVPOST SUBMISSION.\n"
    "Contains exact unapproved G157 draft PDF and unchanged G147 Markdown Skill ZIP.\n"
    "Submit neither this outer bundle nor the old G147 PDF manifest.\n"
    "The PDF remains a draft; entrant rights, licenses, AI disclosure, accuracy,\n"
    "official Uliya checker and final submission all remain UNAPPROVED/NOT_RUN.\n"
    "Verification is local, read-only and does not upload data.\n"
).encode("ascii")


class PairRefused(ValueError):
    """No user paths or confidential excerpts in error reports."""


def _sha(blob: bytes) -> str:
    return sha256(blob).hexdigest()


def _load(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise PairRefused("LOCAL_INPUT_MISSING_OR_UNSAFE")
    blob = path.read_bytes()
    if not 0 < len(blob) <= limit:
        raise PairRefused("INPUT_SIZE_OR_RACE")
    return blob


def _json(raw: bytes) -> dict:
    if not 0 < len(raw) <= 10_000:
        raise PairRefused("MANIFEST_LIMIT")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PairRefused("MANIFEST_DUPLICATE_KEY")
            result[key] = value
        return result
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PairRefused("MANIFEST_INVALID") from exc
    if type(obj) is not dict:
        raise PairRefused("MANIFEST_OBJECT_REQUIRED")
    return obj


def _skill_check(skill_zip: bytes) -> dict:
    if _sha(skill_zip) != SKILL_PIN or not 0 < len(skill_zip) <= 10_000_000:
        raise PairRefused("G147_SKILL_PIN_MISMATCH")
    try:
        with ZipFile(BytesIO(skill_zip)) as zipfile:
            infos = zipfile.infolist()
            if len(infos) != 3 or {i.filename for i in infos} != set(owner.MEMBERS):
                raise PairRefused("G147_SKILL_MEMBER_SET")
            for info in infos:
                if (info.is_dir() or info.flag_bits & 1 or info.file_size > 1_000_000
                    or stat.S_ISLNK(info.external_attr >> 16)
                    or _sha(zipfile.read(info)) != owner.MEMBERS[info.filename]):
                    raise PairRefused("G147_SKILL_MEMBER_INVALID")
            if zipfile.testzip() is not None:
                raise PairRefused("G147_SKILL_CRC")
    except (BadZipFile, RuntimeError, EOFError, OverflowError, OSError) as exc:
        raise PairRefused("G147_SKILL_UNREADABLE") from exc
    return {"bytes": len(skill_zip), "sha256": SKILL_PIN, "markdown_members": 3}


def _validated_pair(pdf: bytes, skill_zip: bytes) -> dict:
    if type(pdf) is not bytes or type(skill_zip) is not bytes:
        raise PairRefused("INPUT_TYPE")
    if _sha(pdf) != PDF_PIN or not 0 < len(pdf) < 1_000_000:
        raise PairRefused("G157_PDF_PIN_MISMATCH")
    report = proposal.audit_pdf(pdf, "g157-unapproved-draft")
    if (report["owner_internal_labels_present"] or report["answer_count"] != 10
            or report["substantive_answer_word_count"] > 500):
        raise PairRefused("G157_PDF_CONTENT_UNAPPROVED")
    skill = _skill_check(skill_zip)
    return {"pdf": {"bytes": len(pdf), "sha256": PDF_PIN,
                    "answers": report["answer_count"],
                    "answer_word_count": report["substantive_answer_word_count"]},
            "skill_zip": skill}


def _manifest(pdf: bytes, skill_zip: bytes) -> dict:
    pair = _validated_pair(pdf, skill_zip)
    return {"schema": SCHEMA, "release_gate": "HOLD",
            "owner_approved": False, "first_party_checker_executed": False,
            "registered_expert_verified": False, "real_nas_verified": False,
            "devpost_submitted": False, "unapproved_draft": True,
            "original_g147_pdf_sha256_unchanged": LEGACY_G147_PDF_PIN,
            "original_g147_skill_sha256_unchanged": SKILL_PIN,
            "artifacts": {PDF_ENTRY: {"bytes": pair["pdf"]["bytes"], "sha256": PDF_PIN},
                          SKILL_ENTRY: {"bytes": pair["skill_zip"]["bytes"], "sha256": SKILL_PIN}},
            "pdf_answer_count": 10,
            "pdf_answer_word_count": pair["pdf"]["answer_word_count"],
            "required_approvals": ["entrant_content_and_rights", "AI_and_platform_license_review",
                                   "genuine_uliya_checker", "explicit_devpost_release"]}


def verify_pair(pdf: bytes, skill_zip: bytes, manifest_raw: bytes) -> dict:
    expected = _manifest(pdf, skill_zip)
    actual = _json(manifest_raw)
    if actual != expected:
        raise PairRefused("G158_PAIR_MANIFEST_DRIFT")
    return {"schema": SCHEMA, "status": "EXACT_G157_PDF_G147_SKILL_UNAPPROVED_PAIR_VERIFIED",
            "pdf_sha256": PDF_PIN, "skill_zip_sha256": SKILL_PIN,
            "pdf_answer_count": expected["pdf_answer_count"],
            "pdf_answer_word_count": expected["pdf_answer_word_count"],
            "official_checker_executed": False, "owner_approved": False,
            "devpost_submitted": False, "release_gate": "HOLD",
            "private_content_returned": False}


def _put(zipfile: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, (2026, 11, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zipfile.writestr(info, data)


def package_bytes(pdf: bytes, skill_zip: bytes) -> bytes:
    manifest = (json.dumps(_manifest(pdf, skill_zip), sort_keys=True, indent=2) + "\n").encode()
    result = BytesIO()
    with ZipFile(result, "w") as archive:
        for name, data in ((PDF_ENTRY, pdf), (SKILL_ENTRY, skill_zip),
                           (MANIFEST_NAME, manifest), (README_NAME, README)):
            _put(archive, name, data)
    raw = result.getvalue()
    verify_package(raw)
    return raw


def verify_package(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BUNDLE:
        raise PairRefused("OWNER_BUNDLE_SIZE")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) != 4 or {i.filename for i in infos} != set(PACKAGE_ENTRIES):
                raise PairRefused("OWNER_BUNDLE_MEMBERS")
            if any(i.is_dir() or i.flag_bits & 1 or stat.S_ISLNK(i.external_attr >> 16)
                   or i.file_size > 1_000_000 for i in infos):
                raise PairRefused("OWNER_BUNDLE_UNSAFE")
            values = {i.filename: archive.read(i.filename) for i in infos}
            if archive.testzip() is not None:
                raise PairRefused("OWNER_BUNDLE_CRC")
    except (BadZipFile, RuntimeError, EOFError, OverflowError, OSError) as exc:
        raise PairRefused("OWNER_BUNDLE_UNREADABLE") from exc
    if values[README_NAME] != README:
        raise PairRefused("OWNER_BUNDLE_INSTRUCTIONS_DRIFT")
    report = verify_pair(values[PDF_ENTRY], values[SKILL_ENTRY], values[MANIFEST_NAME])
    report["bundle_sha256"] = _sha(raw)
    return report


def build(pdf_path: Path, skill_path: Path, destination: Path) -> dict:
    pdf = _load(pdf_path, 1_000_000)
    skill = _load(skill_path, 10_000_000)
    raw = package_bytes(pdf, skill)
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir() or destination.parent.is_symlink():
        raise PairRefused("DESTINATION_EXISTS_OR_UNSAFE")
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    return verify_package(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G158 owner only; never submit this ZIP")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--build", action="store_true")
    modes.add_argument("--verify-package", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--skill-zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.build:
            if not all((args.pdf, args.skill_zip, args.output)):
                raise PairRefused("BUILD_ARGUMENTS_MISSING")
            result = build(args.pdf, args.skill_zip, args.output)
        else:
            if any((args.pdf, args.skill_zip, args.output)):
                raise PairRefused("VERIFY_ARGUMENTS_UNEXPECTED")
            result = verify_package(_load(args.verify_package, MAX_BUNDLE))
        code = 0
    except (PairRefused, proposal.ProposalRefused, OSError, ValueError, RuntimeError):
        result = {"schema": SCHEMA, "status": "G158_OWNER_PAIR_REFUSED",
                  "official_checker_executed": False, "release_gate": "HOLD",
                  "private_content_returned": False}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
