"""G76: byte-verify exported G75 Round 1 owner-review archive and detached files.

G75's GitHub Actions uploaded a ZIP containing PDF, Skill ZIP, JSON
manifest, PNG visual preview and JSON visual audit. The archive, not an
unverified re-rendered detached PDF, is the provenance root.

Default policy pins exact G75 CI bytes; test overrides are injectable ONLY
into verify_archive(), never exposed by CLI. This does not prove official
Creator invocation, copyright clearance, NAS integration, or submission.
No file writes, network, credential access, or external uploads.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import stat
from zipfile import BadZipFile, ZipFile

SKILL_SHA = "47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"
PDF_SHA = "1ca7c52761ce3764ee5feaf8092eaeb12d85f670069ea51289482e7a794cc6d8"
ZIP_SHA = "06127d6da75a958d57524ac1c39294f4f7f366bba925af187280891df9d76bce"
QA_SHA = "3c371e1ca58d17f14dd31c9e0cc15207b5ec428e19b8bcb5f526411cf3eb2dc6"
PNG_SHA = "c5e08b74167b8a070a433b388c83872a27a4c83edf82856a9c6262f7b053b16b"
PDF = "NAS_FlowPilot_3_Round1_OWNER_REVIEW.pdf"
ZIP = "NAS_FlowPilot_3_Round1_OWNER_REVIEW.zip"
MANIFEST = "NAS_FlowPilot_3_Round1_OWNER_REVIEW_manifest.json"
PREVIEW = "NAS_FlowPilot_3_Round1_PREVIEW.png"
AUDIT = "NAS_FlowPilot_3_Round1_visual_audit.json"
MEMBERS = {PDF, ZIP, MANIFEST, PREVIEW, AUDIT}
SOURCE_MEMBER = "flowpilot-nas/SKILL.md"
MAX_ARCHIVE_BYTES = 10_000_000


class IntegrityError(ValueError):
    """Refuse unsafe/mutated exports without echoing any file paths."""


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _bounded_zip(raw: bytes, required: set[str], *, uncompressed_limit: int) -> dict[str, bytes]:
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise IntegrityError("Archive size invalid")
    try:
        with ZipFile(BytesIO(raw)) as z:
            entries = z.infolist()
            names = [p.filename for p in entries]
            if (len(names) != len(required) or set(names) != required
                    or len(names) != len(set(names))):
                raise IntegrityError("Archive members differ from pinned package")
            if any(
                p.is_dir() or (p.flag_bits & 1) or p.file_size > uncompressed_limit
                or stat.S_ISLNK((p.external_attr >> 16) & 0xffff)
                or p.compress_size > MAX_ARCHIVE_BYTES
                for p in entries
            ):
                raise IntegrityError("Unsafe archive member")
            if sum(p.file_size for p in entries) > uncompressed_limit:
                raise IntegrityError("Archive expanded size exceeds limit")
            return {name: z.read(name) for name in names}
    except (BadZipFile, RuntimeError, OSError) as exc:
        raise IntegrityError("Invalid or corrupted zip archive") from exc


def verify_archive(archive: bytes, *, exported_pdf: bytes | None = None,
                   exported_skill_zip: bytes | None = None,
                   expected_pdf: str = PDF_SHA, expected_zip: str = ZIP_SHA,
                   expected_skill: str = SKILL_SHA, expected_qa: str = QA_SHA,
                   expected_png: str = PNG_SHA) -> dict:
    """Verify exact original archive/detached bytes. Default hashes are immutable.

    Parameterized hashes enable only the unit-test's synthetic fixture; the
    command-line interface does not expose any hash override or release action.
    """
    members = _bounded_zip(archive, MEMBERS, uncompressed_limit=4_000_000)
    pdf, skill_zip, png = members[PDF], members[ZIP], members[PREVIEW]
    try:
        manifest = json.loads(members[MANIFEST])
        audit = json.loads(members[AUDIT])
    except (UnicodeDecodeError, ValueError) as exc:
        raise IntegrityError("Manifest or visual audit unreadable") from exc
    if not isinstance(manifest, dict) or not isinstance(audit, dict):
        raise IntegrityError("Manifest and visual audit must be objects")
    if (_sha(pdf) != expected_pdf or _sha(skill_zip) != expected_zip
            or _sha(png) != expected_png):
        raise IntegrityError("Actual archived PDF/ZIP/PNG hashes differ from pinned CI")
    if (manifest.get("status") != "OWNER_REVIEW_NOT_SUBMITTED"
            or manifest.get("source_skill_sha256") != expected_skill
            or manifest.get("qa_sha256") != expected_qa
            or manifest.get("pdf_sha256") != expected_pdf
            or manifest.get("zip_sha256") != expected_zip
            or manifest.get("pdf_bytes") != len(pdf)
            or manifest.get("zip_bytes") != len(skill_zip)
            or manifest.get("pdf_pages") != 1
            or manifest.get("questions") != 10
            or manifest.get("substantive_english_words") != 360
            or manifest.get("skill_members") != [SOURCE_MEMBER]
            or manifest.get("source_exact_match") is not True
            or manifest.get("official_checker") != "PINNED_STATIC_PASS_ONLY"
            or manifest.get("official_creator") != "NOT_RUN"
            or manifest.get("nas_runtime") != "NOT_RUN"
            or manifest.get("legal_rights_released") is not False
            or manifest.get("devpost_submitted") is not False
            or manifest.get("local_prototype_excluded_from_zip") is not True):
        raise IntegrityError("Manifest claims differ from reviewed G75 hold")
    if (audit.get("status") != "OWNER_REVIEW_PDF_GEOMETRY_PASS_NOT_RELEASE"
            or audit.get("source_pdf_sha256") != expected_pdf
            or audit.get("preview_png_sha256") != expected_png
            or audit.get("pages") != 1
            or audit.get("clipped_text_blocks_found") != 0
            or audit.get("ten_questions_visible_in_extracted_text") is not True
            or audit.get("manual_visual_editorial_review") != "PENDING"
            or audit.get("official_creator") != "NOT_RUN"
            or audit.get("registered_nas_agent") != "NOT_RUN"
            or audit.get("devpost_submitted") is not False
            or audit.get("release_gate") != "HOLD"):
        raise IntegrityError("Visual review record differs from pinned G75 hold")
    inner = _bounded_zip(skill_zip, {SOURCE_MEMBER}, uncompressed_limit=1_000_000)
    skill = inner[SOURCE_MEMBER]
    if (_sha(skill) != expected_skill or manifest.get("zip_unpacked_bytes") != len(skill)):
        raise IntegrityError("Inner Skill source differs from pinned canonical source")
    if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]:
        raise IntegrityError("PDF header/trailer invalid")
    if exported_pdf is not None and exported_pdf != pdf:
        raise IntegrityError("Detached PDF differs from CI archive's PDF")
    if exported_skill_zip is not None and exported_skill_zip != skill_zip:
        raise IntegrityError("Detached Skill ZIP differs from CI archive's Skill ZIP")
    return {
        "status": "G75_EXACT_EXPORTED_BYTES_VERIFIED_NOT_RELEASE",
        "pdf_sha256": expected_pdf, "pdf_bytes": len(pdf),
        "skill_zip_sha256": expected_zip, "skill_zip_bytes": len(skill_zip),
        "skill_sha256": expected_skill,
        "pdf_copy_verified": exported_pdf is not None,
        "skill_zip_copy_verified": exported_skill_zip is not None,
        "official_creator_execution_verified": False,
        "nas_runtime_verified": False, "owner_release_approved": False,
        "devpost_submitted": False, "release_gate": "HOLD",
    }


def _read(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise IntegrityError("Unsafe input file")
    return path.read_bytes()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify G75 owner-review CI archive; NO release")
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--pdf-copy", type=Path)
    p.add_argument("--skill-zip-copy", type=Path)
    args = p.parse_args(argv)
    try:
        result = verify_archive(
            _read(args.archive),
            exported_pdf=_read(args.pdf_copy) if args.pdf_copy else None,
            exported_skill_zip=_read(args.skill_zip_copy) if args.skill_zip_copy else None,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (IntegrityError, OSError, ValueError, TypeError, KeyError, OverflowError):
        print(json.dumps({"status": "BLOCKED_EXPORTED_ARTIFACT_INTEGRITY",
                          "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
