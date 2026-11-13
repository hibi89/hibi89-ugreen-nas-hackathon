"""Offline, explicit-owner checklist editor for schema-v1 delivery manifests.

A scanned source folder must NEVER be used as its own requirements authority.
This builder parses an independently supplied contractual list; it neither
discovers source files nor reads their contents. No network, implicit approval,
or overwrite.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

from .engine import InputError, MAX_FILES, MANIFEST_LIMIT, _is_link, _relative, create_only

MAX_INPUT = 750_000


def parse_checklist(text: str) -> list[dict[str, str | None]]:
    """One relative POSIX path per line; optional tab + expected SHA-256.

    Spaces in filenames are meaningful. Blank lines or comments beginning with
    # after optional leading spaces are omitted. Duplicate/casefold collisions,
    path traversal and invalid Windows device names fail closed.
    """
    if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > MAX_INPUT:
        raise InputError("checklist is empty or exceeds 750 KB")
    seen: set[str] = set()
    result: list[dict[str, str | None]] = []
    for index, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        tokens = raw.split("\t")
        if len(tokens) > 2:
            raise InputError(f"line {index}: only a path and optional tab-separated SHA256 are permitted")
        relative = _relative(tokens[0])
        if relative.casefold() in seen:
            raise InputError(f"line {index}: duplicate or case-colliding requirement")
        seen.add(relative.casefold())
        digest = tokens[1].strip() if len(tokens) == 2 else ""
        if digest and not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise InputError(f"line {index}: SHA256 requires 64 hex characters")
        result.append({"path": relative, "sha256": digest.lower() if digest else None})
        if len(result) > MAX_FILES:
            raise InputError("checklist exceeds safe 20,000-file limit")
    if not result:
        raise InputError("checklist must contain at least one file")
    return result


def render_manifest(title: str, text: str, *, approved: bool = False) -> str:
    if approved is not True:
        raise InputError("operator must independently approve the checklist before creating a usable manifest")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
        raise InputError("manifest title must have 1..160 characters")
    entries = parse_checklist(text)
    doc = {"schema_version": 1, "title": title.strip(), "expected_files": entries}
    body = json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if len(body.encode("utf-8")) > MANIFEST_LIMIT:
        raise InputError("manifest exceeds engine size limit")
    return body


def create_approved_manifest(title: str, checklist: str, destination: Path,
                             root: Path, *, approved: bool = False) -> Path:
    """Create-only, schema-v1 JSON outside the inspected folder.

    The original root is never read beyond resolving its directory path.
    """
    if not root.is_dir() or _is_link(root.lstat()):
        raise InputError("select a real authorized non-reparse source directory first")
    if destination.suffix.lower() != ".json":
        raise InputError("requirements manifest destination must end in .json")
    body = render_manifest(title, checklist, approved=approved)
    create_only(destination, body, root)
    return destination
