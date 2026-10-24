"""Read-only inspection of a participant's new official-Creator Skill source.
Not the UGOS checker, not license clearance and never a Devpost submission.
Does not print private source, local paths or raw document content.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from round1_package_audit import REF, SECRET, UNFINISHED, safe_relative

EXPECTED_NAME = "projectready-nas"
LIMIT = 1024 * 1024

class CreatorReviewError(ValueError):
    pass

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def review(generated: Path, expected_sha256: str, baseline: Path) -> dict:
    generated = Path(generated)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise CreatorReviewError("Expected SHA-256 must be exactly 64 hex characters")
    if generated.name != "SKILL.md" or generated.is_symlink() or generated.parent.is_symlink():
        raise CreatorReviewError("Select a regular SKILL.md in a non-symlink Skill folder")
    if generated.parent.name != EXPECTED_NAME or not generated.is_file():
        raise CreatorReviewError("Expected a projectready-nas/SKILL.md file")
    if generated.stat().st_size > LIMIT:
        raise CreatorReviewError("Generated source exceeds safe inspection limit")
    original = generated.read_bytes()
    actual_sha = digest(original)
    if actual_sha != expected_sha256.lower():
        raise CreatorReviewError("Generated SKILL.md SHA-256 differs from participant report")
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CreatorReviewError("Generated SKILL.md is not UTF-8") from exc
    front = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not front or not re.search(r"(?m)^name:\s*['\"]?projectready-nas['\"]?\s*$", front.group(1)):
        raise CreatorReviewError("Expected projectready-nas YAML frontmatter")
    refs = REF.findall(text)
    if len(refs) != len(set(refs)):
        raise CreatorReviewError("Duplicate direct Markdown reference")
    files = {}
    root = generated.parent
    for base, dirs, names in os.walk(root, followlinks=False):
        for item in dirs + names:
            if (Path(base) / item).is_symlink():
                raise CreatorReviewError("Symlinks are forbidden in generated Skill")
        for item in names:
            path = Path(base) / item
            relative = path.relative_to(root).as_posix()
            if relative != "SKILL.md" and (not safe_relative(relative)
                    or not relative.startswith("references/") or not relative.endswith(".md")):
                raise CreatorReviewError("Only SKILL.md and references/*.md may be reviewed")
            if not path.is_file() or path.stat().st_size > LIMIT:
                raise CreatorReviewError("Unreviewable or oversized Markdown file")
            data = path.read_bytes()
            try:
                content = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CreatorReviewError("Reference is not UTF-8") from exc
            if SECRET.search(content) or UNFINISHED.search(content):
                raise CreatorReviewError("Potential secret or unfinished placeholder in Markdown")
            files[relative] = digest(data)
    if set(files) != {"SKILL.md"} | set(refs):
        raise CreatorReviewError("Reference links and included Markdown files disagree")
    if not baseline.is_file():
        raise CreatorReviewError("Repository baseline SKILL.md unavailable")
    baseline_sha = digest(baseline.read_bytes())
    return {
        "assessment": "LOCAL_SOURCE_INTEGRITY_REVIEW_PASS_ONLY",
        "file_sha256": actual_sha,
        "baseline_sha256": baseline_sha,
        "same_bytes_as_baseline": actual_sha == baseline_sha,
        "linked_markdown_files": len(files) - 1,
        "member_sha256": files,
        "official_creator_provenance": "PARTICIPANT_REPORTED_NOT_INDEPENDENTLY_PROVEN",
        "official_checker": "PARTICIPANT_REPORTED_NOT_RERUN",
        "nas_runtime": "NOT_RUN",
        "license_privacy_and_rights": "PENDING_REVIEW",
        "entrant_approval": "PENDING",
        "devpost_submission": "NOT_SUBMITTED"
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Private read-only Creator-source review")
    parser.add_argument("--generated-skill", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--baseline", type=Path,
                        default=Path(__file__).resolve().parents[1] / "skill/projectready-nas/SKILL.md")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(review(args.generated_skill, args.expected_sha256, args.baseline),
                         indent=2, sort_keys=True))
        return 0
    except (CreatorReviewError, OSError) as exc:
        print("CREATOR SOURCE REVIEW BLOCKED: " + str(exc), file=__import__("sys").stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
