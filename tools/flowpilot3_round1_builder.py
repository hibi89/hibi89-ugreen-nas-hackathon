"""Owner-review ONLY: build the Round 1 proposal PDF and Markdown-only Skill ZIP.

No Uliya Expert, NAS runtime, official Creator, GitHub release or Devpost action.
It intentionally reuses the exact already reviewed FlowPilot Skill bytes while
separately describing the new LOCAL FlowPilot 3.0 prototype without claiming
that local Python code ships in the Uliya Skill ZIP.
"""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer
from pypdf import PdfReader

PIN = '47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b'
MEMBER = 'flowpilot-nas/SKILL.md'
PROMPTS = [
    'One sentence: What does the Skill do?',
    'Who is the target user and problem?',
    'What is your proposed solution?',
    'What is the Core User Flow?',
    'What substantive difference does your idea offer compared with existing tools or conventional AI solutions?',
    'Which UGREEN AI NAS capabilities will be used, and at which step in the workflow?',
    'What was your technical approach? Describe the planned Skill workflow, supported NAS CLI capabilities, expert agent orchestration, required inputs, permissions, AI model choices, and data handling, as applicable;',
    'What is the current development status? Identify what was implemented already, not yet implemented, or is pending NAS validation if selected to be a Finalist.',
    'What is your final validation plan? Name two core test cases and one edge case to validate if selected as a Finalist.',
    'Are there any known limitations of your Project? Describe current known limitations, technical risks, and any external dependencies.',
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def validate(skill: bytes, qa: dict) -> int:
    if not skill.startswith(b'---\nname: flowpilot-nas\ndescription:'):
        raise ValueError('Unrecognized official-entry Skill front matter')
    if len(skill) > 1_000_000 or sha(skill) != PIN:
        raise ValueError('Skill is too large or differs from pinned original')
    if not isinstance(qa, dict) or qa.get('status') != 'OWNER_REVIEW_NOT_SUBMITTED':
        raise ValueError('Missing owner-review hold')
    if qa.get('source_skill_sha256') != PIN:
        raise ValueError('Skill SHA does not match proposal')
    rows = qa.get('questions')
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError('Exactly ten official questions required')
    if [row.get('question') for row in rows if isinstance(row, dict)] != PROMPTS:
        raise ValueError('Official question text changed')
    if not all(isinstance(row.get('answer'), str) and row['answer'].strip() for row in rows):
        raise ValueError('Missing answer')
    words = sum(len(re.findall(r'\b[\w-]+\b', q['answer'])) for q in rows)
    if words > 500:
        raise ValueError(f'500 English-word substantive cap exceeded: {words}')
    disclosure = qa.get('disclosure')
    if not isinstance(disclosure, str) or len(disclosure) < 100:
        raise ValueError('Mandatory AI and third-party disclosure missing')
    return words


def verify_pdf(pdf: Path, qa: dict) -> int:
    reader = PdfReader(pdf)
    pages = len(reader.pages)
    if not 1 <= pages <= 2:
        raise ValueError('Unexpected PDF page count')
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    canonical = re.findall(r'[a-z0-9]+', text.lower())
    def coverage(value: str) -> float:
        expected = re.findall(r'[a-z0-9]+', value.lower())
        if not expected:
            return 0.0
        matched = sum(b.size for b in SequenceMatcher(None, expected, canonical, autojunk=False).get_matching_blocks())
        return matched / len(expected)
    for i, q in enumerate(qa['questions'], 1):
        if f'Q{i}.' not in text or coverage(q['question']) < .90 or coverage(q['answer']) < .90:
            raise ValueError(f'PDF extracted text does not cover Q{i}')
    if coverage(qa['disclosure']) < .90:
        raise ValueError('PDF missing disclosure')
    return pages


def build(skill_path: Path, qa_path: Path, out: Path) -> dict:
    if skill_path.is_symlink() or qa_path.is_symlink():
        raise ValueError('Symlink source not allowed')
    skill = skill_path.read_bytes()
    qa_bytes = qa_path.read_bytes()
    qa = json.loads(qa_bytes.decode('utf-8'))
    word_count = validate(skill, qa)
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / 'NAS_FlowPilot_3_Round1_OWNER_REVIEW.pdf'
    zip_path = out / 'NAS_FlowPilot_3_Round1_OWNER_REVIEW.zip'

    # Only one official package member. Local Python, workflows and the PDF
    # live outside the ZIP and are not interpreted by Uliya.
    with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED, compresslevel=9) as z:
        meta = ZipInfo(MEMBER, (2026, 10, 29, 0, 0, 0))
        meta.compress_type = ZIP_DEFLATED
        meta.external_attr = 0o644 << 16
        z.writestr(meta, skill)
    with ZipFile(zip_path) as z:
        infos = z.infolist()
        if len(infos) != 1 or infos[0].filename != MEMBER or z.read(MEMBER) != skill:
            raise ValueError('ZIP source parity or package structure failed')
        if infos[0].file_size > 1_000_000 or infos[0].file_size > 10_000_000:
            raise ValueError('ZIP oversized')

    styles = getSampleStyleSheet()
    title = ParagraphStyle('Title3', parent=styles['Normal'], fontName='Helvetica-Bold',
                           fontSize=15, leading=19, textColor=colors.HexColor('#193a5b'), spaceAfter=8)
    question = ParagraphStyle('Question3', parent=styles['Normal'], fontName='Helvetica-Bold',
                              fontSize=8.3, leading=10.4, textColor=colors.HexColor('#153c60'), spaceAfter=1)
    answer = ParagraphStyle('Answer3', parent=styles['Normal'], fontName='Helvetica',
                            fontSize=8.35, leading=11.1, textColor=colors.HexColor('#182a39'), spaceAfter=5)
    note = ParagraphStyle('Note3', parent=styles['Normal'], fontName='Helvetica',
                          fontSize=7.3, leading=9.5, textColor=colors.HexColor('#3e5369'), spaceAfter=5)
    story = [Paragraph('NAS FlowPilot 3.0 | Round 1 Project Proposal', title),
             Paragraph('OWNER REVIEW ONLY &middot; NOT SUBMITTED &middot; Narrow Uliya Skill / separate local prototype', note),
             Paragraph(f'10 official questions &middot; {word_count}/500 substantive English words &middot; October 29, 2026', note),
             Spacer(1, 3)]
    for i, row in enumerate(qa['questions'], 1):
        story.append(KeepTogether([
            Paragraph(f'Q{i}. {escape(row["question"])}', question),
            Paragraph(escape(row['answer']), answer)
        ]))
    story += [Spacer(1, 4), Paragraph('AI / Third-party / Data-flow disclosure', question),
              Paragraph(escape(qa['disclosure']), note),
              Paragraph('Skill source SHA-256: ' + PIN + '. Static check PASS for pinned source; official Creator and NAS runtime NOT_RUN.', note)]
    SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                      topMargin=13 * mm, bottomMargin=13 * mm,
                      title='NAS FlowPilot 3.0 | UGREEN Round 1 Owner Review').build(story)
    pages = verify_pdf(pdf, qa)
    if pdf.stat().st_size > 1_000_000 or zip_path.stat().st_size > 10_000_000:
        raise ValueError('Submission file exceeds official size cap')
    report = {
        'status': 'OWNER_REVIEW_NOT_SUBMITTED',
        'source_skill_sha256': sha(skill),
        'qa_sha256': sha(qa_bytes),
        'zip_sha256': sha(zip_path.read_bytes()),
        'pdf_sha256': sha(pdf.read_bytes()),
        'zip_bytes': zip_path.stat().st_size,
        'zip_unpacked_bytes': len(skill),
        'pdf_bytes': pdf.stat().st_size,
        'pdf_pages': pages,
        'questions': 10,
        'substantive_english_words': word_count,
        'skill_members': [MEMBER],
        'source_exact_match': True,
        'official_checker': 'PINNED_STATIC_PASS_ONLY',
        'official_creator': 'NOT_RUN',
        'nas_runtime': 'NOT_RUN',
        'la_integration': 'NOT_VERIFIED',
        'sovia_integration': 'NOT_VERIFIED',
        'legal_rights_released': False,
        'devpost_submitted': False,
        'local_prototype_excluded_from_zip': True,
    }
    (out / 'NAS_FlowPilot_3_Round1_OWNER_REVIEW_manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skill', required=True, type=Path)
    ap.add_argument('--qa', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    print(json.dumps(build(args.skill, args.qa, args.out), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
