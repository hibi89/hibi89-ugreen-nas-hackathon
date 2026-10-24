"""CI check that feature pushes also update the GitHub live handoff.

This validates committed file paths only; it cannot prove the notes are truthful.
"""
from __future__ import annotations

import argparse
import subprocess

REQUIRED = frozenset({
    "docs/roles/lead/LIVE_HANDOFF.md",
    "docs/roles/lead/LIVE_STATE.json",
    "docs/roles/lead/LEAD_ACTIVE_WORK.md",
    "docs/roles/lead/DAILY_PROGRESS.md",
    "docs/roles/lead/DAILY_PROGRESS.json",
    "docs/roles/lead/STATUS.md",
    "docs/roles/lead/HANDOFF.md",
    "docs/roles/lead/TO_HACKATHON_LEAD.md",
    "docs/roles/lead/WORK_TIME_LOG.md",
})
WORK_PREFIXES = (
    "src/", "tests/", "tools/", "docs/architecture/",
    "references/", "skill/", "skills/",
)
WORK_EXACT = frozenset({"SKILL.md"})

def closeout_errors(changed: set[str]) -> list[str]:
    work = sorted(p for p in changed
                  if p in WORK_EXACT or any(p.startswith(prefix) for prefix in WORK_PREFIXES))
    if not work:
        return []
    missing = sorted(REQUIRED - changed)
    return ([f"Work files changed: {', '.join(work)}"] +
            [f"Missing mandatory end-of-work GitHub update: {path}" for path in missing]
            if missing else [])

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",required=True)
    parser.add_argument("--head",required=True)
    args=parser.parse_args()
    if not args.base.strip("0"):
        print("New branch/no base: validate latest LIVE_HANDOFF manually.")
        return 0
    diff=subprocess.run(
        ["git","diff","--name-only",args.base,args.head],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    files=set(diff.stdout.splitlines())
    failures=closeout_errors(files)
    if failures:
        for line in failures: print(line)
        return 1
    print(f"Closeout path sync PASS; {len(files)} changed files checked.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
