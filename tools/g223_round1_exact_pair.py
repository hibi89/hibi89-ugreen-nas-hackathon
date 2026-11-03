"""G223: owner-local exact Round1 byte check; no upload, vendor code, NAS or release."""
from __future__ import annotations
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import stat
from zipfile import BadZipFile, ZipFile

SCHEMA = "ugreen.g223.exact-owner-round1-pair.v1"
SKILL_ZIP_SHA256 = "fecc138e34f5fa88c8119baefdb70acec22ad92bf324305d7f5fe179fd1cc4a9"
SKILL_ROOT_SHA256 = "644d9a79aede8b152d5e68d2a8e3cc2ba182e66e6a53e6853eee47ff85d037e4"
PDF_SHA256 = "375a3e5400f767f14866e3eb4acb7637aa43e12baacf4bed5d57033ac8ede59a"
SUPERSEDED_G222_REPORT_SHA256 = "57b017f9e361d0b8b827d3f9dcc055b1453c4972411d6bc7af12b1e8744e5385"
ALLOWED = frozenset({
    "flowpilot-3/SKILL.md",
    "flowpilot-3/references/modes-and-evidence.md",
    "flowpilot-3/references/failure-and-disclosure.md",
})
MAX_PDF = 1_000_000
MAX_ZIP = 10_000_000
MAX_MEMBER = 1_000_000

class PairRejected(ValueError):
    """Fail closed without echoing private text or local paths."""

def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()

def safe_read(path: Path, limit: int) -> bytes:
    try:
        if path.is_symlink() or not path.is_file():
            raise PairRejected("UNSAFE_INPUT")
        size = path.stat().st_size
        if not 0 < size <= limit:
            raise PairRejected("SIZE_OR_MISSING")
        raw = path.read_bytes()
        if len(raw) != size:
            raise PairRejected("INPUT_CHANGED_DURING_READ")
        return raw
    except (OSError, ValueError) as exc:
        if isinstance(exc, PairRejected):
            raise
        raise PairRejected("LOCAL_INPUT_UNAVAILABLE") from exc

def check_package(raw: bytes, expected_zip: str, expected_root: str) -> dict:
    if not 0 < len(raw) <= MAX_ZIP or digest(raw) != expected_zip:
        raise PairRejected("SKILL_ZIP_BYTE_DRIFT")
    try:
        with ZipFile(BytesIO(raw), "r") as archive:
            entries = archive.infolist()
            names = [info.filename for info in entries]
            if len(entries) != 3 or set(names) != ALLOWED or len(set(names)) != 3:
                raise PairRejected("SKILL_MEMBERS_INVALID")
            if any(
                info.is_dir() or info.flag_bits & 1 or info.file_size > MAX_MEMBER
                or stat.S_ISLNK(info.external_attr >> 16) or info.compress_size > MAX_ZIP
                for info in entries
            ) or sum(x.file_size for x in entries) > MAX_ZIP:
                raise PairRejected("SKILL_MEMBER_UNSAFE")
            for info in entries:
                if not archive.read(info).decode("utf-8", errors="strict").strip():
                    raise PairRejected("EMPTY_SKILL_MEMBER")
            if archive.testzip() is not None:
                raise PairRejected("SKILL_CRC_FAILED")
            source = archive.read("flowpilot-3/SKILL.md")
            if digest(source) != expected_root:
                raise PairRejected("ROOT_SKILL_BYTE_DRIFT")
            if not source.startswith(b"---\nname: flowpilot-3\n"):
                raise PairRejected("SKILL_FRONTMATTER_DRIFT")
            for reference in sorted(ALLOWED - {"flowpilot-3/SKILL.md"}):
                if reference.split("flowpilot-3/", 1)[1].encode("utf-8") not in source:
                    raise PairRejected("UNLINKED_REFERENCE")
    except (BadZipFile, RuntimeError, EOFError, OSError, UnicodeError, OverflowError) as exc:
        raise PairRejected("INVALID_SKILL_ZIP") from exc
    return {"zip_sha256": digest(raw), "zip_bytes": len(raw),
            "root_sha256": digest(source), "markdown_members": len(entries)}

def check_pdf(raw: bytes, expected_pdf: str) -> dict:
    if not 0 < len(raw) <= MAX_PDF or digest(raw) != expected_pdf:
        raise PairRejected("PDF_BYTE_DRIFT")
    if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-1024:]:
        raise PairRejected("INVALID_PDF_BYTES")
    return {"pdf_sha256": digest(raw), "pdf_bytes": len(raw),
            "pdf_text_and_visual_qa": ("PINNED_G222_PDF_REVIEWED_2026_11_03"
                                       if expected_pdf == PDF_SHA256 else "SYNTHETIC_TEST_ONLY")}

def review(skill_zip: bytes, pdf: bytes, *, previous_report: bytes | None = None,
           expected_zip: str = SKILL_ZIP_SHA256, expected_root: str = SKILL_ROOT_SHA256,
           expected_pdf: str = PDF_SHA256) -> dict:
    skill = check_package(skill_zip, expected_zip, expected_root)
    proposal = check_pdf(pdf, expected_pdf)
    previous = "NOT_PROVIDED"
    if previous_report is not None:
        if not 0 < len(previous_report) <= 20_000:
            raise PairRejected("REPORT_SIZE_INVALID")
        try:
            data = json.loads(previous_report)
        except (UnicodeError, ValueError, TypeError) as exc:
            raise PairRejected("REPORT_NOT_JSON") from exc
        if type(data) is not dict:
            raise PairRejected("REPORT_NOT_OBJECT")
        if data.get("new_pdf_sha256") != expected_pdf or data.get("source_skill_zip_sha256") != expected_zip:
            raise PairRejected("STALE_OR_DIFFERENT_PAIR_REPORT")
        previous = "PINNED_PAIR_MATCH"
    return {"schema": SCHEMA, "status": "EXACT_PAIR_BYTES_VERIFIED_OFFLINE_NOT_OFFICIAL",
            "skill": skill, "proposal": proposal, "previous_report": previous,
            "superseded_g222_report_pdf_sha256": SUPERSEDED_G222_REPORT_SHA256,
            "official_creator_executed": False, "official_checker_executed": False,
            "nas_test_executed": False, "devpost_submitted": False,
            "owner_final_release_approved": False, "release_gate": "HOLD"}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner-local G223 exact bytes; never submits")
    parser.add_argument("--skill-zip", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--compare-old-report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = review(safe_read(args.skill_zip, MAX_ZIP), safe_read(args.pdf, MAX_PDF),
                        previous_report=safe_read(args.compare_old_report, 20_000)
                        if args.compare_old_report is not None else None)
        code = 0
    except (PairRejected, ValueError, TypeError, KeyError, OSError) as exc:
        result = {"schema": SCHEMA, "status": "PAIR_REFUSED",
                  "reason_code": str(exc) if isinstance(exc, PairRejected) else "INPUT_FAILED",
                  "official_creator_executed": False, "official_checker_executed": False,
                  "release_gate": "HOLD"}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
