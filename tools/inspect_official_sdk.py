#!/usr/bin/env python3
"""Inspect OFFICIAL PUBLIC UGREEN creation-tool ZIP as EPHEMERAL, READ-ONLY DATA.

Only bounded, non-content package metadata appears in logs. Does not extract files,
execute package content, write artifacts, reveal doc text, or endorse archive license.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import stat
import sys
import urllib.parse
import urllib.request
import zipfile

MAX_DOWNLOAD = 20 * 1024 * 1024
MAX_UNCOMPRESSED = 64 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_MEMBERS = 1000
ALLOWED_HOST = "cdn.shopify.com"
KNOWN_DOC_SUFFIXES = (".md", ".txt", ".yaml", ".yml", ".json")
DOC_KEYWORDS = ("cli", "agent", "reference", "validate", "check", "skill")

class UnsafePackage(ValueError):
    pass

def _safe_path(name: str) -> None:
    if not name or "\\" in name or name.startswith("/") or ":" in name.split("/")[0]:
        raise UnsafePackage("unsafe member name")
    if any(p in (".", "..") for p in name.strip("/").split("/")):
        raise UnsafePackage("relative path traversal")
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise UnsafePackage("control character in member path")

def inspect_zip_bytes(binary: bytes) -> dict:
    if not binary or len(binary) > MAX_DOWNLOAD:
        raise UnsafePackage("download empty/too large")
    try:
        archive = zipfile.ZipFile(io.BytesIO(binary), "r")
    except zipfile.BadZipFile as exc:
        raise UnsafePackage("download is not a valid ZIP") from exc
    with archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise UnsafePackage("too many archive entries")
        total = 0
        docs = 0
        caps = {word: False for word in DOC_KEYWORDS}
        found_license = False
        file_extension_counts: dict[str, int] = {}
        for member in members:
            _safe_path(member.filename)
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise UnsafePackage("archive contains symlink")
            if member.flag_bits & 0x1:
                raise UnsafePackage("encrypted archive member")
            if member.file_size > MAX_FILE:
                raise UnsafePackage("oversized member")
            total += member.file_size
            if total > MAX_UNCOMPRESSED:
                raise UnsafePackage("uncompressed size exceeds inspection limit")
            name = member.filename.lower()
            if member.is_dir():
                continue
            ext = "." + name.rsplit(".", 1)[-1] if "." in name else "(none)"
            file_extension_counts[ext] = file_extension_counts.get(ext, 0) + 1
            if name.endswith(KNOWN_DOC_SUFFIXES):
                docs += 1
                for word in caps:
                    if word in name:
                        caps[word] = True
            if name.endswith(("license", "license.md", "license.txt", "copying", "copying.md")):
                found_license = True
        return {
            "inspection": "OFFICIAL_ARCHIVE_METADATA_ONLY",
            "sha256": hashlib.sha256(binary).hexdigest(),
            "zip_bytes": len(binary),
            "file_count": sum(not m.is_dir() for m in members),
            "document_filename_count": docs,
            "uncompressed_total_bytes": total,
            "license_filename_present": found_license,
            "documentation_filename_keywords_present": caps,
            "extension_counts": dict(sorted(file_extension_counts.items())),
            "no_content_or_source_printed": True,
            "cli_signatures_verified": False,
            "registered_agents_verified": False,
            "official_validator_executed": False,
            "real_nas_executed": False
        }

def download_public_official_zip(url: str) -> bytes:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise UnsafePackage("only official CDN host allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "UGREEN-Hackathon-Verification/1.0"})
    with urllib.request.urlopen(request, timeout=35) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != ALLOWED_HOST:
            raise UnsafePackage("unexpected external redirect")
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise UnsafePackage("download limit exceeded")
    return data

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--official-url", required=True)
    args = p.parse_args()
    try:
        archive = download_public_official_zip(args.official_url)
        print(json.dumps(inspect_zip_bytes(archive), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        # Never log ZIP data, request credentials, or arbitrary server error bodies.
        print(json.dumps({
            "inspection": "DOWNLOAD_OR_ARCHIVE_INSPECTION_FAILED",
            "exception_class": type(exc).__name__,
            "archive_bytes_saved": False,
            "cli_signatures_verified": False,
            "official_validator_executed": False,
            "requires_private_or_official_docs_fallback": True
        }, sort_keys=True))
        return 2

if __name__ == "__main__":
    sys.exit(main())
