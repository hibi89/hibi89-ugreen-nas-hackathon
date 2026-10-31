"""G123: structural and byte-parity gate for owner-local Round 1 review bundle.

This is NOT the official Uliya Checker. Does not access NAS, run scripts,
extract to disk, certify rights, or submit Devpost. Reads a user-selected
local review ZIP, never prints owner contents, paths, or customer data.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
from zipfile import ZipFile, BadZipFile

SCHEMA = "flowpilot-g123-round1-owner-parity-v1"
PROFILE = {
    "skill": "f940bcd884b83d80fbecf533caee7d492488c274e1d3eab2b99b034b92428e15",
    "zip": "1496103b5c1b15da113867ed0cab57ad1e2dab0be80c2f06fd049cac359bf11b",
    "pdf": "b775510605be963e38ad05057a9cb1edcc5e79a6b1e3417e302af4887aaf6858",
}
FILES = frozenset((
    "FlowPilot3_G103_SKILL_OWNER_REVIEW_NOT_SUBMITTED.zip",
    "FlowPilot3_G103_ROUND1_PROPOSAL_OWNER_REVIEW_NOT_SUBMITTED.pdf",
    "G103_MANIFEST.json",
    "G103_ROUND1_PROPOSAL_SOURCE.json",
))
SKILL_ENTRY = "flowpilot-3/SKILL.md"
MAX_OUTER = 20 * 1024 * 1024
MAX_SKILL_ZIP = 10 * 1024 * 1024
MAX_SKILL_UNPACKED = 10 * 1024 * 1024
MAX_PDF = 1024 * 1024
WORD = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


class CandidateRefused(ValueError):
    """Never echo raw owner input or internal file paths."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zip_parts(data: bytes, *, allowed: frozenset[str],
               max_size: int, max_unpacked: int) -> dict[str, bytes]:
    if not isinstance(data, bytes) or not 0 < len(data) <= max_size:
        raise CandidateRefused("Unsupported ZIP size or type")
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) != len(allowed):
                raise CandidateRefused("ZIP entry count mismatch")
            seen = set()
            outputs = {}
            expanded = 0
            for info in infos:
                name = info.filename
                if (name not in allowed or name.casefold() in seen
                        or info.is_dir() or info.flag_bits & 1
                        or info.file_size > max_unpacked
                        or stat.S_ISLNK(info.external_attr >> 16)):
                    raise CandidateRefused("Unsafe or unsupported ZIP entry")
                seen.add(name.casefold())
                expanded += info.file_size
                if expanded > max_unpacked:
                    raise CandidateRefused("Excessive expanded size")
                outputs[name] = archive.read(info)
            if set(outputs) != allowed or archive.testzip() is not None:
                raise CandidateRefused("Incomplete ZIP or failed CRC")
            return outputs
    except (BadZipFile, RuntimeError, EOFError, OSError, ValueError, OverflowError) as exc:
        raise CandidateRefused("Invalid or corrupt ZIP") from exc


def _json(data: bytes) -> dict:
    if len(data) > 128 * 1024:
        raise CandidateRefused("Oversized metadata")
    def unique(items):
        value = {}
        for key, val in items:
            if key in value:
                raise CandidateRefused("Duplicate JSON key")
            value[key] = val
        return value
    try:
        output = json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                            parse_constant=lambda _: (_ for _ in ()).throw(
                                CandidateRefused("Invalid JSON number")))
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise CandidateRefused("Invalid metadata JSON") from exc
    if type(output) is not dict:
        raise CandidateRefused("Expected metadata object")
    return output


