"""Owner-local G103 PDF answer-text parity; NOT the official Uliya Checker.

Requires PyMuPDF. Never uploads the owner-private PDF or proposal source.
"""
import argparse
import json
import re
from pathlib import Path


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def check(pdf_bytes: bytes, source: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PYMUPDF_REQUIRED") from exc
    questions = source.get("questions") if isinstance(source, dict) else None
    if (type(questions) is not list or len(questions) != 10
            or any(type(q) is not dict or type(q.get("answer")) is not str
                   or not q["answer"].strip() for q in questions)):
        raise ValueError("INVALID_TEN_ANSWERS")
    if not isinstance(pdf_bytes, bytes) or not 0 < len(pdf_bytes) <= 1024 * 1024 or not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("INVALID_PDF_SIZE_OR_SIGNATURE")
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.needs_pass or doc.page_count < 1:
                raise ValueError("PDF_LOCKED_OR_EMPTY")
            extracted = normalize(" ".join(page.get_text(sort=True) for page in doc))
    except (fitz.FileDataError, fitz.EmptyFileError, RuntimeError) as exc:
        raise ValueError("PDF_UNREADABLE") from exc
    answers = [normalize(q["answer"]) for q in questions]
    if len(set(answers)) != 10:
        raise ValueError("DUPLICATE_ANSWERS")
    if not all(answer in extracted for answer in answers):
        raise ValueError("PDF_ANSWER_MISMATCH")
    return {"status": "PDF_TEXT_PARITY_PASS_NOT_OFFICIAL", "matched_answers": 10,
            "official_checker_executed": False, "release_gate": "HOLD"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local PDF text parity; NOT vendor validation")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = check(args.pdf.read_bytes(), json.loads(args.source.read_text(encoding="utf-8")))
        code = 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError):
        result = {"status": "PDF_PARITY_REFUSED", "official_checker_executed": False, "release_gate": "HOLD"}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
