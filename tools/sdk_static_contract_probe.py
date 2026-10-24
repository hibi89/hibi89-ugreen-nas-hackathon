"""Bounded static-only structural scan of pinned official public Uliya kit.

No package execution, artifacts, sources, raw JSON, proprietary documentation or
literal user data are emitted. File paths and bounded interface-schema keys only.
"""
import argparse
import hashlib
import io
import json
import re
import zipfile

from inspect_official_sdk import download_public_official_zip, inspect_zip_bytes, UnsafePackage
from sdk_semantic_index import EXPECTED_SHA256

REQUIRED = ("uliya-skill-kit/scripts/check-skill.mjs",
            "uliya-skill-kit/scripts/check-lib.mjs",
            "uliya-skill-kit/data/capability-catalog.json",
            "uliya-skill-kit/docs/skill-development-standard.md")
DANGEROUS = {
    "child_process": re.compile(r"(?:child_process|\bspawn\s*\(|\bexecFile\s*\(|\bexecSync\s*\()", re.I),
    "network": re.compile(r"(?:node:https?|node:net|node:dns|\bfetch\s*\(|\bXMLHttpRequest\b)", re.I),
    "dynamic_code": re.compile(r"(?:\beval\s*\(|\bnew\s+Function\s*\(|\bimport\s*\()", re.I),
    "environment": re.compile(r"\bprocess\.env\b", re.I),
    "shell": re.compile(r"(?:/bin/sh|bash\s+-c|powershell\.exe|\bsudo\b)", re.I),
}
MAX_BRANCHES = 6
MAX_ENTRIES = 12


def shape(value, depth=0):
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        keys = [k for k in value if re.fullmatch(r"[A-Za-z][\w-]{0,72}", k)]
        return {k: shape(value[k], depth+1) for k in keys[:MAX_ENTRIES]}
    if isinstance(value, list):
        return {"type": "array", "count": len(value), "first_shape": shape(value[0], depth+1) if value else None}
    return type(value).__name__


def static_probe(data: bytes, expected=EXPECTED_SHA256):
    metadata = inspect_zip_bytes(data)
    if metadata["sha256"] != expected:
        raise UnsafePackage("Pinned ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if not set(REQUIRED).issubset(archive.namelist()):
            raise UnsafePackage("Missing canonical verifier or catalog files")
        catalog = json.loads(archive.read(REQUIRED[2]).decode("utf-8"))
        scripts = [archive.read(path).decode("utf-8") for path in REQUIRED[:2]]
        risk = {name: any(pattern.search(code) for code in scripts) for name,pattern in DANGEROUS.items()}
        node_imports = []
        for code in scripts:
            node_imports.extend(re.findall(r"\b(?:import|from)\s*[('\"\s]*((?:node:)?[a-zA-Z0-9_./-]+)",code))
        safe_imports = sorted(set(x for x in node_imports if len(x) <= 70))[:MAX_ENTRIES]
        return {
            "inspection": "PINNED_OFFICIAL_ARCHIVE_STATIC_CONTRACT_SCAN",
            "official_sha256": expected,
            "canonical_paths": list(REQUIRED),
            "catalog_top_level_shape": shape(catalog),
            "checker_entrypoint_import_module_hints": safe_imports,
            "checker_source_risk_markers": risk,
            "checker_execution_safety_confirmed": False,
            "sdk_source_or_docs_republished": False,
            "license_scope_verified": False,
            "cli_and_agent_registry_verified": False,
            "sdk_checker_executed": False,
            "nas_runtime_executed": False,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-url", required=True)
    args = parser.parse_args()
    try:
        data = download_public_official_zip(args.official_url)
        print(json.dumps(static_probe(data),indent=2,sort_keys=True))
        return 0
    except Exception as ex:
        print(json.dumps({"inspection":"STATIC_PROBE_FAILED",
                          "exception_class":type(ex).__name__,
                          "sdk_checker_executed":False,"source_republished":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
