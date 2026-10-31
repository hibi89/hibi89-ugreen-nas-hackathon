"""Owner-local G103 PDF answer-text parity; NOT the official Uliya Checker.

Requires PyMuPDF for actual PDF extraction. No NAS, network, or private data logs.
A PASS proves ordered normalized literal answer text is present, NOT visual,
semantic, or official vendor parity. The owner review gate remains HOLD.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAX_PDF_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 128 * 1024


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def check(pdf_bytes: bytes, source: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PYMUPDF_REQUIRED") from exc
    questions = source.get("questions") if type(source) is dict else None
    if (type(questions) is not list or len(questions) != 10
            or any(type(q) is not dict
                   or type(q.get("question")) is not str or not q["question"].strip()
                   or type(q.get("answer")) is not str or not q["answer"].strip()
                   for q in questions)):
        raise ValueError("INVALID_TEN_ANSWERS")
    answers = [normalize(q["answer"]) for q in questions]
    if len(set(answers)) != 10:
        raise ValueError("DUPLICATE_ANSWERS")
    if (type(pdf_bytes) is not bytes or not 0 < len(pdf_bytes) <= MAX_PDF_BYTES
            or not pdf_bytes.startswith(b"%PDF-")):
        raise ValueError("INVALID_PDF_SIZE_OR_SIGNATURE")
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.needs_pass or doc.page_count < 1:
                raise ValueError("PDF_LOCKED_OR_EMPTY")
            extracted = normalize(" ".join(page.get_text(sort=True) for page in doc))
    except (fitz.FileDataError, fitz.EmptyFileError, RuntimeError) as exc:
        raise ValueError("PDF_UNREADABLE") from exc
    # Require all answers, in source order, as distinct whole-text spans.
    # This prevents substring-only false positives and out-of-order proposals.
    cursor = 0
    for answer in answers:
        found = re.search(r"(?<!\w)" + re.escape(answer) + r"(?!\w)", extracted[cursor:])
        if found is None:
            raise ValueError("PDF_ANSWER_MISMATCH_OR_ORDER")
        cursor += found.end()
    return {"status": "PDF_TEXT_PARITY_PASS_NOT_OFFICIAL", "matched_answers": 10,
            "official_checker_executed": False, "release_gate": "HOLD"}


def _read_bounded(path: Path, limit: int) -> bytes:
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= limit):
        raise ValueError("FILE_MISSING_OR_OUT_OF_BOUNDS")
    data = path.read_bytes()
    if not 0 < len(data) <= limit:
        raise ValueError("FILE_MISSING_OR_OUT_OF_BOUNDS")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner-local PDF answer-text parity; NOT vendor validation")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pdf_bytes = _read_bounded(args.pdf, MAX_PDF_BYTES)
        source_bytes = _read_bounded(args.source, MAX_SOURCE_BYTES)
        result = check(pdf_bytes, json.loads(source_bytes.decode("utf-8")))
        code = 0
    except RuntimeError as exc:
        # Optional dependency missing must not emit a traceback or file path.
        result = {"status": "PDF_PARITY_DEPENDENCY_MISSING" if str(exc) == "PYMUPDF_REQUIRED"
                  else "PDF_PARITY_REFUSED", "official_checker_executed": False, "release_gate": "HOLD"}
        code = 2
    except (ValueError, OSError, UnicodeError, TypeError, json.JSONDecodeError):
        result = {"status": "PDF_PARITY_REFUSED", "official_checker_executed": False,
                  "release_gate": "HOLD"}
        code = 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
