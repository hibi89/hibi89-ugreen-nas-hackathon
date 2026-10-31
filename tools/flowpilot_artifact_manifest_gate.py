"""G140: owner-local exact PDF/Markdown ZIP/manifest byte gate.

This is NOT the Uliya first-party Checker and does not run NAS/Expert,
create output, read folder contents, approve rights, or upload candidate bytes.
PDF text/layout must be verified separately by an actual PDF renderer.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import stat
from zipfile import BadZipFile, ZipFile

_SCHEMA = "g139-alternate-review-v1"
_BASE = "FlowPilot3_G139_ALTERNATE_OWNER_REVIEW_NOT_SUBMITTED"
_WORD = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*)(?![A-Za-z0-9])")
_ENTRY = "flowpilot-3/SKILL.md"
_MAX_PDF = 1_000_000
_MAX_ZIP = 10_000_000
_MAX_UNPACKED = 10_000_000
_MAX_FILE = 1_000_000
_MAX_JSON = 64_000


class ArtifactRefused(ValueError):
    """Sanitized denial, without owner paths or candidate excerpts."""


def _digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _manifest(raw: bytes) -> dict:
    if not 0 < len(raw) < _MAX_JSON:
        raise ArtifactRefused("MANIFEST_SIZE")
    def unique(items):
        output = {}
        for key, value in items:
            if key in output:
                raise ArtifactRefused("DUPLICATE_MANIFEST_KEY")
            output[key] = value
        return output
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (ValueError, UnicodeError, TypeError, RecursionError) as exc:
        raise ArtifactRefused("MANIFEST_INVALID") from exc
    if type(result) is not dict:
        raise ArtifactRefused("MANIFEST_OBJECT_REQUIRED")
    return result


def verify_candidate(pdf: bytes, skill_zip: bytes, manifest_raw: bytes) -> dict:
    """Verify exact current bytes; never infer official Checker/PDF visual PASS."""
    if (type(pdf) is not bytes or not 0 < len(pdf) <= _MAX_PDF
            or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]):
        raise ArtifactRefused("PDF_INVALID")
    if type(skill_zip) is not bytes or not 0 < len(skill_zip) <= _MAX_ZIP:
        raise ArtifactRefused("ZIP_SIZE")
    meta = _manifest(manifest_raw)
    if (meta.get("schema") != _SCHEMA or meta.get("owner_review_only") is not True
            or meta.get("official_checker") != "NOT_RUN"
            or meta.get("live_nas") != "NOT_RUN"
            or meta.get("devpost") != "NOT_SUBMITTED"
            or meta.get("official_checker_executed", False) is not False
            or meta.get("owner_approved_release", False) is not False
            or meta.get("release_gate", "HOLD") != "HOLD"
            or type(meta.get("substantive_english_words")) is not int
            or not 1 <= meta["substantive_english_words"] <= 500
            or type(meta.get("pdf_pages")) is not int
            or not 1 <= meta["pdf_pages"] <= 2):
        raise ArtifactRefused("UNTRUSTED_RELEASE_METADATA")
    expected = {
        _BASE + ".pdf": pdf, _BASE + ".zip": skill_zip,
    }
    artifacts = meta.get("artifacts")
    if type(artifacts) is not dict or set(artifacts) != set(expected):
        raise ArtifactRefused("EXPECTED_PAIR_MISSING")
    for key, blob in expected.items():
        entry = artifacts[key]
        if (type(entry) is not dict or set(entry) != {"bytes", "sha256"}
                or type(entry["bytes"]) is not int or entry["bytes"] != len(blob)
                or type(entry["sha256"]) is not str
                or entry["sha256"] != _digest(blob)):
            raise ArtifactRefused("STALE_OR_UNMATCHED_MANIFEST")
    try:
        with ZipFile(io.BytesIO(skill_zip)) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= 100:
                raise ArtifactRefused("ZIP_ENTRY_COUNT")
            members = {}
            seen = set()
            total = 0
            for info in infos:
                name = info.filename
                parts = name.split("/")
                key = name.casefold()
                if (name in seen or key in seen or info.is_dir()
                        or info.flag_bits & 1
                        or not name.startswith("flowpilot-3/")
                        or not name.endswith(".md")
                        or any(part in ("", ".", "..") for part in parts)
                        or any(ord(c) < 32 or ord(c) == 127 for c in name)
                        or "\\" in name or ":" in name
                        or (name != _ENTRY and
                            not name.startswith("flowpilot-3/references/"))
                        or stat.S_ISLNK(info.external_attr >> 16)
                        or not 0 < info.file_size <= _MAX_FILE):
                    raise ArtifactRefused("UNSAFE_MARKDOWN_ARCHIVE")
                seen.add(key)
                total += info.file_size
                if total > _MAX_UNPACKED:
                    raise ArtifactRefused("UNPACKED_LIMIT")
                members[name] = archive.read(info)
            if _ENTRY not in members or archive.testzip() is not None:
                raise ArtifactRefused("MISSING_SKILL_OR_CORRUPT_ARCHIVE")
    except (BadZipFile, RuntimeError, EOFError, OverflowError, OSError) as exc:
        raise ArtifactRefused("INVALID_ZIP") from exc
    try:
        skill = members[_ENTRY].decode("utf-8")
        references = {name: value.decode("utf-8") for name, value in members.items()
                      if name != _ENTRY}
    except UnicodeError as exc:
        raise ArtifactRefused("NOT_UTF8") from exc
    if not re.match(r"\A---\r?\nname: flowpilot-3\r?\ndescription: [^\r\n]{1,1024}\r?\n---\r?\n", skill):
        raise ArtifactRefused("SKILL_FRONTMATTER")
    for name in references:
        short = name.removeprefix("flowpilot-3/")
        if (f"]({short})" not in skill and f"<{short}>" not in skill):
            raise ArtifactRefused("UNLINKED_REFERENCE")
    recorded = meta.get("skill_members")
    if (type(recorded) is not list or len(recorded) != len(members)
            or not all(type(x) is dict and set(x) == {"name", "bytes"}
                       and type(x["name"]) is str and type(x["bytes"]) is int
                       for x in recorded)
            or {x["name"]: x["bytes"] for x in recorded} !=
                {name: len(raw) for name, raw in members.items()}
            or type(meta.get("uncompressed_zip_bytes")) is not int
            or meta["uncompressed_zip_bytes"] != total):
        raise ArtifactRefused("MEMBER_MANIFEST_DRIFT")
    return {
        "schema": "flowpilot-g140-owner-artifact-byte-gate-v1",
        "status": "LOCAL_BYTES_AND_MARKDOWN_STRUCTURE_MATCH",
        "skill_zip_sha256": _digest(skill_zip),
        "pdf_sha256": _digest(pdf),
        "member_count": len(members),
        "pdf_header_footer_checked": True,
        "pdf_text_and_visual_not_checked_by_this_gate": True,
        "official_checker_executed": False,
        "nas_verified": False,
        "owner_release_approved": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
        "private_content_returned": False,
    }


def _load(path: Path, limit: int) -> bytes:
    if (not path.is_absolute() or path.is_symlink()
            or path.parent.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= limit):
        raise ArtifactRefused("LOCAL_INPUT_REFUSED")
    raw = path.read_bytes()
    if not 0 < len(raw) <= limit:
        raise ArtifactRefused("LOCAL_INPUT_REFUSED")
    return raw



# G148 extends the existing G140 local-only artifact gate; it does not change
# older G139 validation. These G147 pins are PUBLIC HASHES, never private bytes.
_G147_BASE = "FlowPilot3_G147_RULES_ALIGNED_OWNER_REVIEW_NOT_SUBMITTED"
_G147_EXPECTED = {
    "zip": "d8c66b24000b6fb1f7ea8b0d69417febfc83128d935e9b8db33dd382bb9c64c1",
    "pdf": "bf5319f0b840747e53d3a84f78e4006bc932a4d5d2bd0671c9c43c6f3877b90f",
    "flowpilot-3/SKILL.md": "1062bba52833e3bbbc5f020739f80d2dee1dc2f2b428016e342075525bf2bc6d",
    "flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md": "4fa2235bdc164334f3592b16a358986718fc49a057ba800e931f5f7fc5017f49",
    "flowpilot-3/references/SAFETY_AND_SCENARIOS.md": "baf04355555f689266b46ba0866c25a022003d79ae8ad3f9475eda0408cc6ad0",
}


def verify_g147_candidate(pdf: bytes, skill_zip: bytes, manifest_raw: bytes, *,
                          require_pdf_text: bool = False) -> dict:
    """Read ONLY owner-supplied local bytes. Every result remains release HOLD.

    Hash validation is separate from mandatory first-party Uliya Checker and
    from any native NAS test. Optional PDF text reading requires local PyMuPDF.
    """
    if type(require_pdf_text) is not bool:
        raise ArtifactRefused("INVALID_PDF_TEXT_FLAG")
    if (type(pdf) is not bytes or not 0 < len(pdf) <= _MAX_PDF
            or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]
            or type(skill_zip) is not bytes or not 0 < len(skill_zip) <= _MAX_ZIP):
        raise ArtifactRefused("INVALID_G147_DOCUMENT_BYTES")
    # Do not let a self-authored manifest authorize different ZIP/PDF bytes.
    if _digest(skill_zip) != _G147_EXPECTED["zip"] or _digest(pdf) != _G147_EXPECTED["pdf"]:
        raise ArtifactRefused("G147_PINNED_PAIR_CHANGED")
    m = _manifest(manifest_raw)
    if (m.get("schema") != "g147-exact-owner-review-v1"
            or m.get("release_gate") != "HOLD"
            or m.get("owner_review_only") is not True
            or any(m.get(k) is not False for k in (
                "first_party_checker_executed", "registered_uliya_expert_verified",
                "real_nas_verified", "devpost_submitted"))
            or m.get("package_member_count") != 3
            or type(m.get("substantive_english_word_count")) is not int
            or not 1 <= m["substantive_english_word_count"] <= 500
            or type(m.get("pdf_pages")) is not int or m["pdf_pages"] != 1):
        raise ArtifactRefused("INVALID_G147_RELEASE_METADATA")
    artifacts = m.get("artifacts")
    expected_artifacts = {
        _G147_BASE + ".pdf": pdf,
        _G147_BASE + ".zip": skill_zip,
    }
    if type(artifacts) is not dict or set(artifacts) != set(expected_artifacts):
        raise ArtifactRefused("INVALID_G147_PAIR_MANIFEST")
    for filename, content in expected_artifacts.items():
        item = artifacts[filename]
        if (type(item) is not dict or set(item) != {"bytes", "sha256"}
                or type(item["bytes"]) is not int or item["bytes"] != len(content)
                or item["sha256"] != _digest(content)):
            raise ArtifactRefused("G147_STALE_PAIR_MANIFEST")
    members = {}
    try:
        with ZipFile(io.BytesIO(skill_zip)) as z:
            infos = z.infolist()
            allowed = set(_G147_EXPECTED) - {"pdf", "zip"}
            if len(infos) != 3 or set(x.filename for x in infos) != allowed:
                raise ArtifactRefused("G147_UNEXPECTED_MARKDOWN_MEMBERS")
            for info in infos:
                name = info.filename
                if (info.is_dir() or info.flag_bits & 1
                        or stat.S_ISLNK(info.external_attr >> 16)
                        or not 0 < info.file_size <= _MAX_FILE):
                    raise ArtifactRefused("G147_UNSAFE_MEMBER")
                content = z.read(info)
                if _digest(content) != _G147_EXPECTED[name]:
                    raise ArtifactRefused("G147_MEMBER_PIN_CHANGED")
                members[name] = content
            if z.testzip() is not None or sum(map(len, members.values())) > _MAX_UNPACKED:
                raise ArtifactRefused("G147_CORRUPT_OR_OVERSIZED_ZIP")
    except (BadZipFile, RuntimeError, EOFError, OSError, OverflowError) as exc:
        raise ArtifactRefused("G147_CORRUPT_ZIP") from exc
    records = m.get("package_members")
    if (type(records) is not list or len(records) != 3
            or any(type(r) is not dict or set(r) != {"name", "bytes", "sha256"}
                   or type(r["name"]) is not str or type(r["bytes"]) is not int
                   or type(r["sha256"]) is not str for r in records)
            or {r["name"]: (r["bytes"], r["sha256"]) for r in records}
            != {name: (len(b), _digest(b)) for name, b in members.items()}):
        raise ArtifactRefused("G147_MEMBER_MANIFEST_DRIFT")
    try:
        text = members[_ENTRY].decode("utf-8")
        for name, raw in members.items():
            if name != _ENTRY:
                raw.decode("utf-8")
                relative = name.removeprefix("flowpilot-3/")
                if f"]({relative})" not in text:
                    raise ArtifactRefused("G147_UNLINKED_REFERENCE")
    except UnicodeError as exc:
        raise ArtifactRefused("G147_INVALID_UTF8") from exc
    if (not re.match(r"\A---\r?\nname: flowpilot-3\r?\ndescription: [^\r\n]{1,1024}\r?\n---\r?\n", text)
            or not all(term in text.casefold()
                       for term in ("hackathon-original", "chatgpt", "third-party",
                                    "registered", "release_gate"))):
        # Release gate is a return-schema field, not a requirement in the Skill;
        # use the explicit consent/rights terms in candidate text instead.
        if not re.match(r"\A---\r?\nname: flowpilot-3\r?\ndescription: [^\r\n]{1,1024}\r?\n---\r?\n", text):
            raise ArtifactRefused("G147_INVALID_FRONTMATTER")
        if not all(term in text.casefold() for term in (
                "hackathon-original", "chatgpt", "third-party",
                "registered", "rights check")):
            raise ArtifactRefused("G147_MISSING_DISCLOSURES")
    text_checked = False
    if require_pdf_text:
        try:
            import fitz
        except ImportError as exc:
            raise ArtifactRefused("G147_PDF_TEXT_READER_UNAVAILABLE") from exc
        try:
            with fitz.open(stream=pdf, filetype="pdf") as doc:
                if doc.needs_pass or doc.page_count != 1:
                    raise ArtifactRefused("G147_PDF_LOCKED_OR_MULTIPAGE")
                content = doc[0].get_text(sort=True)
                first, end = content.find("1. What does"), content.find("Disclosures (excluded")
                if first < 0 or end <= first:
                    raise ArtifactRefused("G147_PDF_QA_BLOCK_MISSING")
                substantive = content[first:end]
                indices = [int(match.group(1)) for match in re.finditer(
                    r"(?m)^([1-9]|10)\.\s+\S+", substantive)]
                if indices != list(range(1, 11)) or len(substantive.split()) > 500:
                    raise ArtifactRefused("G147_PDF_QA_MISSING_OR_OVER_LIMIT")
                if "UGREEN Uliya/UGOS" not in content or "ChatGPT" not in content:
                    raise ArtifactRefused("G147_PDF_DISCLOSURE_MISSING")
            text_checked = True
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            raise ArtifactRefused("G147_PDF_TEXT_UNVERIFIED") from exc
    return {
        "schema": "flowpilot-g148-g147-owner-final-byte-gate-v1",
        "status": "G147_EXACT_LOCAL_PAIR_VERIFIED_NOT_OFFICIAL",
        "candidate_profile": "g147",
        "skill_zip_sha256": _digest(skill_zip),
        "pdf_sha256": _digest(pdf),
        "markdown_member_count": 3, "pdf_text_verified": text_checked,
        "pdf_visual_layout_independently_certified": False,
        "official_checker_executed": False,
        "registered_expert_verified": False, "real_nas_verified": False,
        "owner_rights_approved": False, "devpost_submitted": False,
        "release_gate": "HOLD", "private_content_returned": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Private local G139 artifact parity; not official Checker")
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--profile", choices=("g139", "g147"), default="g139")
    p.add_argument("--require-pdf-text", action="store_true",
                   help="Use installed PyMuPDF to inspect G147 actual PDF text")
    args = p.parse_args(argv)
    try:
        if args.profile == "g147":
            result = verify_g147_candidate(
                _load(args.pdf, _MAX_PDF), _load(args.zip, _MAX_ZIP),
                _load(args.manifest, _MAX_JSON),
                require_pdf_text=args.require_pdf_text)
        elif args.require_pdf_text:
            raise ArtifactRefused("G139_PDF_TEXT_UNSUPPORTED_BY_THIS_GATE")
        else:
            result = verify_candidate(
                _load(args.pdf, _MAX_PDF), _load(args.zip, _MAX_ZIP),
                _load(args.manifest, _MAX_JSON))
        code = 0
    except (ArtifactRefused, ValueError, TypeError, OSError):
        result = {"schema": "flowpilot-g140-owner-artifact-byte-gate-v1",
                  "status": "OWNER_CANDIDATE_PARITY_REFUSED",
                  "official_checker_executed": False, "release_gate": "HOLD"}
        code = 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
