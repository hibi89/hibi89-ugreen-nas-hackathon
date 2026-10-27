"""UGREEN G45 FlowPilot provisional PDF/ZIP owner-review builder; never submits."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile,ZIP_DEFLATED
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from check_round1_proposal import PROMPTS
from flowpilot_package_audit import audit_zip_bytes

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/"skill/flowpilot-nas/SKILL.md"
QA=ROOT/"docs/submission/flowpilot_round1_qas_20261027.json"
PIN="47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"
CHECKER_RUN="https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40505339535"
CHECKER_STATUS="FIRST_PARTY_STATIC_PASS_0_ERRORS_0_WARNINGS_0_INFO_EXACT_SOURCE"

def build(output:Path):
    if SKILL.is_symlink() or not SKILL.is_file():raise ValueError("Candidate source missing, unsafe or symlink")
    skill=SKILL.read_bytes()
    if hashlib.sha256(skill).hexdigest()!=PIN:raise ValueError("Changed source SHA needs review")
    if not skill.startswith(b"---\nname: flowpilot-nas\ndescription:"):raise ValueError("Invalid Skill YAML")
    data=json.loads(QA.read_text(encoding="utf-8"))
    questions=data["questions"]
    if data.get("status")!="OWNER_REVIEW_NOT_SUBMITTED" or len(questions)!=10:raise ValueError("Need ten owner-review QAs")
    if any(not q.get("question") or not q.get("answer") for q in questions):raise ValueError("Empty answer")
    if [q["question"] for q in questions]!=PROMPTS:raise ValueError("Official question text mismatch")
    words=sum(len(re.findall(r"\b[\w-]+\b",q["answer"])) for q in questions)
    if words>500:raise ValueError("500 substantive-word limit exceeded")
    output.mkdir(parents=True,exist_ok=True)
    pdf=output/"FlowPilot_Round1_OWNER_REVIEW.pdf"
    bundle=output/"FlowPilot_Round1_OWNER_REVIEW.zip"
    with ZipFile(bundle,"w",ZIP_DEFLATED,compresslevel=9) as z:z.writestr("flowpilot-nas/SKILL.md",skill)
    zip_audit=audit_zip_bytes(bundle.read_bytes(),skill)
    if zip_audit["official_uliya_toolkit_files"]!=0 or zip_audit["third_party_binary_members"]!=0:raise ValueError("Unexpected vendor files")
    styles=getSampleStyleSheet()
    body=ParagraphStyle("FPBody",parent=styles["Normal"],fontName="Helvetica",fontSize=9.0,leading=12.2,spaceAfter=4)
    qstyle=ParagraphStyle("FPQ",parent=body,fontName="Helvetica-Bold",fontSize=9.3,leading=11.8,spaceAfter=1,textColor=colors.HexColor("#153454"))
    title=ParagraphStyle("FPTitle",parent=body,fontName="Helvetica-Bold",fontSize=16,leading=18,spaceAfter=8,textColor=colors.HexColor("#153454"))
    note=ParagraphStyle("FPNote",parent=body,fontSize=8.0,leading=11)
    story=[Paragraph("NAS FlowPilot | UGREEN Round 1 Proposal",title),Paragraph("G52 OWNER REVIEW DRAFT - NOT SUBMITTED",qstyle),Paragraph(f"10 exact official questions | {words}/500 substantive words",note),Spacer(1,5)]
    for i,q in enumerate(questions,1):
        story.append(KeepTogether([Paragraph(f"Q{i}. {escape(q['question'])}",qstyle),Paragraph(escape(q["answer"]),body)]))
    story.extend([Spacer(1,4),Paragraph("AI / Third-party / Data Flow Disclosures",qstyle),Paragraph(escape(data["disclosure"]),note)])
    story.append(Paragraph("FlowPilot source SHA256: "+PIN+". Official Creator NOT_RUN; first-party static checker PASS (0/0/0).",note))
    SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=12*mm,bottomMargin=12*mm).build(story)
    from pypdf import PdfReader
    pages=PdfReader(pdf).pages
    if len(pages)!=1:raise ValueError("Expected exactly 1 page after official question expansion")
    if pdf.stat().st_size>1000000 or bundle.stat().st_size>10000000 or len(skill)>1000000:raise ValueError("Package exceeds limit")
    evidence={"state":"OWNER_REVIEW_NOT_SUBMITTED","source_sha256":PIN,"zip_sha256":hashlib.sha256(bundle.read_bytes()).hexdigest(),"pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"zip_bytes":bundle.stat().st_size,"pdf_bytes":pdf.stat().st_size,"answers":10,"substantive_words":words,"zip_composition_audit":zip_audit,"official_creator":"NOT_RUN","official_checker":CHECKER_STATUS,"official_checker_run":CHECKER_RUN,"nas_runtime":"NOT_RUN","devpost":"NOT_SUBMITTED"}
    (output/"FlowPilot_Round1_OWNER_REVIEW_manifest.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    return evidence

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();print(json.dumps(build(args.output),indent=2))
