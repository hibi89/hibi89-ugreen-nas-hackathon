"""Read only a pinned first-party public UGREEN ZIP in an ephemeral GitHub runner.

This is a bounded semantic INDEX, not an SDK validator, installer, CLI execution,
license grant, or permission to redistribute kit text. Only file-level topic flags,
line numbers, safe literal agent labels, and first command tokens are printed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile

from inspect_official_sdk import download_public_official_zip, inspect_zip_bytes, UnsafePackage

EXPECTED_SHA256 = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
TOPICS = {
    "registered_agent": re.compile(r"\b(?:registered|available|expert)\s+agents?\b", re.I),
    "cli": re.compile(r"\b(?:UGOS\s+CLI|Uliya\s+CLI|command[\s-]line)\b", re.I),
    "permissions": re.compile(r"\b(?:permission|authorization|consent|access\s+control)\b", re.I),
    "validation": re.compile(r"\b(?:validat(?:e|ion|or)|creation[\s-]tool\s+check)\b", re.I),
    "license": re.compile(r"\blicen[sc]e\b", re.I),
    "files": re.compile(r"\b(?:file\s+search|file\s+listing|browse\s+files|find\s+files)\b", re.I),
    "documents": re.compile(r"\b(?:document\s+reading|document\s+agent|extract\s+text)\b", re.I),
}
AGENT_LABEL = re.compile(r"\b(Files|Documents|Knowledge|Albums|Video|Music)\s+(Expert\s+)?Agent\b", re.I)
CLI_TOKEN = re.compile(r"^\s*(?:\$\s*)?(?P<entry>ugos|uliya|skill-creator|skill_creator)\s+(?P<sub>[a-zA-Z][\w-]{1,40})", re.I)
MAX_LINES = 25000
MAX_FILES = 100
MAX_TOPIC_EVIDENCE = 3


def semantic_index(data: bytes, expected_sha: str = EXPECTED_SHA256) -> dict:
    meta = inspect_zip_bytes(data)
    if meta["sha256"] != expected_sha:
        raise UnsafePackage("Unexpected official kit SHA256; do not inspect changed version")
    summary = {"analysis": "EPHEMERAL_OFFICIAL_PUBLIC_KIT_BOUNDED_SEMANTIC_INDEX",
               "sha256": meta["sha256"],
               "archive_file_count": meta["file_count"],
               "metadata_only": False, "sdk_contents_redistributed": False,
               "license_grant_determined": False,
               "exact_cli_schema_verified": False,
               "registered_agent_registry_verified": False,
               "official_skill_validator_executed": False, "nas_test_executed": False,
               "documents": []}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".md", ".json", ".txt", ".mjs")):
                continue
            if len(summary["documents"]) >= MAX_FILES:
                raise UnsafePackage("too many text files")
            text = archive.read(info).decode("utf-8")
            lines = text.splitlines()
            if len(lines) > MAX_LINES:
                raise UnsafePackage("oversized text document")
            topics = {name: [] for name in TOPICS}
            labels = set()
            command_tokens = set()
            for index, line in enumerate(lines, 1):
                for name, regex in TOPICS.items():
                    if len(topics[name]) < MAX_TOPIC_EVIDENCE and regex.search(line):
                        topics[name].append(index)
                for m in AGENT_LABEL.finditer(line):
                    labels.add(m.group(0).lower().replace("  ", " "))
                match = CLI_TOKEN.match(line)
                if match:
                    command_tokens.add(" ".join((match["entry"].lower(), match["sub"].lower())))
            safe_name = info.filename
            if not re.fullmatch(r"[a-zA-Z0-9_./-]{1,180}", safe_name):
                raise UnsafePackage("filename outside safe report character set")
            summary["documents"].append({
                "path": safe_name,
                "bytes": info.file_size,
                "sha256_prefix": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
                "topic_line_numbers": {k: v for k, v in topics.items() if v},
                "agent_labels_mentioned_not_registry_proof": sorted(labels)[:12],
                "cli_command_prefix_candidates_not_runtime_proof": sorted(command_tokens)[:12],
            })
    return summary


def main() -> int:
    arg = argparse.ArgumentParser()
    arg.add_argument("--official-url", required=True)
    args = arg.parse_args()
    try:
        payload = download_public_official_zip(args.official_url)
        print(json.dumps(semantic_index(payload), sort_keys=True, indent=2))
        return 0
    except Exception as err:
        # No fetched content/stacktraces/third-party error messages in public logs.
        print(json.dumps({"analysis": "OFFICIAL_KIT_INDEX_FAILED",
                          "exception_type": type(err).__name__,
                          "original_archive_saved": False,
                          "exact_cli_schema_verified": False,
                          "license_grant_determined": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
