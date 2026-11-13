"""Optional offline Korean PDF evidence. No font files are redistributed.

PDFs are local QA documents, not cryptographically authenticated certificates.
ReportLab is only required when PDF output is explicitly requested.
"""
from __future__ import annotations
from io import BytesIO
import os
from pathlib import Path
import re
import stat
from typing import Any
from xml.sax.saxutils import escape
from .engine import InputError, _is_link

MAX_PDF_BYTES = 20 * 1024 * 1024
FONT_NAME = "FlowPilotLocalKorean"
FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"),
)


def _libraries():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, LongTable, Spacer, TableStyle
    except ImportError as exc:
        raise InputError("PDF output requires ReportLab; existing HTML/JSON output is still available") from exc
    return colors, A4, ParagraphStyle, pdfmetrics, TTFont, SimpleDocTemplate, Paragraph, LongTable, Spacer, TableStyle


def ensure_pdf_support() -> str:
    _, _, _, pdfmetrics, TTFont, *_ = _libraries()
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    for path in FONT_CANDIDATES:
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or path.is_symlink():
                continue
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(path)))
            return FONT_NAME
        except (OSError, ValueError, KeyError):
            continue
    raise InputError("PDF needs an installed Korean TTF: Windows Malgun Gothic or Linux Nanum; none bundled")


def _text(value: Any, max_chars: int = 250) -> str:
    original = str(value)
    cleaned = "".join(ch if ch >= " " and ch != "\x7f" else " " for ch in original[:max_chars])
    return escape(cleaned + (" …" if len(original) > max_chars else ""))


def render_pdf(report: dict[str, Any]) -> bytes:
    font = ensure_pdf_support()
    (colors, A4, ParagraphStyle, _, _, SimpleDocTemplate, Paragraph,
     LongTable, Spacer, TableStyle) = _libraries()
    if (not isinstance(report, dict) or report.get("status") not in
            {"READY", "INCOMPLETE", "BLOCKED", "NEEDS_REVIEW"}
            or not isinstance(report.get("files"), list)
            or not isinstance(report.get("issues"), list)):
        raise InputError("invalid PDF source report")
    style = ParagraphStyle("FPNormal", fontName=font, fontSize=9, leading=15, spaceAfter=7)
    small = ParagraphStyle("FPSmall", fontName=font, fontSize=7.5, leading=11, splitLongWords=True)
    heading = ParagraphStyle("FPHeading", parent=style, fontSize=16, leading=23, spaceAfter=12)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=44, bottomMargin=49,
                            title="FlowPilot Universal Offline Evidence",
                            author="FlowPilot Universal", pageCompression=1)
    status = report["status"]
    story = [
        Paragraph("FLOWPILOT UNIVERSAL | 납품 파일 검수", heading),
        Paragraph("검수 상태: " + _text(status) + " / 검사 파일 수: " +
                  str(report.get("files_scanned", 0)) + " / 이슈: " +
                  str(len(report["issues"])), style),
        Paragraph("요구사항: " + _text(report.get("title", "")), style),
        Paragraph("원본 경로: " + _text(report.get("root", ""), 350), small),
        Paragraph("오프라인 읽기 전용 보고서입니다. 서명·고객 인수·인증·판매 승인 문서가 아닙니다.", style),
    ]
    if status != "READY":
        story.append(Paragraph("검토 또는 보류 필요: 이 결과는 최종 완료 증명이 아닙니다.", style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("검사 이슈", heading))
    for issue in report["issues"][:200]:
        if not isinstance(issue, dict):
            raise InputError("bad PDF issue")
        location = issue.get("path", ", ".join(map(str, issue.get("paths", []))))
        story.append(Paragraph(_text(issue.get("code", ""), 60) + " | " + _text(location, 250), small))
    if len(report["issues"]) > 200:
        story.append(Paragraph("이슈 " + str(len(report["issues"]) - 200) +
                               "개 표시 생략. 상세 JSON을 확인하세요.", style))
    if not report["issues"]:
        story.append(Paragraph("이슈 없음", style))
    story.append(Paragraph("검사 파일 목록", heading))
    rows = [[Paragraph("상대 경로", small), Paragraph("크기", small), Paragraph("SHA-256 앞 22자리", small)]]
    for rec in report["files"][:900]:
        if not isinstance(rec, dict):
            raise InputError("bad PDF file record")
        digest = rec.get("sha256") or "NOT_READ"
        if digest != "NOT_READ" and (not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest)):
            raise InputError("bad PDF SHA")
        rows.append([Paragraph(_text(rec.get("path", ""), 260), small),
                     Paragraph(_text(rec.get("size", "")), small),
                     Paragraph(_text(digest[:22]), small)])
    width = A4[0] - 84
    table = LongTable(rows, colWidths=[width*.56, width*.14, width*.30], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7edf1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#607080")),
        ("LINEBELOW", (0, 1), (-1, -1), .15, colors.HexColor("#d0d8df")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    if len(report["files"]) > 900:
        story.append(Paragraph("파일 " + str(len(report["files"]) - 900) +
                               "개 표시 생략. 전체 SHA-256은 JSON을 확인하세요.", style))
    def footer(canvas, page):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#53616f"))
        canvas.setFont(font, 8)
        canvas.drawString(42, 27, "원본 읽기 전용 / 서명 없는 검사 증거")
        canvas.drawRightString(A4[0] - 42, 27, str(page.page))
        canvas.restoreState()
    try:
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    except (ValueError, KeyError, TypeError) as exc:
        raise InputError("PDF layout rejected") from exc
    raw = buffer.getvalue()
    if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-128:] or len(raw) > MAX_PDF_BYTES:
        raise InputError("PDF bytes malformed or too large")
    return raw


def create_pdf_only(path: Path, raw: bytes, root: Path) -> None:
    if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-128:] or len(raw) > MAX_PDF_BYTES:
        raise InputError("invalid PDF bytes")
    target = path.absolute()
    if os.path.lexists(target):
        raise InputError("PDF destination exists; create-only")
    parent = target.parent
    if not parent.is_dir() or _is_link(parent.lstat()):
        raise InputError("PDF parent must be an existing non-reparse directory")
    resolved, source = parent.resolve(strict=True), root.resolve(strict=True)
    if resolved == source or source in resolved.parents:
        raise InputError("PDF cannot be written inside source")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
