"""G80: held owner-review PDF + ZIP from an exact SHA-pinned Creator-reported Skill.

The actual candidate stays in the owner's local environment. This script does
not invoke Uliya, Codex, NAS, Devpost or any public release. The old canonical
flowpilot-nas Skill and G75/G76 review packages are not touched.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import stat
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from flowpilot3_round1_builder import PROMPTS, verify_pdf

PIN = '2ac1b6c656c57443c63ee71b0d03b81a286845da230e9bdf068066d08f16dac7'
NAME = 'flowpilot-3'
MEMBER = 'flowpilot-3/SKILL.md'
PDF_NAME = 'NAS_FlowPilot3_Creator_R1_OWNER_REVIEW.pdf'
ZIP_NAME = 'NAS_FlowPilot3_Creator_R1_OWNER_REVIEW.zip'
MANIFEST_NAME = 'NAS_FlowPilot3_Creator_R1_manifest.json'
CREATOR_EVIDENCE = 'OWNER_REPORTED_NOT_INDEPENDENTLY_VERIFIED'
CHECKER_STATUS = 'static-pass-needs-target-validation'
WARNING = 'DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE'
REQUIRED_INTENTS = ('CHECK_REQUIRED', 'REVIEW_VERSIONS', 'HANDOFF_AUDIT', 'SUMMARIZE_SELECTED')
MAX_SKILL = 1_000_000
MAX_ZIP = 10_000_000
MAX_PDF = 1_000_000


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def validate_skill(raw: bytes, *, expected_sha: str = PIN) -> None:
    if not raw or len(raw) > MAX_SKILL or digest(raw) != expected_sha:
        raise ValueError('Candidate source hash or size mismatch')
    try:
        doc = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Candidate is not UTF-8') from exc
    front = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n', doc, re.S)
    if not front:
        raise ValueError('Invalid SKILL.md frontmatter')
    attrs = {}
    for line in front.group(1).splitlines():
        if ':' not in line:
            raise ValueError('Malformed frontmatter')
        key, value = [x.strip() for x in line.split(':', 1)]
        if key in attrs:
            raise ValueError('Duplicate frontmatter key')
        attrs[key] = value.strip('"\'')
    if attrs.get('name') != NAME or not (1 <= len(attrs.get('description', '')) <= 1024):
        raise ValueError('Creator candidate identity/description mismatch')
    if not all(signal in doc for signal in REQUIRED_INTENTS + ('file-agent', 'document-agent')):
        raise ValueError('Candidate missing expected delegated review capabilities')
    if re.search(r'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY-----', doc):
        raise ValueError('Potential credential in candidate')
    if re.search(r'(?mi)^\s*(?:TODO|TBD|FIXME)\s*[:\-]', doc):
        raise ValueError('Unfinished candidate instructions')


def validate_qa(qa: dict, *, expected_sha: str = PIN) -> int:
    if (not isinstance(qa, dict) or qa.get('status') != 'OWNER_REVIEW_NOT_SUBMITTED'
            or qa.get('date_kst') != '2026-10-31' or qa.get('project') != 'NAS FlowPilot 3.0'
            or qa.get('candidate_name') != NAME or qa.get('source_skill_sha256') != expected_sha
            or qa.get('official_creator_evidence') != CREATOR_EVIDENCE):
        raise ValueError('Proposal is not the exact held Creator candidate edition')
    chk = qa.get('checker_evidence')
    if not isinstance(chk, dict) or (chk.get('source'), chk.get('status'), chk.get('errors'), chk.get('warnings')) != (
            'owner_report', CHECKER_STATUS, 0, [WARNING]):
        raise ValueError('Do not erase or upgrade owner-reported Checker warning')
    rows = qa.get('questions')
    if not isinstance(rows, list) or len(rows) != len(PROMPTS) or any(not isinstance(r, dict) for r in rows):
        raise ValueError('Exactly ten official responses required')
    if [r.get('question') for r in rows] != PROMPTS:
        raise ValueError('Official questions differ')
    if any(not isinstance(r.get('answer'), str) or not r['answer'].strip() for r in rows):
        raise ValueError('Empty answer')
    words = sum(len(re.findall(r'\b[\w-]+\b', row['answer'])) for row in rows)
    if words > 500:
        raise ValueError('Answer words exceed 500')
    disclosure = qa.get('disclosure')
    if not isinstance(disclosure, str) or len(disclosure) < 100:
        raise ValueError('AI, third-party and data-flow disclosure missing')
    for phrase in ('Codex', 'ChatGPT', 'Third-party', 'Data flow', 'owner-reported', 'warning', 'not independently'):
        if phrase.casefold() not in disclosure.casefold():
            raise ValueError('Missing truthful disclosure field: ' + phrase)
    return words


def build(skill_path: Path, qa_path: Path, out: Path, *, expected_sha: str = PIN) -> dict:
    """Create review files only, without overwrite. Test fixtures may supply an alternate hash."""
    for path in (skill_path, qa_path):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SKILL:
            raise ValueError('Candidate or proposal input unavailable/unsafe')
    skill = skill_path.read_bytes()
    validate_skill(skill, expected_sha=expected_sha)
    qa_raw = qa_path.read_bytes()
    qa = json.loads(qa_raw.decode('utf-8'))
    words = validate_qa(qa, expected_sha=expected_sha)
    if out.is_symlink() or out.parent.is_symlink():
        raise ValueError('Output path cannot be a symlink')
    out.mkdir(parents=True, exist_ok=True)
    pdf, zip_path, manifest = (out / PDF_NAME, out / ZIP_NAME, out / MANIFEST_NAME)
    if any(p.exists() or p.is_symlink() for p in (pdf, zip_path, manifest)):
        raise ValueError('Existing reviewer artifact; select fresh output directory')
    with ZipFile(zip_path, 'x', compression=ZIP_DEFLATED, compresslevel=9) as z:
        info = ZipInfo(MEMBER, (2026, 10, 31, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        z.writestr(info, skill)
    with ZipFile(zip_path) as z:
        infos = z.infolist()
        if len(infos) != 1 or infos[0].filename != MEMBER or infos[0].is_dir() or stat.S_ISLNK(infos[0].external_attr >> 16):
            raise ValueError('ZIP contains unsafe or unexpected entries')
        if z.testzip() is not None or z.read(MEMBER) != skill:
            raise ValueError('ZIP corruption or source mismatch')
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, KeepTogether
    navy = colors.HexColor('#153351')
    slate = colors.HexColor('#45576B')
    title = ParagraphStyle('G80Title', fontName='Helvetica-Bold', fontSize=16, leading=18,
                           textColor=navy, spaceAfter=6)
    lead = ParagraphStyle('G80Lead', fontName='Helvetica', fontSize=7.6, leading=9.2,
                          textColor=slate, spaceAfter=4)
    question = ParagraphStyle('G80Question', fontName='Helvetica-Bold', fontSize=8.7,
                              leading=11.1, textColor=navy, spaceBefore=4, spaceAfter=2)
    answer = ParagraphStyle('G80Answer', fontName='Helvetica', fontSize=8.65,
                            leading=11.5, textColor=colors.HexColor('#1C2936'), spaceAfter=1)
    small = ParagraphStyle('G80Small', fontName='Helvetica', fontSize=7.75,
                           leading=10.35, textColor=slate, spaceAfter=2)
    story = [Paragraph('NAS FlowPilot 3.0', title),
             Paragraph('UGREEN ROUND 1 / ENTRANT REVIEW DRAFT / NOT SUBMITTED', lead),
             Paragraph('Candidate: flowpilot-3  |  10 official questions  |  '
                       f'{words}/500 substantive English words  |  October 31, 2026', small),
             Spacer(1, 3)]
    for i, q in enumerate(qa['questions'], 1):
        story.append(KeepTogether([Paragraph(f'Q{i}. {escape(q["question"])}', question),
                                  Paragraph(escape(q['answer']), answer)]))
    story.extend([Spacer(1, 4), Paragraph('AI assistance / Third-party components / Data flow', question),
                  Paragraph(escape(qa['disclosure']), small),
                  Paragraph('Source SHA-256: ' + expected_sha + '. Creator and Checker execution: owner-reported only; '
                            'static delegation warning unresolved; NAS NOT RUN; release HOLD.', small)])
    def decorate(canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor('#CED9E3'))
        canvas.line(16 * mm, 13 * mm, width - 16 * mm, 13 * mm)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(slate)
        canvas.drawString(16 * mm, 9 * mm, 'FLOWPILOT 3.0 / OWNER REVIEW / NOT SUBMITTED')
        canvas.drawRightString(width - 16 * mm, 9 * mm, f'Page {doc.page}')
        canvas.restoreState()
    SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                      topMargin=13*mm, bottomMargin=16*mm, title='NAS FlowPilot 3.0 - Round 1 Review').build(
                          story, onFirstPage=decorate, onLaterPages=decorate)
    pages = verify_pdf(pdf, qa)
    if pdf.stat().st_size > MAX_PDF or zip_path.stat().st_size > MAX_ZIP:
        raise ValueError('Review output exceeds official size cap')
    report = {
        'status': 'OWNER_REVIEW_NOT_SUBMITTED', 'release_gate': 'HOLD',
        'candidate_name': NAME, 'skill_sha256': digest(skill),
        'qa_sha256': digest(qa_raw), 'zip_sha256': digest(zip_path.read_bytes()),
        'pdf_sha256': digest(pdf.read_bytes()), 'zip_bytes': zip_path.stat().st_size,
        'unpacked_skill_bytes': len(skill), 'pdf_bytes': pdf.stat().st_size,
        'pdf_pages': pages, 'questions': 10, 'substantive_words': words,
        'zip_members': [MEMBER], 'zip_crc': 'PASS', 'skill_source_parity': 'PASS',
        'creator_evidence': CREATOR_EVIDENCE,
        'checker_report': {'source': 'owner_report', 'status': CHECKER_STATUS,
                           'errors': 0, 'warnings': [WARNING]},
        'real_nas': 'NOT_RUN', 'live_experts': 'NOT_VERIFIED',
        'third_party_rights_approved': False, 'owner_approved_release': False,
        'devpost_submitted': False, 'canonical_skill_modified': False,
    }
    manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description='Build G80 owner-review PDF and Skill ZIP; release always HOLD')
    ap.add_argument('--skill', required=True, type=Path)
    ap.add_argument('--qa', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    print(json.dumps(build(args.skill, args.qa, args.out), indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
