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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Private local G139 artifact parity; not official Checker")
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args(argv)
    try:
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
