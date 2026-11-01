"""G154: portable owner-only G147 static artifact verifier and offline bundle builder.

Not the official Uliya Checker. Never calls networks, vendor code, NAS, or Devpost.
Only source code goes to public GitHub; private G147 bytes are read locally.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo, BadZipFile

BASE = "FlowPilot3_G147_RULES_ALIGNED_OWNER_REVIEW_NOT_SUBMITTED"
PDF = BASE + ".pdf"
ZIP = BASE + ".zip"
MANIFEST = "G147_OWNER_REVIEW_MANIFEST_NOT_SUBMITTED.json"
MEMBERS = {
    "flowpilot-3/SKILL.md": "1062bba52833e3bbbc5f020739f80d2dee1dc2f2b428016e342075525bf2bc6d",
    "flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md": "4fa2235bdc164334f3592b16a358986718fc49a057ba800e931f5f7fc5017f49",
    "flowpilot-3/references/SAFETY_AND_SCENARIOS.md": "baf04355555f689266b46ba0866c25a022003d79ae8ad3f9475eda0408cc6ad0",
}
PINS = {
    PDF: "bf5319f0b840747e53d3a84f78e4006bc932a4d5d2bd0671c9c43c6f3877b90f",
    ZIP: "d8c66b24000b6fb1f7ea8b0d69417febfc83128d935e9b8db33dd382bb9c64c1",
}
MAX_BYTES = {PDF: 1_000_000, ZIP: 10_000_000, MANIFEST: 64_000}
PACKAGE_FILES = ("verify_g147.py", "candidate/" + PDF,
                 "candidate/" + ZIP, "candidate/" + MANIFEST,
                 "RUN_VERIFY_G147.cmd", "README.txt")
BUNDLE_MANIFEST = "BUNDLE_INTEGRITY.json"
# G155: public, independently pinned hashes for the *previously distributed* G154
# runner, owner instructions and Windows launcher. Do NOT rely on the editable
# BUNDLE_INTEGRITY.json alone for executable/operational-file trust.
LEGACY_G154_VERIFIER_SHA256 = "9dc36fcaf425569dbe9d827c078babf6e0277daec9b5981526f45147a0e5d113"
TRUSTED_WINDOWS_LAUNCHER_SHA256 = "4a63f53c989a7b21ef35e2db84c29798b7607cb2894f25bd458015ac4a118796"
TRUSTED_OWNER_README_SHA256 = "61c949a4d9f7bccda439138f885c73bd7c2375a8ff0c45b14e9cc7cbb08001b8"


class Refused(ValueError):
    """Sanitized error without owner paths, content or credentials."""


def digest(blob: bytes) -> str:
    return sha256(blob).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _json(blob: bytes):
    try:
        return json.loads(blob.decode("utf-8"), object_pairs_hook=_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(Refused("NONFINITE_JSON")))
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise Refused("INVALID_JSON") from exc


def _file(folder: Path, filename: str) -> bytes:
    path = folder / filename
    if folder.is_symlink() or path.is_symlink() or not path.is_file():
        raise Refused("UNSAFE_OR_MISSING_OWNER_FILE")
    try:
        size = path.stat().st_size
        if not 0 < size <= MAX_BYTES[filename]:
            raise Refused("OWNER_SIZE_LIMIT")
        blob = path.read_bytes()
    except OSError as exc:
        raise Refused("OWNER_INPUT_UNAVAILABLE") from exc
    if not 0 < len(blob) <= MAX_BYTES[filename]:
        raise Refused("OWNER_SIZE_LIMIT")
    return blob


def verify_bytes(pdf: bytes, skill_zip: bytes, manifest: bytes, *, pdf_text=False) -> dict:
    if type(pdf_text) is not bool or any(type(x) is not bytes for x in (pdf, skill_zip, manifest)):
        raise Refused("INVALID_INPUT_TYPE")
    if (not 0 < len(pdf) <= MAX_BYTES[PDF] or not pdf.startswith(b"%PDF-")
            or b"%%EOF" not in pdf[-1024:]):
        raise Refused("INVALID_PDF")
    if not 0 < len(skill_zip) <= MAX_BYTES[ZIP] or not 0 < len(manifest) <= MAX_BYTES[MANIFEST]:
        raise Refused("INVALID_ARCHIVE_OR_MANIFEST_SIZE")
    if digest(pdf) != PINS[PDF] or digest(skill_zip) != PINS[ZIP]:
        raise Refused("EXACT_G147_PAIR_SHA_MISMATCH")
    data = _json(manifest)
    if (type(data) is not dict or data.get("schema") != "g147-exact-owner-review-v1"
            or data.get("release_gate") != "HOLD" or data.get("owner_review_only") is not True
            or any(data.get(key) is not False for key in (
                "first_party_checker_executed", "registered_uliya_expert_verified",
                "real_nas_verified", "devpost_submitted"))
            or type(data.get("substantive_english_word_count")) is not int
            or not 1 <= data["substantive_english_word_count"] <= 500
            or type(data.get("pdf_pages")) is not int or data["pdf_pages"] != 1
            or data.get("package_member_count") != 3):
        raise Refused("RELEASE_METADATA_NOT_VERIFIED")
    a = data.get("artifacts")
    if type(a) is not dict or set(a) != {PDF, ZIP}:
        raise Refused("PAIR_MANIFEST_MISSING")
    for filename, blob in ((PDF, pdf), (ZIP, skill_zip)):
        x = a[filename]
        if (type(x) is not dict or set(x) != {"bytes", "sha256"}
                or type(x["bytes"]) is not int or x["bytes"] != len(blob)
                or x["sha256"] != digest(blob)):
            raise Refused("PAIR_MANIFEST_DRIFT")
    try:
        with ZipFile(BytesIO(skill_zip)) as z:
            infos = z.infolist()
            if len(infos) != 3 or set(x.filename for x in infos) != set(MEMBERS):
                raise Refused("INVALID_MARKDOWN_MEMBERS")
            blobs = {}
            for info in infos:
                if (info.is_dir() or info.flag_bits & 1
                        or stat.S_ISLNK(info.external_attr >> 16)
                        or not 0 < info.file_size <= 1_000_000):
                    raise Refused("UNSAFE_MEMBER")
                item = z.read(info)
                if digest(item) != MEMBERS[info.filename]:
                    raise Refused("MARKDOWN_SHA_MISMATCH")
                blobs[info.filename] = item
            if z.testzip() is not None or sum(map(len, blobs.values())) > 10_000_000:
                raise Refused("ZIP_CRC_OR_LIMIT_FAILED")
    except (BadZipFile, RuntimeError, EOFError, OverflowError, OSError) as exc:
        raise Refused("CORRUPT_ZIP") from exc
    records = data.get("package_members")
    if (type(records) is not list or len(records) != 3
            or any(type(x) is not dict or set(x) != {"name", "bytes", "sha256"}
                   or type(x["name"]) is not str or type(x["bytes"]) is not int
                   or type(x["sha256"]) is not str for x in records)
            or {x["name"]: (x["bytes"], x["sha256"]) for x in records}
            != {n: (len(blob), digest(blob)) for n, blob in blobs.items()}):
        raise Refused("MARKDOWN_MANIFEST_DRIFT")
    try:
        text = blobs["flowpilot-3/SKILL.md"].decode("utf-8")
        for name, raw in blobs.items():
            raw.decode("utf-8")
            if name != "flowpilot-3/SKILL.md" and f"]({name.removeprefix('flowpilot-3/')})" not in text:
                raise Refused("UNLINKED_REFERENCE")
    except UnicodeError as exc:
        raise Refused("NON_UTF8_MARKDOWN") from exc
    if not re.match(r"\A---\r?\nname: flowpilot-3\r?\ndescription: [^\r\n]{1,1024}\r?\n---\r?\n", text):
        raise Refused("INVALID_SKILL_FRONTMATTER")
    if not all(word in text.casefold() for word in
               ("hackathon-original", "chatgpt", "third-party", "registered", "rights check")):
        raise Refused("DISCLOSURE_MISSING")
    checked_pdf_text = False
    if pdf_text:
        try:
            import fitz
            with fitz.open(stream=pdf, filetype="pdf") as doc:
                if doc.needs_pass or doc.page_count != 1:
                    raise Refused("PDF_LOCKED_OR_MULTIPAGE")
                content = doc[0].get_text(sort=True)
                first, last = content.find("1. What does"), content.find("Disclosures (excluded")
                if first < 0 or last <= first:
                    raise Refused("PDF_QUESTION_BLOCK_MISSING")
                section = content[first:last]
                questions = [int(m.group(1)) for m in re.finditer(r"(?m)^([1-9]|10)\.\s+\S+", section)]
                if questions != list(range(1, 11)) or len(section.split()) > 500:
                    raise Refused("PDF_QUESTION_COUNT_OR_WORD_LIMIT")
                if "UGREEN Uliya/UGOS" not in content or "ChatGPT" not in content:
                    raise Refused("PDF_DISCLOSURE_MISSING")
            checked_pdf_text = True
        except ImportError as exc:
            raise Refused("PDF_TEXT_REQUIRES_PYMUPDF") from exc
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            raise Refused("PDF_TEXT_UNVERIFIED") from exc
    return {"status": "EXACT_G147_OFFLINE_PAIR_PASS_NOT_OFFICIAL",
            "pdf_sha256": digest(pdf), "skill_zip_sha256": digest(skill_zip),
            "pdf_text_verified": checked_pdf_text, "markdown_members": 3,
            "official_checker_executed": False, "nas_verified": False,
            "devpost_submitted": False, "release_gate": "HOLD"}


def verify_folder(folder: Path, *, pdf_text=False) -> dict:
    if not folder.is_dir() or folder.is_symlink():
        raise Refused("OWNER_FOLDER_UNAVAILABLE")
    return verify_bytes(_file(folder, PDF), _file(folder, ZIP), _file(folder, MANIFEST),
                        pdf_text=pdf_text)


def _zip_entry(z: ZipFile, name: str, blob: bytes):
    info = ZipInfo(name, (2026, 10, 31, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    z.writestr(info, blob)


def verify_package(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) < 500_000:
        raise Refused("PACKAGE_SIZE")
    try:
        with ZipFile(BytesIO(raw)) as z:
            infos = z.infolist()
            expected = set(PACKAGE_FILES) | {BUNDLE_MANIFEST}
            if len(infos) != len(expected) or set(x.filename for x in infos) != expected:
                raise Refused("PACKAGE_MEMBERS_INVALID")
            if (z.testzip() is not None or any(x.is_dir() or x.flag_bits & 1 or
                    stat.S_ISLNK(x.external_attr >> 16) or x.file_size > 100_000 for x in infos)):
                raise Refused("PACKAGE_UNSAFE")
            parts = {name: z.read(name) for name in expected}
    except (BadZipFile, RuntimeError, EOFError, OSError) as exc:
        raise Refused("PACKAGE_CORRUPT") from exc
    recorded = _json(parts[BUNDLE_MANIFEST])
    if (type(recorded) is not dict or recorded.get("release_gate") != "HOLD"
            or recorded.get("schema") != "g154-owner-offline-bundle-v1"
            or type(recorded.get("sha256")) is not dict
            or set(recorded["sha256"]) != set(PACKAGE_FILES)):
        raise Refused("BUNDLE_MANIFEST_INVALID")
    for name in PACKAGE_FILES:
        if recorded["sha256"][name] != digest(parts[name]):
            raise Refused("BUNDLE_INTEGRITY_MISMATCH")
    # A forged bundle can rewrite both a malicious runner and the SHA map.
    # Verify executable and instruction bytes against an external trust anchor:
    # the already-approved G154 runner or THIS trusted checkout's source.
    # Running this check from an untrusted, already-modified runner cannot
    # authenticate itself; owners should run it from the trusted repo.
    try:
        checkout_verifier_sha = digest(Path(__file__).read_bytes())
    except OSError as exc:
        raise Refused("TRUSTED_CHECKOUT_SOURCE_UNAVAILABLE") from exc
    if digest(parts["verify_g147.py"]) not in (
            LEGACY_G154_VERIFIER_SHA256, checkout_verifier_sha):
        raise Refused("BUNDLE_RUNNER_NOT_TRUSTED")
    if digest(parts["RUN_VERIFY_G147.cmd"]) != TRUSTED_WINDOWS_LAUNCHER_SHA256:
        raise Refused("BUNDLE_WINDOWS_LAUNCHER_NOT_TRUSTED")
    if digest(parts["README.txt"]) != TRUSTED_OWNER_README_SHA256:
        raise Refused("BUNDLE_INSTRUCTIONS_NOT_TRUSTED")
    pair = verify_bytes(parts["candidate/" + PDF], parts["candidate/" + ZIP],
                        parts["candidate/" + MANIFEST])
    return {"status": "G154_OWNER_OFFLINE_BUNDLE_VERIFIED_NOT_SUBMITTED",
            "bundle_sha256": digest(raw), "candidate_verified": pair["status"],
            "official_checker_executed": False, "release_gate": "HOLD"}


def build(folder: Path, output: Path, *, pdf_text=False) -> dict:
    pair = verify_folder(folder, pdf_text=pdf_text)
    script = Path(__file__).read_bytes()
    # Fixed archive entries. No vendor kit, hidden folder, arbitrary files or scripts from owner.
    contents = {
        "verify_g147.py": script,
        "candidate/" + PDF: _file(folder, PDF),
        "candidate/" + ZIP: _file(folder, ZIP),
        "candidate/" + MANIFEST: _file(folder, MANIFEST),
        "RUN_VERIFY_G147.cmd": (
            "@echo off\r\ncd /d \"%~dp0\"\r\n"
            "python verify_g147.py --verify-folder \"%~dp0candidate\"\r\n"
            "exit /b %ERRORLEVEL%\r\n").encode("ascii"),
        "README.txt": (
            "G154 owner-only OFFLINE G147 artifact audit. NOT a Devpost Skill ZIP.\n"
            "Unzip locally and double-click RUN_VERIFY_G147.cmd (requires Python 3.11+).\n"
            "Checks SHA256, three Markdown members, manifest and read-only HOLD; no network.\n"
            "Optional: python verify_g147.py --verify-folder candidate --pdf-text (PyMuPDF).\n"
            "Real Uliya Checker, NAS, Expert, entrant rights and Devpost NOT VERIFIED.\n"
            "Do not submit this outer ZIP. Only separately approved official PDF + Skill ZIP.\n"
        ).encode("utf-8"),
    }
    metadata = {"schema": "g154-owner-offline-bundle-v1", "release_gate": "HOLD",
                "sha256": {k: digest(contents[k]) for k in sorted(contents)}}
    stream = BytesIO()
    with ZipFile(stream, "w") as z:
        for name in PACKAGE_FILES:
            _zip_entry(z, name, contents[name])
        _zip_entry(z, BUNDLE_MANIFEST, (json.dumps(metadata, sort_keys=True, indent=2)+"\n").encode())
    blob = stream.getvalue()
    verify_package(blob)
    if output.exists() or output.is_symlink() or not output.parent.is_dir() or output.parent.is_symlink():
        raise Refused("OUTPUT_EXISTS_OR_UNSAFE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(output, flags, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
    except FileExistsError as exc:
        raise Refused("OUTPUT_EXISTS_OR_UNSAFE") from exc
    except OSError as exc:
        raise Refused("OUTPUT_UNAVAILABLE") from exc
    return {"status": "G154_PRIVATE_OFFLINE_PACKAGE_BUILT_NOT_SUBMITTED",
            "bundle_sha256": digest(blob), "bytes": len(blob),
            "candidate_verified": pair["status"], "pdf_text_verified": pair["pdf_text_verified"],
            "vendor_kit_included": False, "network_used": False,
            "official_checker_executed": False, "devpost_submitted": False, "release_gate": "HOLD"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G154 local owner G147 private offline audit bundle. NEVER official Uliya Checker")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-folder", type=Path)
    mode.add_argument("--verify-package", type=Path)
    mode.add_argument("--build", type=Path, metavar="OWNER_FOLDER")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pdf-text", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verify_folder is not None:
            if args.output: raise Refused("UNEXPECTED_OUTPUT")
            result = verify_folder(args.verify_folder, pdf_text=args.pdf_text)
        elif args.verify_package is not None:
            if args.output or args.pdf_text: raise Refused("UNEXPECTED_FLAG")
            path = args.verify_package
            if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 500_000:
                raise Refused("UNSAFE_PACKAGE_INPUT")
            result = verify_package(path.read_bytes())
        else:
            if args.output is None: raise Refused("OUTPUT_REQUIRED")
            result = build(args.build, args.output, pdf_text=args.pdf_text)
        rc = 0
    except (Refused, OSError, ValueError, RuntimeError) as exc:
        result = {"status": "G154_OFFLINE_OWNER_CHECK_REFUSED", "reason": type(exc).__name__,
                  "official_checker_executed": False, "release_gate": "HOLD"}
        rc = 2
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
