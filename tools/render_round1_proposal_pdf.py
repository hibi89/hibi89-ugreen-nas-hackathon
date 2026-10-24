"""Optional local PDF renderer (ReportLab installed separately; never in Skill ZIP).

Usage: python tools/render_round1_proposal_pdf.py --output proposal_DRAFT.pdf
Source: docs/submission/round1_proposal.json; run check_round1_proposal.py first.
Not part of the runtime Skill, and not the official Uliya validator.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from xml.sax.saxutils import escape
from check_round1_proposal import JSON_PATH,MD_PATH,errors,render_markdown

def render(out:Path, proposal:dict|None=None)->None:
    try:
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.pagesizes import A4
    except ImportError as exc:
        raise RuntimeError("Optional local PDF generation requires ReportLab; not bundled with Skill ZIP") from exc
    d=proposal if proposal is not None else json.loads(JSON_PATH.read_text(encoding="utf8"))
    source_md=render_markdown(d) if proposal is not None else MD_PATH.read_text(encoding="utf8")
    faults=errors(d,source_md)
    if faults:raise ValueError("; ".join(faults))
    styles={
      "title":ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=19,leading=23,textColor=colors.HexColor("#123049"),spaceAfter=6),
      "subtitle":ParagraphStyle("subtitle",fontName="Helvetica",fontSize=8.3,leading=12,textColor=colors.HexColor("#475F72"),spaceAfter=12),
      "question":ParagraphStyle("question",fontName="Helvetica-Bold",fontSize=9,leading=11.5,spaceBefore=4,spaceAfter=1,textColor=colors.HexColor("#143D55")),
      "answer":ParagraphStyle("answer",fontName="Helvetica",fontSize=8.75,leading=12.2,spaceAfter=2,textColor=colors.HexColor("#243746")),
      "footer":ParagraphStyle("footer",fontName="Helvetica",fontSize=7,leading=9,textColor=colors.HexColor("#506273"),spaceBefore=3)}
    story=[Paragraph("ProjectReady NAS",styles["title"]),Paragraph(
      f"UGREEN AI NAS Hackathon | Round 1 proposal | DRAFT - NOT SUBMITTED | {d['substantive_words']}/500 answer words",styles["subtitle"])]
    for item in d["questions"]:
        story.append(KeepTogether([Paragraph(f"{item['number']:02d}  {item['prompt']}",styles["question"]),
                                   Paragraph(item["answer"],styles["answer"])]))
    story += [Spacer(1,4), Paragraph("Disclosures (separate from ten substantive answers)",styles["question"])]
    disclosure_labels = (
        ("ai_assistance", "AI assistance"),
        ("platform", "Platform and third-party source"),
        ("other_libraries", "Other libraries"),
        ("data_flow", "Data flow and permissions"),
    )
    # PDF declarations must be rendered from the same checked proposal JSON,
    # never a manually maintained shorter footer that can become stale.
    for key, label in disclosure_labels:
        story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(d['disclosures'][key])}",styles["footer"]))
    story.append(Paragraph("Official rules: ugreenhackathon.devpost.com/rules | Participant approval and submission pending.",styles["footer"]))
    def foot(canvas,doc):
        canvas.setStrokeColor(colors.HexColor("#CCD7E0"));canvas.line(47,32,A4[0]-47,32)
        canvas.setFont("Helvetica",7);canvas.drawRightString(A4[0]-47,21,f"{doc.page} | DRAFT")
    out.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(out),pagesize=A4,topMargin=39,bottomMargin=37,leftMargin=47,
        rightMargin=47,title="ProjectReady NAS | Round 1 Proposal Draft").build(story,onFirstPage=foot,onLaterPages=foot)
    if out.stat().st_size>1_000_000:raise ValueError("Official proposal PDF exceeds 1 MB")
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    render(a.output);print("ROUND1 DRAFT PDF CREATED (NOT SUBMITTED):",a.output)
if __name__=="__main__":main()
