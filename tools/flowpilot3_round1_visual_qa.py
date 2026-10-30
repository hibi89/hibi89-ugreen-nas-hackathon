"""Independent G75 first-page PDF geometry and visual-preview proof (NOT release).

This is a layout/text inspection of an already built owner-review PDF, not an
official UGOS/Uliya/Devpost audit. Produces a PNG that can be visually inspected.
No customer data, PDF editing, external upload, NAS or official Creator calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def inspect(pdf: Path, manifest: Path, output: Path) -> dict:
    import pymupdf

    if any(p.is_symlink() or not p.is_file() for p in (pdf, manifest)):
        raise ValueError("Missing/symlinked input")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    pdf_raw = pdf.read_bytes()
    if (data.get("status") != "OWNER_REVIEW_NOT_SUBMITTED"
            or data.get("pdf_sha256") != hashlib.sha256(pdf_raw).hexdigest()
            or data.get("official_creator") != "NOT_RUN"
            or data.get("nas_runtime") != "NOT_RUN"
            or data.get("devpost_submitted") is not False
            or data.get("legal_rights_released") is not False
            or data.get("questions") != 10
            or not 0 < data.get("substantive_english_words", 501) <= 500):
        raise ValueError("Unrecognized or mutable draft artifact claim")

    with pymupdf.open(stream=pdf_raw, filetype="pdf") as document:
        if document.needs_pass or len(document) != 1:
            raise ValueError("Expected readable one-page owner review PDF")
        page = document[0]
        bounds = page.rect
        text = page.get_text(sort=True)
        if not all(f"Q{i}." in text for i in range(1, 11)):
            raise ValueError("Missing official numbered question in visual PDF")
        if "NOT SUBMITTED" not in text or "NOT_RUN" not in text:
            raise ValueError("Unverified state omitted from visual PDF")
        blocks = [b for b in page.get_text("blocks")
                  if len(b) >= 7 and b[6] == 0 and str(b[4]).strip()]
        if not blocks:
            raise ValueError("No readable text bounding boxes")
        pad = 8
        if any(not (pad <= b[0] < b[2] <= bounds.width - pad
                    and pad <= b[1] < b[3] <= bounds.height - pad)
               for b in blocks):
            raise ValueError("PDF text clipped or too near page edge")
        structure = page.get_text("dict")
        sizes = [round(float(span["size"]), 2)
                 for section in structure.get("blocks", [])
                 if "lines" in section
                 for line in section["lines"]
                 for span in line["spans"]
                 if span["text"].strip()]
        if not sizes or min(sizes) < 7.0:
            raise ValueError("PDF body font too small or missing")
        # Write preview create-only; never clobber reviewed visual inspection.
        if output.is_symlink() or output.exists():
            raise ValueError("Existing preview output")
        pixel_map = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        pixel_map.save(str(output))
        preview_hash = hashlib.sha256(output.read_bytes()).hexdigest()
        return {
            "status": "OWNER_REVIEW_PDF_GEOMETRY_PASS_NOT_RELEASE",
            "source_pdf_sha256": hashlib.sha256(pdf_raw).hexdigest(),
            "preview_png_sha256": preview_hash,
            "text_blocks_checked": len(blocks),
            "min_font_pt": min(sizes),
            "max_font_pt": max(sizes),
            "pages": len(document),
            "ten_questions_visible_in_extracted_text": True,
            "clipped_text_blocks_found": 0,
            "manual_visual_editorial_review": "PENDING",
            "official_creator": "NOT_RUN",
            "registered_nas_agent": "NOT_RUN",
            "devpost_submitted": False,
            "release_gate": "HOLD",
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render exact G75 owner PDF as PNG, no release")
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.pdf, args.manifest, args.preview)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, ImportError):
        print(json.dumps({"status": "OWNER_REVIEW_VISUAL_QA_REFUSED",
                          "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
