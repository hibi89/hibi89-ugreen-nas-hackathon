"""G157: pinned owner-private G147 and derived G157 PDF content review.

NOT official Uliya Checker, entrant rights approval or Devpost submission.
Public GitHub contains only hashes/source, never owner PDF bytes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

G147_SHA256 = "bf5319f0b840747e53d3a84f78e4006bc932a4d5d2bd0671c9c43c6f3877b90f"
G157_SHA256 = "d5a5a5ac422140a168e18dfef8c3efd5abeced36c2fdf13ee2704bbcc6dd5d5a"
PINS = {"g147-owner-review": G147_SHA256, "g157-unapproved-draft": G157_SHA256}
MAX_PDF_BYTES = 1_000_000
QUESTION = re.compile(r"(?m)^\s*(0?[1-9]|10)(?:\.\s+|\s*/\s+)([^\n]+)")
WORD = re.compile(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b")
INTERNAL_LABEL = re.compile(r"\bOWNER\s+REVIEW\b|\bG147\s+REVIEW\b|\bNOT\s+SUBMITTED\b", re.I)
DISCLOSURE = re.compile(r"(?im)^\s*(?:disclosures\s*\(|disclosures\s*&\s*dependencies)")


class ProposalRefused(ValueError):
    """Sanitized fail-closed denial; never print private owner excerpts/paths."""


def audit_text(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ProposalRefused("PDF_TEXT_EMPTY")
    cutoff = DISCLOSURE.search(text)
    if not cutoff:
        raise ProposalRefused("DISCLOSURE_SECTION_REQUIRED")
    substantive = text[:cutoff.start()]
    found = list(QUESTION.finditer(substantive))
    if [int(m.group(1)) for m in found] != list(range(1, 11)):
        raise ProposalRefused("TEN_NUMBERED_ANSWERS_REQUIRED")
    answer_words = []
    for i, m in enumerate(found):
        next_start = found[i + 1].start() if i + 1 < len(found) else len(substantive)
        body = substantive[m.end():next_start]
        count = len(WORD.findall(body))
        if count < 5:
            raise ProposalRefused("ANSWER_EMPTY_OR_TOO_SHORT")
        answer_words.append(count)
    total_words = sum(answer_words)
    if total_words > 500:
        raise ProposalRefused("TOTAL_ANSWERS_EXCEED_500")
    internal_markers = bool(INTERNAL_LABEL.search(text))
    disclosure_text = text[cutoff.start():].casefold()
    if not all(term in disclosure_text for term in ("chatgpt", "ugreen", "rights")):
        raise ProposalRefused("AI_PLATFORM_RIGHTS_DISCLOSURE_REQUIRED")
    return {
        "schema": "flowpilot-g157-round1-pdf-review-v1",
        "status": "INTERNAL_REVIEW_LABELS_FOUND" if internal_markers
                  else "JUDGE_FACING_PDF_TEXT_REVIEW_PASS_NOT_RELEASED",
        "answer_count": len(found), "substantive_answer_word_count": total_words,
        "pdf_text_verified": True, "owner_internal_labels_present": internal_markers,
        "official_checker_executed": False, "entrant_rights_approved": False,
        "devpost_submitted": False, "release_gate": "HOLD",
        "private_content_returned": False,
    }


def audit_pdf(pdf_bytes: bytes, profile: str) -> dict:
    if profile not in PINS or type(pdf_bytes) is not bytes or not 0 < len(pdf_bytes) < MAX_PDF_BYTES:
        raise ProposalRefused("INVALID_PROFILE_OR_SIZE")
    if sha256(pdf_bytes).hexdigest() != PINS[profile]:
        raise ProposalRefused("EXACT_PDF_SHA_MISMATCH")
    try:
        import fitz
    except ImportError as exc:
        raise ProposalRefused("PYMUPDF_REQUIRED") from exc
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.needs_pass or doc.page_count != 1:
                raise ProposalRefused("UNREVIEWABLE_PDF")
            result = audit_text(doc[0].get_text(sort=True))
    except (RuntimeError, ValueError, AttributeError, TypeError) as exc:
        raise ProposalRefused("UNVERIFIED_PDF_TEXT") from exc
    result["profile"] = profile
    result["pdf_sha256"] = PINS[profile]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G157 PDF review; NEVER release approval")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--profile", choices=tuple(PINS), required=True)
    args = parser.parse_args(argv)
    try:
        path = args.pdf
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < MAX_PDF_BYTES:
            raise ProposalRefused("LOCAL_PDF_MISSING_OR_UNSAFE")
        result = audit_pdf(path.read_bytes(), args.profile)
        code = 2 if result["owner_internal_labels_present"] else 0
    except (OSError, ProposalRefused, ValueError, TypeError):
        result = {"schema": "flowpilot-g157-round1-pdf-review-v1",
                  "status": "PDF_REVIEW_REFUSED", "official_checker_executed": False,
                  "release_gate": "HOLD", "private_content_returned": False}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
