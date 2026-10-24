"""Build an inspectable DRAFT Round 1 ZIP + PDF manifest. Never submit.

Actual input PDF gets parsed with pypdf: validates size, extractability,
ten official question texts, and the authored first/last answer.
Only direct-linked Markdown references enter the ZIP; no SDK/runtime code.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from check_round1_proposal import errors as proposal_errors
from check_round1_proposal import JSON_PATH, MD_PATH
from round1_package_audit import audit_skill, build_candidate_zip, PackageError

ROOT = Path(__file__).resolve().parents[1]
PDF_LIMIT = 1_000_000
ZIP_LIMIT = 10 * 1024 * 1024


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_candidate_zip(skill_folder: Path, raw_zip: bytes) -> list[dict]:
    audit = audit_skill(skill_folder)
    if len(raw_zip) > ZIP_LIMIT:
        raise ValueError("Round 1 candidate ZIP exceeds the size limit")
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = zf.namelist()
        expected = [f"{skill_folder.name}/{path}" for path in audit["files"]]
        if names != expected or len(names) != len(set(names)):
            raise ValueError("Round 1 ZIP has extra, reordered or missing entries")
        files = []
        for filename, relative in zip(names, audit["files"]):
            info = zf.getinfo(filename)
            if info.is_dir() or info.flag_bits & 1:
                raise ValueError("Directory or encrypted ZIP member")
            if info.file_size > 1024 * 1024:
                raise ValueError("Uncompressed member > 1MB")
            content = zf.read(info)
            original = (skill_folder / relative).read_bytes()
            if content != original:
                raise ValueError("ZIP member differs from inspected original")
            files.append({"path": filename, "bytes": len(content), "sha256": sha256(content)})
        return files


def validate_pdf(pdf: Path, questions: list[dict]) -> dict:
    content = pdf.read_bytes()
    if len(content) > PDF_LIMIT or not content.startswith(b"%PDF-") or b"%%EOF" not in content[-1024:]:
        raise ValueError("Invalid or >1 MB PDF")
    # Never accept only PDF magic; the PDF must be parsed and searchable.
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf required to verify PDF pages and official questions") from exc
    try:
        doc = PdfReader(io.BytesIO(content), strict=True)
        if not 1 <= len(doc.pages) <= 5 or doc.is_encrypted:
            raise ValueError("Bad page count or encrypted PDF")
        text = re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in doc.pages))
    except Exception as exc:
        raise ValueError("PDF cannot be parsed and searched") from exc
    for q in questions:
        prompt = re.sub(r"\s+", " ", q["prompt"])
        if prompt not in text:
            raise ValueError(f"Proposal PDF question {q['number']} absent; stale draft?")
    for q in (questions[0], questions[-1]):
        prefix = re.sub(r"\s+", " ", q["answer"])[:35]
        if prefix not in text:
            raise ValueError("PDF does not carry the current authored answer")
    if "DRAFT" not in text or "NOT SUBMITTED" not in text:
        raise ValueError("Draft PDF missing non-submission disclosure")
    return {"name": pdf.name, "pages": len(doc.pages),
            "bytes": len(content), "sha256": sha256(content),
            "official_questions_in_pdf": 10, "content_extractable": True}


def draft_bundle(skill_dir: Path, pdf: Path | None = None) -> tuple[bytes, dict]:
    proposal = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    issues = proposal_errors(proposal, MD_PATH.read_text(encoding="utf-8"))
    if issues:
        raise ValueError("Round 1 proposal invalid: " + "; ".join(issues))
    raw = build_candidate_zip(skill_dir)
    files = validate_candidate_zip(skill_dir, raw)
    result = {
        "kind": "UGREEN_ROUND1_PREVIEW_NOT_SUBMITTED",
        "source": "official Devpost Round 1 PDF + initial Skill ZIP rules",
        "official_rules_url": "https://ugreenhackathon.devpost.com/rules",
        "sha256_zip": sha256(raw),
        "zip_bytes": len(raw),
        "zip_contains_markdown_only": True,
        "zip_member_count": len(files),
        "zip_members": files,
        "proposal_question_count": 10,
        "proposal_answer_words": proposal["substantive_words"],
        "proposal_word_limit": 500,
        "pdf": validate_pdf(pdf, proposal["questions"]) if pdf else None,
        "official_uliya_checker": "NOT_RUN",
        "live_nas_validation": "NOT_RUN",
        "license_and_dataflow_review": "NOT_CLEARED",
        "entrant_approval": "PENDING",
        "devpost_submission": "NOT_SUBMITTED",
    }
    return raw, result


def main() -> int:
    parser = argparse.ArgumentParser(description="Local/CI candidate, NOT official validation or submission")
    parser.add_argument("--skill-dir", type=Path, default=ROOT/"skill/projectready-nas")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        archive, manifest = draft_bundle(args.skill_dir, args.pdf)
        if args.output_dir.resolve() == args.skill_dir.resolve():
            raise ValueError("Draft package must not be written into the Skill folder")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir/"ProjectReady_NAS_Skill_DRAFT.zip").write_bytes(archive)
        (args.output_dir/"Round1_DRAFT_Manifest.json").write_text(json.dumps(manifest, indent=2)+"\n",encoding="utf-8")
        print("ROUND1 OFFLINE PREVIEW PASS:",
              f"{manifest['zip_member_count']} linked Markdown members;",
              f"ZIP {manifest['zip_bytes']} bytes;",
              f"PDF {manifest['pdf']['pages']} pages / {manifest['pdf']['bytes']} bytes;",
              f"{manifest['proposal_answer_words']}/500 answer words; NOT_SUBMITTED")
        return 0
    except (ValueError, PackageError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
        print("ROUND1 OFFLINE PREVIEW FAIL:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
