"""Offline-first compliance check for the official Round 1 ten-question English PDF draft.

This validates the *authored proposal*, not the official SDK or user consent.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JSON_PATH=ROOT/"docs/submission/round1_proposal.json"
MD_PATH=ROOT/"docs/submission/ROUND1_PROPOSAL_DRAFT.md"
PROMPTS=[
    "One sentence: What does the Skill do?",
    "Who is the target user and problem?",
    "What is your proposed solution?",
    "What is the Core User Flow?",
    "What substantive difference does your idea offer compared with existing tools or conventional AI solutions?",
    "Which UGREEN AI NAS capabilities will be used, and at which step in the workflow?",
    "What was your technical approach? Describe the planned Skill workflow, supported NAS CLI capabilities, expert agent orchestration, required inputs, permissions, AI model choices, and data handling, as applicable;",
    "What is the current development status? Identify what was implemented already, not yet implemented, or is pending NAS validation if selected to be a Finalist.",
    "What is your final validation plan? Name two core test cases and one edge case to validate if selected as a Finalist.",
    "Are there any known limitations of your Project? Describe current known limitations, technical risks, and any external dependencies."
]
def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b",text))
def render_markdown(d:dict)->str:
    line=["# ProjectReady NAS — UGREEN Round 1 Proposal","",
          f"> **DRAFT / NOT SUBMITTED — {d['dated_kst']} KST**. Ten substantive answers total **{d['substantive_words']}/500 English words**. Do not imply official NAS, validator, privacy or licensing approval.",""]
    for item in d["questions"]:
        line += [f"## {item['number']}. {item['prompt']}","",item["answer"],""]
    line+=["## Third-party and AI declarations (separate from 10 answers)",""]
    for k,v in d["disclosures"].items():
        line += [f"- **{k.replace('_',' ')}:** {v}"]
    line+=["","**Official prompt source:** https://ugreenhackathon.devpost.com/rules",
           "**Production decision:** Submission requires participant review, verified external rights, approved PDF and final ZIP; neither official NAS validation nor Devpost submission has occurred.",""]
    return "\n".join(line)+"\n"
def errors(d:dict,markdown:str|None=None)->list[str]:
    err=[]
    if d.get("status")!="DRAFT_NOT_SUBMITTED":err.append("Do not claim submission")
    if d.get("official_rules_url")!="https://ugreenhackathon.devpost.com/rules":err.append("Missing official primary source")
    questions=d.get("questions",[])
    if len(questions)!=10:
        err.append("Exactly ten answers are required")
        return err
    for i,x in enumerate(questions):
        if x.get("number")!=i+1 or x.get("prompt")!=PROMPTS[i]:err.append(f"Official question {i+1} changed")
        a=x.get("answer")
        if not isinstance(a,str) or not a.strip():err.append(f"Answer {i+1} missing")
    count=sum(word_count(x.get("answer","")) for x in questions)
    if count>500:err.append(f"Word cap exceeded: {count}")
    if d.get("substantive_words")!=count:err.append("Wrong word count stored")
    proofs=d.get("proof_status",{})
    if proofs.get("official_validator")!="NOT_RUN" or proofs.get("nas")!="NOT_RUN" or proofs.get("devpost")!="NOT_SUBMITTED":
        err.append("Falsified live platform/submission status")
    disclosures=d.get("disclosures",{})
    for field in ("ai_assistance","platform","other_libraries","data_flow"):
        if not isinstance(disclosures.get(field),str) or len(disclosures[field])<35:err.append(f"Missing disclosure {field}")
    if markdown is not None and markdown!=render_markdown(d):err.append("Markdown not regenerated from JSON")
    return err
def main():
    a=argparse.ArgumentParser();a.add_argument("--check",action="store_true");args=a.parse_args()
    d=json.loads(JSON_PATH.read_text(encoding="utf8"))
    results=errors(d,MD_PATH.read_text(encoding="utf8"))
    for e in results:print("ROUND1 DRAFT ERROR:",e)
    if results:return 1
    print(f"ROUND1 DRAFT PASS: 10 official answers, {d['substantive_words']}/500 substantive English words, disclosures, NOT_SUBMITTED")
    return 0
if __name__=="__main__":raise SystemExit(main())
