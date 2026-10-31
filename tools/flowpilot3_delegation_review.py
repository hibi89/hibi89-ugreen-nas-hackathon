"""G99: local candidate workflow integrity review. NOT the Uliya official Checker.

Read-only; no NAS, Expert, network, source writes, authorization or publication.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

MODES = ("CHECK_REQUIRED", "REVIEW_VERSIONS", "HANDOFF_AUDIT", "SUMMARIZE_SELECTED")
MAX_BYTES = 1_000_000


def review_source(raw: bytes) -> dict:
    issues = []
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        return {"status": "STRUCTURAL_HOLD", "issues": ["INVALID_SIZE_OR_TYPE"],
                "official_checker_executed": False, "release_gate": "HOLD"}
    digest = sha256(raw).hexdigest()
    try:
        doc = raw.decode("utf-8")
    except UnicodeError:
        return {"status": "STRUCTURAL_HOLD", "skill_sha256": digest, "issues": ["INVALID_UTF8"],
                "official_checker_executed": False, "release_gate": "HOLD"}
    if not re.match(r"\A---\r?\nname: flowpilot-3\r?\ndescription: .+\r?\n---\r?\n", doc):
        issues.append("UNEXPECTED_SKILL_ID_OR_FRONTMATTER")
    if re.search(r"<include\b|<\s*insert\b|\b(?:TODO|TBD|FIXME)\b", doc, re.I):
        issues.append("UNBOUND_INSTRUCTION_PLACEHOLDER")
    sections = doc.split("# Orchestration", 1)
    if len(sections) != 2:
        issues.append("MISSING_ORCHESTRATION")
    else:
        section = sections[1].split("# Result classification", 1)[0]
        match = re.search(r"(?ms)^2\.\s*(.*?)(?=^3\.|\Z)", section)
        first = match.group(1) if match else ""
        if not first or "file-agent" not in first or "delegate" not in first.lower() or any(m not in first for m in MODES):
            issues.append("SUMMARY_MISSING_FILE_AGENT_INVENTORY")
        if "document-agent" not in section or "file-agent" not in section:
            issues.append("MISSING_DELEGATION_CHAIN")
        if not all(k in section.lower() for k in ("consent", "scope", "reference")):
            issues.append("MISSING_STAGE_BINDING_GUARDS")
        if "sha256sum" in doc and "separate" not in section.lower():
            issues.append("HASHING_CONSENT_NOT_EXPLICIT")
    return {"status": "STRUCTURAL_PASS_OFFICIAL_CHECKER_REQUIRED" if not issues else "STRUCTURAL_HOLD",
            "skill_sha256": digest, "issues": issues, "official_checker_executed": False,
            "native_expert_invoked": False, "real_nas_verified": False,
            "owner_release_approved": False, "devpost_submitted": False, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G99 local-only structural gate; NOT official Uliya Checker")
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args(argv)
    p = args.candidate
    if p.is_symlink() or p.name != "SKILL.md" or not p.is_file() or p.stat().st_size > MAX_BYTES:
        report = {"status": "STRUCTURAL_HOLD", "issues": ["INVALID_CANDIDATE_PATH"],
                  "official_checker_executed": False, "release_gate": "HOLD"}
    else:
        report = review_source(p.read_bytes())
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "STRUCTURAL_PASS_OFFICIAL_CHECKER_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