def inspect_owner_review_bundle(raw: bytes, *, synthetic_test_profile: dict | None = None) -> dict:
    """Independently recompute hashes and upper-bound English word count.

    A synthetic override is for unit tests only, explicitly marked as such,
    and still NEVER changes the release HOLD verdict.
    """
    if synthetic_test_profile is not None:
        if (type(synthetic_test_profile) is not dict
                or set(synthetic_test_profile) != set(PROFILE)
                or any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{64}", x)
                       for x in synthetic_test_profile.values())):
            raise CandidateRefused("Invalid synthetic profile")
    pins = PROFILE if synthetic_test_profile is None else synthetic_test_profile
    parts = _zip_parts(raw, allowed=FILES, max_size=MAX_OUTER,
                       max_unpacked=MAX_OUTER)
    manifest = _json(parts["G103_MANIFEST.json"])
    source = _json(parts["G103_ROUND1_PROPOSAL_SOURCE.json"])
    skillzip = parts["FlowPilot3_G103_SKILL_OWNER_REVIEW_NOT_SUBMITTED.zip"]
    pdf = parts["FlowPilot3_G103_ROUND1_PROPOSAL_OWNER_REVIEW_NOT_SUBMITTED.pdf"]
    nested = _zip_parts(skillzip, allowed=frozenset((SKILL_ENTRY,)),
                        max_size=MAX_SKILL_ZIP, max_unpacked=MAX_SKILL_UNPACKED)
    skill = nested[SKILL_ENTRY]
    if len(skill) > 1024 * 1024 or not 0 < len(pdf) <= MAX_PDF:
        raise CandidateRefused("File size violates Round 1 limits")
    if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]:
        raise CandidateRefused("Invalid PDF signature")
    s_sha, z_sha, p_sha = _digest(skill), _digest(skillzip), _digest(pdf)
    if (s_sha != pins["skill"] or z_sha != pins["zip"] or p_sha != pins["pdf"]
            or s_sha != manifest.get("source_skill_sha256")
            or z_sha != manifest.get("submission_zip_sha256")
            or p_sha != manifest.get("pdf_sha256")
            or s_sha != source.get("source_skill_sha256")
            or manifest.get("source_skill_bytes") != len(skill)
            or manifest.get("submission_zip_bytes") != len(skillzip)
            or manifest.get("pdf_bytes") != len(pdf)):
        raise CandidateRefused("Pinned or declared source mismatch")
    if (manifest.get("schema") != "flowpilot-g103-owner-review-v1"
            or manifest.get("status") != "NOT_SUBMITTED"
            or manifest.get("release_gate") != "HOLD"
            or manifest.get("official_checker_executed") is not False
            or manifest.get("nas_verified") is not False
            or manifest.get("right_and_license_cleared") is not False
            or source.get("status") != "OWNER_REVIEW_NOT_SUBMITTED"
            or source.get("devpost_submitted") is not False
            or source.get("real_nas_verified") is not False
            or source.get("release_gate") != "HOLD"):
        raise CandidateRefused("Inconsistent or unauthorized release assertions")
    try:
        text = skill.decode("utf-8")
    except UnicodeError as exc:
        raise CandidateRefused("Skill not UTF-8") from exc
    front = re.match(r"\A---\r?\nname: ([a-z0-9-]{2,64})\r?\ndescription: ([^\r\n]{1,1024})\r?\n---(?:\r?\n|$)", text)
    if not front or front.group(1) != "flowpilot-3" or not front.group(2).strip():
        raise CandidateRefused("Invalid Skill frontmatter")
    questions = source.get("questions")
    if (type(questions) is not list or len(questions) != 10
            or any(type(q) is not dict or set(q) != {"question", "answer"}
                   or type(q["question"]) is not str or not q["question"].strip()
                   or type(q["answer"]) is not str or not q["answer"].strip()
                   for q in questions)):
        raise CandidateRefused("Not exactly ten complete proposal answers")
    seen = {q["question"] for q in questions}
    if len(seen) != 10:
        raise CandidateRefused("Duplicate proposal question")
    raw_answers = " ".join(q["answer"] for q in questions)
    count_split = sum(len(q["answer"].split()) for q in questions)
    conservative_count = len(WORD.findall(raw_answers))
    claimed = manifest.get("substantive_words")
    if (type(claimed) is not int or type(source.get("substantive_word_count")) is not int
            or claimed != source["substantive_word_count"]
            or min(claimed, count_split, conservative_count) <= 0
            or max(claimed, count_split, conservative_count) > 500):
        raise CandidateRefused("Substantive word count not within conservative cap")
    disclosure = source.get("disclosure")
    if type(disclosure) is not str or not all(
        value in disclosure.casefold() for value in ("chatgpt", "codex", "third-party")
    ) or not all(value in text.casefold() for value in ("chatgpt", "codex", "third-party")):
        raise CandidateRefused("Missing disclosure parity")
    return {
        "schema": SCHEMA, "status": "G103_BYTE_PARITY_AND_STRUCTURE_PASS_NOT_OFFICIAL",
        "source_profile": "G103_PINNED_PRIVATE_OWNER_REVIEW" if synthetic_test_profile is None
                          else "SYNTHETIC_TEST_PROFILE_ONLY",
        "source_sha256": s_sha, "skill_zip_sha256": z_sha, "pdf_sha256": p_sha,
        "skill_zip_member_count": len(nested), "proposal_question_count": len(questions),
        "declared_words": claimed, "whitespace_words": count_split,
        "conservative_token_words": conservative_count,
        "pdf_header_footer_only_checked": True,
        "pdf_visual_and_text_parity_independently_verified_here": False,
        "official_uliya_checker_executed": False,
        "native_nas_verified": False, "rights_and_license_approved": False,
        "devpost_submitted": False, "release_gate": "HOLD",
        "owner_private_text_or_paths_returned": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner-local G103 byte parity; NOT official checker")
    parser.add_argument("--bundle", type=Path, required=True,
                        help="Explicit owner-local G103 review bundle; never uploaded")
    args = parser.parse_args(argv)
    try:
        path = args.bundle
        if (path.is_symlink() or path.parent.is_symlink() or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_OUTER):
            raise CandidateRefused("Owner candidate path refused")
        result = inspect_owner_review_bundle(path.read_bytes())
    except (CandidateRefused, ValueError, OSError):
        result = {"schema": SCHEMA, "status": "G103_CANDIDATE_PARITY_REFUSED",
                  "official_uliya_checker_executed": False, "release_gate": "HOLD"}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] == "G103_BYTE_PARITY_AND_STRUCTURE_PASS_NOT_OFFICIAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
