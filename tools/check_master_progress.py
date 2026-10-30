"""Validate canonical JSON, rendered root dashboard and original 24-day plan.

Only synthetic/document facts are asserted, never actual NAS validation.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"MASTER_PROGRESS.md"
SOURCE=ROOT/"docs/UGREEN_DAILY_EFFORT_PLAN_20261024.md"
DATA=ROOT/"data/master_progress.json"
sys.path.insert(0,str(ROOT))
from render_master_progress import render

def plan_rows(raw):
    out=[]
    for line in raw.splitlines():
        cols=[c.strip() for c in line.split("|")][1:-1]
        if len(cols)<6:continue
        m=re.match(r"^(\d{2}/\d{2})\s*\([^)]+\)",cols[0])
        if not m:continue
        out.append(("2026-"+m.group(1).replace("/","-"),cols[1].replace("**",""),
            float(cols[2].rstrip("h")),float(cols[3].rstrip("h"))))
    return out

def integrity_errors(master,original):
    errors=[]
    try:
        doc=json.loads(DATA.read_text(encoding="utf-8"))
        original_rows=plan_rows(original)
        if doc.get("expected_days")!=24 or len(original_rows)!=24 or len(doc.get("days",[]))!=24:
            return ["Missing original or canonical 24-day coverage"]
        for n,(row,source) in enumerate(zip(doc["days"],original_rows),1):
            if row["day_id"]!=f"UGR-D{n:02d}" or row["scheduled_date_kst"]!=source[0]:
                errors.append(f"ID/date mismatch {n}")
            if row["scope"]!=source[1]:
                errors.append(f"Changed original scope {n}")
            if (float(row["estimated_total_hours"]),float(row["safe_total_hours"]))!=source[2:]:
                errors.append(f"Changed original time budget {n}")
        if doc["days"][0]["progress_state"]!="DONE" or doc["days"][0]["percent_complete"]!=100:
            errors.append("Actual 10/24 deliverables were not preserved")
        if doc["days"][1]["progress_state"]!="BLOCKED":
            errors.append("Unverified official SDK gate should stay BLOCKED")
        if doc["days"][-1]["progress_state"]=="DONE":
            errors.append("No Devpost submission receipt on 11/16")
        rendered = render(doc)
        if master != rendered:
            offset = next((i for i, (a, b) in enumerate(zip(master, rendered))
                           if a != b), min(len(master), len(rendered)))
            line = master.count("\n", 0, offset) + 1
            errors.append(
                "MASTER_PROGRESS.md does not equal deterministic JSON rendering"
                " (first differing line " + str(line)
                + ", local_chars=" + str(len(master))
                + ", expected_chars=" + str(len(rendered)) + ")"
            )
    except (ValueError,TypeError,KeyError,IndexError) as exc:
        errors.append("Invalid master JSON or content: "+str(exc))
    return errors

def main():
    errors=integrity_errors(MASTER.read_text(encoding="utf-8"),SOURCE.read_text(encoding="utf-8"))
    for error in errors:print("MASTER_PROGRESS ERROR",error)
    if errors:return 1
    print("MASTER_PROGRESS PASS: 24-day full plan, original budgets, generated JSON dashboard")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
