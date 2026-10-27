"""Minimal honest milestone gate, superseding legacy 10-file closeout noise.

Ordinary code/test/tool changes need verified commits and CI, but NOT
10 duplicate handoff edits. Canonical Skill change is a release-impacting
milestone and still needs STATUS/HANDOFF. Canonical progress JSON always
requires matching rendered dashboard. Never bypass approval or official tools.
"""
from __future__ import annotations
import argparse
import subprocess

REQUIRED = frozenset({"STATUS.md", "HANDOFF.md"})
HIGH_IMPACT = frozenset({"skill/flowpilot-nas/SKILL.md", "SKILL.md"})

def closeout_errors(changed: set[str]) -> list[str]:
    errors = []
    if "data/master_progress.json" in changed and "MASTER_PROGRESS.md" not in changed:
        errors.append("Canonical JSON changed without MASTER_PROGRESS.md")
    if changed & HIGH_IMPACT:
        for missing in sorted(REQUIRED - changed):
            errors.append("Canonical Skill changed without important handoff: " + missing)
    return errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    args = ap.parse_args()
    if not args.base.strip("0"):
        print("No previous head: manual review necessary")
        return 0
    diff = subprocess.run(
        ["git", "diff", "--name-only", args.base, args.head],
        check=True, capture_output=True, text=True
    )
    files = set(diff.stdout.splitlines())
    failures = closeout_errors(files)
    for item in failures:
        print(item)
    if failures:
        return 1
    print(f"Minimal milestone gate PASS; {len(files)} changed paths")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
