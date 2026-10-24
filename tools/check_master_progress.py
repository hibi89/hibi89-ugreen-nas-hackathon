"""Structural 24-day master register audit against unchanged original baseline.

Does not authenticate external GitHub proofs or certify NAS.
"""
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"MASTER_PROGRESS.md"
SOURCE=ROOT/"docs/UGREEN_DAILY_EFFORT_PLAN_20261024.md"
STATES={"DONE","PARTIAL","BLOCKED","NOT_STARTED"}

def plan_rows(raw:str):
    out=[]
    for line in raw.splitlines():
        cols=[c.strip() for c in line.split("|")][1:-1]
        if len(cols)<5:continue
        m=re.match(r"^(\d{2}/\d{2})\s*\([^)]+\)",cols[0])
        if m:
            out.append(("2026-"+m.group(1).replace("/","-"),float(cols[2].rstrip("h")),float(cols[3].rstrip("h"))))
    return out

def master_rows(raw:str):
    out=[]
    for line in raw.splitlines():
        c=[x.strip() for x in line.split("|")][1:-1]
        if len(c)!=10 or not re.fullmatch(r"2026-\d{2}-\d{2}",c[0]):continue
        out.append((c[0],c[1],c[2].replace("*",""),c[3],c[4],c[5],float(c[6]),float(c[7]),c[8],c[9]))
    return out

def integrity_errors(m:str,p:str):
    orig=plan_rows(p);cur=master_rows(m);errors=[]
    if len(orig)!=24 or len(cur)!=24:
        return [f"Expected 24 days, original={len(orig)}, master={len(cur)}"]
    for n,(o,r) in enumerate(zip(orig,cur),1):
        date,ident,status,description,actual,detail,base,reserve,evidence,remaining=r
        if date!=o[0] or ident!=f"D{n:02d}":errors.append(f"Date/ID mismatch row {n}")
        if (base,reserve)!=o[1:]:errors.append(f"Plan hour mismatch row {n}")
        if status not in STATES:errors.append(f"Invalid status row {n}")
        if not (description and detail and remaining):errors.append(f"Missing description/recovery row {n}")
        if status!="NOT_STARTED":
            if actual!="2026-10-24" or not re.search(r"\]\((?:docs/|skill/|https://github\.com/)",evidence):
                errors.append(f"Unproven advance row {n}")
        elif actual!="—" or evidence!="—":errors.append(f"Future unproven work row {n}")
    if cur[0][2]!="DONE":errors.append("Oct 24 finite-day status must stay DONE")
    if cur[-1][2]=="DONE":errors.append("Nov 16 cannot be DONE without receipt")
    for required in ["100%","165/165","NOT_RUN","NOT_SUBMITTED","NOT_MEASURED","34.25h","26.75h","61h"]:
        if required not in m:errors.append("Missing summary distinction: "+required)
    return errors

def main():
    errors=integrity_errors(MASTER.read_text(encoding="utf8"),SOURCE.read_text(encoding="utf8"))
    for e in errors:print("MASTER_PROGRESS ERROR",e)
    if errors:return 1
    print("MASTER_PROGRESS PASS: 24 dates + budgets + statuses + evidence shape. Real NAS not audited.")
    return 0

if __name__=="__main__":raise SystemExit(main())
