"""G67: Creator-origin candidate only; independent owner-review PDF/ZIP preview.

Never overwrites the historical G52 PDF/ZIP or the canonical G49 Skill.
Do not interpret a successful preview as owner release, real NAS, or submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from pypdf import PdfReader

from check_round1_proposal import PROMPTS
from flowpilot_package_audit import audit_zip_bytes

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill/creator-candidate/flowpilot-nas/SKILL.md"
QA = ROOT / "docs/submission/flowpilot_round1_qas_G67_owner_review.json"
G65 = ROOT / "docs/submission/G65_OFFICIAL_FLOWPILOT_CREATOR_EXECUTION_20261028.md"
PIN = "f7982feae70e773440486fd8b0bee408fbadc69ced82d96d6e761c686f6131a5"
CHECKER_RUN = "https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40547404706"
FILEROOT = "FlowPilot_G67_CREATOR_OWNER_REVIEW"


def validate_inputs() -> tuple[bytes, list[dict], str, int]:
    if SKILL.is_symlink() or not SKILL.is_file() or QA.is_symlink() or not G65.is_file():
        raise ValueError("G65 reviewed source/evidence missing")
    skill = SKILL.read_bytes()
    if hashlib.sha256(skill).hexdigest() != PIN:
        raise ValueError("G66 official-checker-pinned candidate SHA mismatch")
    if not skill.startswith(b"---\nname: flowpilot-nas\ndescription:"):
        raise ValueError("Invalid Markdown Skill frontmatter")
    data = json.loads(QA.read_text(encoding="utf-8"))
    if set(data) != {"status", "questions", "disclosure"} or data["status"] != "OWNER_REVIEW_NOT_SUBMITTED":
        raise ValueError("Release status or QA schema changed")
    questions = data["questions"]
    if not isinstance(questions, list) or len(questions) != 10:
        raise ValueError("Exactly 10 official questions required")
    if any(not isinstance(q, dict) or set(q) != {"question", "answer"}
           or not isinstance(q["answer"], str) or not q["answer"].strip()
           for q in questions):
        raise ValueError("Invalid official answer")
    if [q["question"] for q in questions] != PROMPTS:
        raise ValueError("Official 10-question text mismatch")
    words = sum(len(re.findall(r"\b[\w-]+\b", q["answer"])) for q in questions)
    if words > 500 or words < 100:
        raise ValueError("Outside substantive word-limit window")
    disclosure = data["disclosure"]
    if not isinstance(disclosure, str) or not disclosure.strip():
        raise ValueError("Missing explicit AI and licensing disclosure")
    expected = ("ChatGPT", "Codex", "UGREEN", "Creator", "third-party", "NOT_SUBMITTED")
    whole = disclosure + " " + " ".join(q["answer"] for q in questions)
    if not all(t.casefold() in whole.casefold() for t in expected):
        # Some status language should be in manifest rather than QAs; reject
        # incomplete disclosure only for material claims, not a spelling marker.
        if not all(t.casefold() in whole.casefold() for t in expected[:-1]):
            raise ValueError("Missing contest disclosure fields")
    if "has NOT yet been generated" in whole or "Official Creator NOT_RUN" in whole:
        raise ValueError("Stale Creator claim from pre-G65 proposal")
    if "40547404706" not in whole:
        raise ValueError("Missing exact-source G66 static checker receipt")
    return skill, questions, disclosure, words


def build(output: Path) -> dict:
    skill, questions, disclosure, words = validate_inputs()
    output.mkdir(parents=True, exist_ok=True)
    pdf = output / (FILEROOT + ".pdf")
    bundle = output / (FILEROOT + ".zip")
    manifest = output / (FILEROOT + "_manifest.json")

    # Deterministic one-member Markdown-only ZIP. No developer code or vendor kit.
    member = ZipInfo("flowpilot-nas/SKILL.md", date_time=(2026, 10, 28, 0, 0, 0))
    member.compress_type = ZIP_DEFLATED
    member.external_attr = 0o100644 << 16
    with ZipFile(bundle, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(member, skill, compress_type=ZIP_DEFLATED, compresslevel=9)
    audit = audit_zip_bytes(bundle.read_bytes(), skill)
    if not audit["source_exact_match"] or audit["third_party_binary_members"] or audit["official_uliya_toolkit_files"]:
        raise ValueError("Unsafe release preview ZIP")

    styles = getSampleStyleSheet()
    body = ParagraphStyle("G67Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=8.55, leading=11.25, spaceAfter=3.2)
    question = ParagraphStyle("G67Question", parent=body, fontName="Helvetica-Bold",
                              fontSize=8.8, leading=11.0, spaceAfter=0.9,
                              textColor=colors.HexColor("#153454"))
    title = ParagraphStyle("G67Title", parent=body, fontName="Helvetica-Bold",
                           fontSize=15, leading=17, spaceAfter=4,
                           textColor=colors.HexColor("#153454"))
    caption = ParagraphStyle("G67Caption", parent=body, fontSize=7.1,
                             leading=9.0, spaceAfter=2)
    intro = "G67 | Creator-origin candidate | Owner review only - NOT SUBMITTED"
    doc = [
        Paragraph("NAS FlowPilot | UGREEN Round 1 Proposal", title),
        Paragraph(escape(intro), question),
        Paragraph(f"10 exact official questions | {words}/500 substantive answer words", caption),
        Spacer(1, 3),
    ]
    for index, q in enumerate(questions, 1):
        doc.append(KeepTogether([
            Paragraph(f"Q{index}. {escape(q['question'])}", question),
            Paragraph(escape(q["answer"]), body)
        ]))
    doc.extend([
        Spacer(1, 3),
        Paragraph("AI Assistance / Third-party / Data Flow Disclosures", question),
        Paragraph(escape(disclosure), caption),
        Paragraph("Skill SHA256: " + PIN, caption),
        Paragraph("Official UGREEN static Checker G66: static-pass (0/0/0). "
                  "Official Creator workflow: Codex operator-reported. "
                  "Real NAS/Expert: NOT RUN. Owner release: HOLD.", caption)
    ])
    SimpleDocTemplate(str(pdf), pagesize=A4,
                      leftMargin=14 * mm, rightMargin=14 * mm,
                      topMargin=10 * mm, bottomMargin=10 * mm).build(doc)
    reader = PdfReader(pdf)
    if len(reader.pages) != 1:
        raise ValueError("Proposal exceeds one A4 PDF page")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if any(f"Q{i}." not in text for i in range(1, 11)):
        raise ValueError("Missing visible official question in rendered PDF")
    # Extractors may insert newlines inside the 64-character digest or footer.
    # Preserve an exact-byte SHA comparison, but normalize extraction whitespace.
    normalized = " ".join(text.split())
    compact = "".join(text.split())
    has_sha = PIN in compact
    has_status = "NOT SUBMITTED" in normalized
    has_release = "Owner release: HOLD" in normalized
    if not (has_sha and has_status and has_release):
        raise ValueError(f"PDF extracted proof incomplete: sha={has_sha}, status={has_status}, release={has_release}")
    if len(skill) > 1_000_000 or pdf.stat().st_size > 1_000_000 or bundle.stat().st_size > 10_000_000:
        raise ValueError("Artifact exceeds size policy")
    result = {
        "stage": "G67_CREATOR_ORIGIN_OWNER_REVIEW_PREVIEW",
        "status": "OWNER_REVIEW_NOT_SUBMITTED",
        "skill_sha256": PIN,
        "zip_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "zip_bytes": bundle.stat().st_size,
        "pdf_bytes": pdf.stat().st_size,
        "pdf_pages": len(reader.pages),
        "official_questions": 10,
        "substantive_answer_words": words,
        "zip_composition": audit,
        "official_creator": "OPERATOR_REPORTED_CODEX_ULIYA_0.7.3_EN",
        "official_checker": "VERIFIED_STATIC_PASS_EXACT_CANDIDATE_SHA",
        "official_checker_run": CHECKER_RUN,
        "registered_uliya_expert": "NOT_RUN",
        "nas_runtime": "NOT_RUN",
        "rights_signoff": "PENDING",
        "owner_release": "HOLD",
        "devpost": "NOT_SUBMITTED",
        "predecessor_submission_artifacts": "UNCHANGED"
    }
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="G67 read-only human-review preview builder")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
