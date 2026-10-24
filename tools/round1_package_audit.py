"""OFFLINE UGREEN Round 1 Markdown preflight, never the official Uliya validator.
This development-only Python file is never bundled into the submission.
"""
import argparse
import io
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

MAX_BYTES = 10 * 1024 * 1024
MAX_FILE = 1024 * 1024
MAX_FILES = 100
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REF = re.compile(r"\]\((references/[^)#?\s]+\.md)\)")
SECRET = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA|EC|OPENSSH) PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}")
UNFINISHED = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.I)


class PackageError(ValueError):
    pass


def safe_relative(value: str) -> bool:
    return (bool(value) and value == PurePosixPath(value).as_posix()
            and all(x not in ("", ".", "..") for x in value.split("/"))
            and not value.startswith("/") and "\\" not in value)


def audit_skill(directory: Path) -> dict:
    folder = Path(directory)
    if not folder.is_dir() or folder.is_symlink():
        raise PackageError("Must supply a real non-symlink Skill folder")
    if not NAME.fullmatch(folder.name) or not 2 <= len(folder.name) <= 64:
        raise PackageError("Invalid lowercase/hyphenated 2–64 character Skill name")
    payload = {}
    for base, dirs, names in os.walk(folder, followlinks=False):
        for n in dirs + names:
            if (Path(base) / n).is_symlink():
                raise PackageError("Symlinks forbidden")
        for n in names:
            item = Path(base) / n
            rel = item.relative_to(folder).as_posix()
            if not safe_relative(rel):
                raise PackageError(f"Noncanonical file path: {rel}")
            if rel != "SKILL.md" and not (rel.startswith("references/") and rel.endswith(".md")):
                raise PackageError(f"Unsupported ZIP entry: {rel}")
            if not item.is_file():
                raise PackageError(f"Nonregular file: {rel}")
            data = item.read_bytes()
            if len(data) > MAX_FILE:
                raise PackageError(f"File exceeds 1MB: {rel}")
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PackageError(f"Invalid UTF-8: {rel}") from exc
            if SECRET.search(text) or UNFINISHED.search(text):
                raise PackageError(f"Possible secret/unfinished content: {rel}")
            payload[rel] = data
    if "SKILL.md" not in payload:
        raise PackageError("SKILL.md missing")
    if len(payload) > MAX_FILES or sum(map(len, payload.values())) > MAX_BYTES:
        raise PackageError("File count or uncompressed size limit exceeded")
    doc = payload["SKILL.md"].decode("utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", doc, re.S)
    if not match:
        raise PackageError("Frontmatter missing")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise PackageError("Malformed frontmatter")
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k in fields:
            raise PackageError("Duplicate frontmatter field")
        fields[k] = v
    if fields.get("name") != folder.name:
        raise PackageError("Frontmatter Skill name does not match folder")
    if not 1 <= len(fields.get("description", "")) <= 1024:
        raise PackageError("Description must be 1–1024 characters")
    links = REF.findall(doc)
    if len(links) != len(set(links)) or set(links) != set(payload) - {"SKILL.md"}:
        raise PackageError("Each reference must be directly linked once from SKILL.md")
    if not all(safe_relative(p) for p in links):
        raise PackageError("Unsafe reference")
    if "references/attribution.md" not in payload:
        raise PackageError("Attribution reference missing")
    disclosure = payload["references/attribution.md"].decode("utf-8")
    for heading in ("AI Tools", "Third-Party Components", "Data Flow"):
        if heading not in disclosure:
            raise PackageError(f"Disclosure section missing: {heading}")
    return {"name": folder.name, "file_count": len(payload), "files": sorted(payload),
            "uncompressed_bytes": sum(map(len, payload.values())),
            "official_validator": "NOT_RUN"}


def build_candidate_zip(folder: Path) -> bytes:
    report = audit_skill(folder)
    folder = Path(folder)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for rel in report["files"]:
            item = zipfile.ZipInfo(f"{folder.name}/{rel}", (1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            out.writestr(item, (folder / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = buffer.getvalue()
    if len(data) > MAX_BYTES:
        raise PackageError("Compressed ZIP exceeds 10MB")
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="OFFLINE preflight, not official Uliya validation")
    parser.add_argument("--skill-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Explicit opt-in LOCAL draft ZIP, not validated for Devpost")
    args = parser.parse_args(argv)
    try:
        r = audit_skill(args.skill_dir)
        if args.output:
            data = build_candidate_zip(args.skill_dir)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(data)
            print(f"Candidate ZIP written: {len(data)} bytes, official validator NOT_RUN")
        print(f"OFFLINE PREFLIGHT PASS: {r['file_count']} files; official validator NOT_RUN")
        return 0
    except (PackageError, OSError) as exc:
        print(f"OFFLINE PREFLIGHT FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
