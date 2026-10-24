"""GitHub push closeout: every push must update the authoritative MASTER_PROGRESS.

Path checks establish update synchronization, not factual accuracy of SDK/NAS.
"""
from __future__ import annotations
import argparse
import subprocess

REQUIRED=frozenset({
    "MASTER_PROGRESS.md",
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
WORK_PREFIXES=("src/","tests/","tools/","docs/architecture/","references/","skill/","skills/")
WORK_EXACT=frozenset({"SKILL.md"})

def closeout_errors(changed:set[str])->list[str]:
    if changed and "MASTER_PROGRESS.md" not in changed:
        return ["Missing required MASTER_PROGRESS.md update in this push"]
    work=sorted(p for p in changed if p in WORK_EXACT or any(p.startswith(x) for x in WORK_PREFIXES))
    if not work:
        return []
    missing=sorted(REQUIRED-changed)
    if missing:
        return [f"Work files changed: {', '.join(work)}"]+[f"Missing mandatory end-of-work GitHub update: {p}" for p in missing]
    return []

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--base",required=True);p.add_argument("--head",required=True);a=p.parse_args()
    if not a.base.strip("0"):
        print("No base for new branch: inspect manually")
        return 0
    names=set(subprocess.run(["git","diff","--name-only",a.base,a.head],check=True,
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.splitlines())
    errors=closeout_errors(names)
    for error in errors:print(error)
    if errors:return 1
    print(f"Closeout path sync PASS; MASTER_PROGRESS path present, {len(names)} changed files")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
