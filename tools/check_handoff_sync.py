"""Check actual code changes have full handoff and status JSON regenerated.

A full closeout is needed for source/test/tool edits. Simple docs-only
updates do not trigger full closeout, but a changed canonical master JSON
must ALWAYS be accompanied by the generated MASTER_PROGRESS.md.
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

def closeout_errors(changed: set[str]) -> list[str]:
    if "data/master_progress.json" in changed and "MASTER_PROGRESS.md" not in changed:
        return ["Missing required MASTER_PROGRESS.md update when canonical JSON changed"]
    work=sorted(p for p in changed if p in WORK_EXACT or any(p.startswith(x) for x in WORK_PREFIXES))
    if not work:
        return []
    missing=sorted(REQUIRED-changed)
    if not missing:
        return []
    return [f"Work files changed: {', '.join(work)}"]+[
        f"Missing mandatory end-of-work GitHub update: {p}" for p in missing]

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",required=True)
    parser.add_argument("--head",required=True)
    args=parser.parse_args()
    if not args.base.strip("0"):
        print("No previous head: manual review necessary")
        return 0
    changed=set(subprocess.run(["git","diff","--name-only",args.base,args.head],
        check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.splitlines())
    errors=closeout_errors(changed)
    for error in errors: print(error)
    if errors:return 1
    print(f"Closeout path sync PASS; {len(changed)} changed paths")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
