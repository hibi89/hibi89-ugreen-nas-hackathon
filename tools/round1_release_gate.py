"""Independent integrity/release-gate audit for UGREEN Round 1 DRAFT.

Never upload, approve, sign or submit. A technical PASS does not grant an
SDK license, NAS permission, finalist status or participant approval.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

MAX_PDF=1_000_000
MAX_ZIP=10*1024*1024
GATES=(
 ("entrant_editorial_approval","PENDING","Entrant must review the exact ten-answer PDF, Markdown ZIP, and factual declarations"),
 ("official_creation_tool_use","NOT_VERIFIED","Round 1 rules require using the official UGOS Skill Creation Tool; installed use/creation provenance is not evidenced by the public capability catalog"),
 ("sdk_license_and_attribution","NOT_CLEARED","Confirm official-kit usage terms, all third-party sources/licenses and ownership before submission"),
 ("round1_dataflow_disclosure","REVIEW_PENDING","Entrant confirms the planned owner permission, external services and local/cloud unknowns are stated truthfully; live NAS access is not required in Round 1"),
)
OTHER=(
 ("official_checker_execution","NOT_RUN","Starter Kit recommends running its checker; no equivalent official-validation success claimed"),
 ("real_nas_runtime","NOT_RUN","Finalist-only device validation; NOT a Round 1 eligibility prerequisite"),
 ("real_privacy_permission_audit","NOT_CHECKED","Full installed runtime/privacy verification is finalist-dependent and not a Round 1 prerequisite"),
 ("devpost_submission","NOT_SUBMITTED","Real Devpost receipt must be verified after approved submission"),
)
class ReleaseAuditError(ValueError):pass
def sha256(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def audit(manifest:dict,zip_data:bytes,pdf_data:bytes)->dict:
    if manifest.get("kind")!="UGREEN_ROUND1_PREVIEW_NOT_SUBMITTED":
        raise ReleaseAuditError("Not a known preview manifest")
    p=manifest.get("pdf") or {}
    if (len(zip_data)>MAX_ZIP or len(pdf_data)>MAX_PDF or
        not zip_data.startswith(b"PK\x03\x04") or not pdf_data.startswith(b"%PDF-")):
        raise ReleaseAuditError("Candidate size or signature invalid")
    if sha256(zip_data)!=manifest.get("sha256_zip") or len(zip_data)!=manifest.get("zip_bytes"):
        raise ReleaseAuditError("ZIP hash/size differs from source manifest")
    if sha256(pdf_data)!=p.get("sha256") or len(pdf_data)!=p.get("bytes"):
        raise ReleaseAuditError("PDF hash/size differs from source manifest")
    if (manifest.get("zip_member_count")!=4 or len(manifest.get("zip_members",[]))!=4
        or not manifest.get("zip_contains_markdown_only") or
        p.get("official_questions_in_pdf")!=10 or not p.get("content_extractable")
        or not 1<=p.get("pages",0)<=5 or manifest.get("proposal_question_count")!=10
        or not 0<manifest.get("proposal_answer_words",501)<=500):
        raise ReleaseAuditError("Draft technical contract incomplete")
    for key,want in (("entrant_approval","PENDING"),("license_and_dataflow_review","NOT_CLEARED"),
                     ("official_uliya_checker","NOT_RUN"),("live_nas_validation","NOT_RUN"),
                     ("devpost_submission","NOT_SUBMITTED")):
        if manifest.get(key)!=want:raise ReleaseAuditError("Unsupported claimed status: "+key)
    paths=[x.get("path") for x in manifest["zip_members"]]
    if len(set(paths))!=4 or any(not isinstance(p,str) or not p.endswith(".md") for p in paths):
        raise ReleaseAuditError("ZIP paths duplicate or not Markdown")
    return {
      "assessment":"OFFLINE_TECHNICAL_PREVIEW_PASS",
      "release_decision":"NOT_APPROVED_FOR_SUBMISSION",
      "rules_reference":manifest.get("official_rules_url"),
      "pdf":{"sha256":p["sha256"],"bytes":len(pdf_data),"pages":p["pages"]},
      "zip":{"sha256":manifest["sha256_zip"],"bytes":len(zip_data),"files":4},
      "answer_count":10,"answer_words":manifest["proposal_answer_words"],
      "required_reviews":[{"gate":k,"status":v,"action":a} for k,v,a in GATES],
      "other_incomplete":[{"gate":k,"status":v,"note":a} for k,v,a in OTHER],
      "claim_limit":"Static draft preview only; no UGREEN, NAS, Devpost or participant verification.",
    }

def markdown(report:dict)->str:
    p,z=report["pdf"],report["zip"]
    lines=["# UGREEN Round 1 - draft release review",
      "","**OFFLINE technical preview PASS; NOT APPROVED FOR SUBMISSION.**","",
      "- PDF: "+str(p["pages"])+" pages / "+str(p["bytes"])+" bytes / SHA-256 "+p["sha256"],
      "- Skill ZIP: "+str(z["files"])+" Markdown members / "+str(z["bytes"])+" bytes / SHA-256 "+z["sha256"],
      "- Answers: 10 official questions / "+str(report["answer_words"])+" of 500 substantive English words.",
      "","## Required participant or external checks (NOT CLEARED)",""]
    lines += ["- [ ] "+g["gate"]+" ["+g["status"]+"]: "+g["action"] for g in report["required_reviews"]]
    lines += ["","## Other unfinished steps",""]
    lines += ["- [ ] "+g["gate"]+" ["+g["status"]+"]: "+g["note"] for g in report["other_incomplete"]]
    lines += ["","This draft is NOT SUBMITTED. Actual evidence is required to change a gate.",""]
    return "\n".join(lines)

def main()->int:
    p=argparse.ArgumentParser()
    for arg in ("manifest","zip","pdf","output-dir"):p.add_argument("--"+arg,required=True,type=Path)
    a=p.parse_args()
    try:
        report=audit(json.loads(a.manifest.read_text(encoding="utf8")),a.zip.read_bytes(),a.pdf.read_bytes())
        a.output_dir.mkdir(parents=True,exist_ok=True)
        (a.output_dir/"Round1_DRAFT_Release_Gates.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
        (a.output_dir/"Round1_DRAFT_Release_Checklist.md").write_text(markdown(report),encoding="utf8")
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print("ROUND1 RELEASE AUDIT FAIL:",type(exc).__name__,str(exc)[:160])
        return 1
    print("ROUND1 RELEASE AUDIT PASS: byte-identical PDF/ZIP hashes; external gates NOT_CLEARED; NOT_SUBMITTED")
    return 0
if __name__=="__main__":raise SystemExit(main())
