"""G57: inspect newly generated FlowPilot Skill bytes before human adoption.

Does not invoke the official Creator, certify its provenance, access NAS,
modify canonical artifacts, approve release or submit to Devpost.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Any

from g53_flowpilot_creator_gate import review_creator_evidence

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "skill/flowpilot-nas/SKILL.md"
PINNED_BASELINE_SHA = "47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"
MAX_FILE = 1_000_000
MAX_TOTAL = 10_000_000
MAX_FILES = 100
FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
LINK = re.compile(r"\]\((references/[a-z0-9][a-z0-9._-]*\.md)\)")
ALL_REFERENCE_LINKS = re.compile(r"\]\((references/[^)]*)\)")
SECRET = re.compile(
    r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|"
    r"-----BEGIN (?:RSA|EC|OPENSSH) PRIVATE KEY-----|"
    r"xox[baprs]-[A-Za-z0-9-]{16,}"
)
UNFINISHED = re.compile(r"(?mi)^\s*(?:TODO|FIXME|TBD)\s*[:\-]")
SUPPORTED_CANDIDATE_NAMES = frozenset(("flowpilot-nas", "flowpilot-3"))
CANONICAL_NAME = "flowpilot-nas"

FEATURE_SIGNALS = (
    "HANDOFF_AUDIT", "CHECK_REQUIRED", "REVIEW_VERSIONS", "SUMMARIZE_SELECTED",
    "file-agent", "document-agent", "NOT_CHECKED", "VERSION_REVIEW",
)


class CandidateError(ValueError):
    """Unsafe or structurally unreviewable candidate; no source included."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def inspect_candidate(
    directory: Path, baseline: bytes, receipt: Mapping[str, Any] | None = None
) -> dict:
    """Return a sanitized local structure/source-diff report, always HOLD."""
    folder = Path(directory)
    if folder.name not in SUPPORTED_CANDIDATE_NAMES or folder.is_symlink() or not folder.is_dir():
        raise CandidateError("Use a real, explicitly supported FlowPilot candidate folder without symlinks")
    if folder.parent.is_symlink():
        raise CandidateError("Parent path is a symlink")
    if not isinstance(baseline, bytes) or not baseline:
        raise CandidateError("Missing reviewed baseline source")
    payload: dict[str, bytes] = {}
    for path in folder.rglob("*"):
        if path.is_symlink():
            raise CandidateError("Symlink in generated Skill directory")
        relative = path.relative_to(folder).as_posix()
        if path.is_dir():
            if relative != "references":
                raise CandidateError("Unexpected nested directory")
            continue
        if not path.is_file():
            raise CandidateError("Nonregular generated member")
        if relative != "SKILL.md" and not re.fullmatch(r"references/[a-z0-9][a-z0-9._-]*\.md", relative):
            raise CandidateError("Unsupported generated member: only Markdown references allowed")
        if path.stat().st_size > MAX_FILE:
            raise CandidateError("Generated member exceeds 1MB")
        raw = path.read_bytes()
        if len(raw) > MAX_FILE:
            raise CandidateError("Generated member exceeds 1MB")
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CandidateError("Invalid UTF-8 generated member") from exc
        if SECRET.search(decoded) or UNFINISHED.search(decoded):
            raise CandidateError("Sensitive or unfinished generated text")
        payload[relative] = raw
        if len(payload) > MAX_FILES or sum(map(len, payload.values())) > MAX_TOTAL:
            raise CandidateError("Generated Skill exceeds file or size budget")
    if "SKILL.md" not in payload:
        raise CandidateError("Generated SKILL.md missing")
    skill = payload["SKILL.md"]
    doc = skill.decode("utf-8")
    front = FRONT.match(doc)
    if front is None:
        raise CandidateError("Missing Skill frontmatter")
    metadata: dict[str, str] = {}
    for line in front.group(1).splitlines():
        if ":" not in line:
            raise CandidateError("Malformed frontmatter")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if key in metadata:
            raise CandidateError("Duplicate frontmatter field")
        metadata[key] = value
    if metadata.get("name") != folder.name:
        raise CandidateError("Generated Skill name must match its exact candidate directory")
    if not 1 <= len(metadata.get("description", "")) <= 1024:
        raise CandidateError("Invalid generated description length")
    references = LINK.findall(doc)
    raw_references = ALL_REFERENCE_LINKS.findall(doc)
    if len(references) != len(raw_references) or len(references) != len(set(references)):
        raise CandidateError("Unsafe or repeated reference Markdown link")
    if set(references) != set(payload) - {"SKILL.md"}:
        raise CandidateError("Reference files and direct links mismatch")
    old_lines = baseline.decode("utf-8").splitlines()
    new_lines = doc.splitlines()
    diff = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    added = removed = 0
    for tag, a0, a1, b0, b1 in diff.get_opcodes():
        if tag in ("replace", "insert"):
            added += b1 - b0
        if tag in ("replace", "delete"):
            removed += a1 - a0
    missing = [signal for signal in FEATURE_SIGNALS if signal.casefold() not in doc.casefold()]
    missing_disclosure = [
        x for x in ("third-party", "AI", "data flow")
        if x.casefold() not in doc.casefold()
        and not any(x.casefold() in raw.decode("utf-8").casefold() for raw in payload.values())
    ]
    declaration = review_creator_evidence(skill, receipt)
    canonical_identity = metadata["name"] == CANONICAL_NAME
    return {
        "status": ("SOURCE_DIFF_IDENTITY_REVIEW_REQUIRED" if not canonical_identity
                   else "SOURCE_MATCHED_HUMAN_PROVENANCE_REVIEW"
                   if digest(skill) == digest(baseline)
                   else "SOURCE_DIFF_HUMAN_REVIEW_REQUIRED"),
        "candidate": metadata["name"],
        "canonical_candidate": CANONICAL_NAME,
        "canonical_identity_matches": canonical_identity,
        "candidate_adoption_approved": False,
        "operator_receipt_gate_scope": "flowpilot-nas-only",
        "skill_sha256": digest(skill),
        "baseline_sha256": digest(baseline),
        "source_matches_baseline": skill == baseline,
        "added_lines": added,
        "removed_lines": removed,
        "markdown_file_count": len(payload),
        "reference_count": len(references),
        "uncompressed_bytes": sum(map(len, payload.values())),
        "missing_design_signals_for_owner_review": missing,
        "missing_disclosure_signals_for_owner_review": missing_disclosure,
        "operator_receipt_status": declaration["status"],
        "creator_execution_independently_verified": False,
        "first_party_checker_independently_verified_on_generated_source": False,
        "actual_nas_verified": False,
        "entrant_release_approved": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only review of generated FlowPilot")
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--operator-receipt", type=Path)
    args = parser.parse_args()
    try:
        if BASELINE.is_symlink() or not BASELINE.is_file():
            raise CandidateError("Canonical baseline unavailable")
        baseline = BASELINE.read_bytes()
        if digest(baseline) != PINNED_BASELINE_SHA:
            raise CandidateError("Baseline SHA drift requires independent review")
        receipt = None
        if args.operator_receipt is not None:
            p = args.operator_receipt
            if p.is_symlink() or not p.is_file() or p.stat().st_size > 10_000:
                raise CandidateError("Invalid operator receipt")
            receipt = json.loads(p.read_text(encoding="utf-8"))
        report = inspect_candidate(args.candidate_dir, baseline, receipt)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        # 0 means inspection complete; the report always withholds release.
        return 0
    except (CandidateError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "CANDIDATE_INSPECTION_REFUSED",
                          "reason_category": type(exc).__name__,
                          "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
