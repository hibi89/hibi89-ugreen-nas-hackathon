"""G22: Build a strictly isolated creator-based UGREEN Round 1 PREVIEW.

The pinned creator-review Skill has a user-reported official static-pass.
This script appends required entrant disclosures in a *staging copy*, so
the augmented version is NOT official-checker validated. No publishing,
checkout mutation, NAS requests, external data or Devpost operations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from check_round1_proposal import JSON_PATH, errors, render_markdown, word_count
from round1_candidate_bundle import validate_pdf
from round1_package_audit import SECRET, UNFINISHED
from render_round1_proposal_pdf import render

ROOT = Path(__file__).resolve().parents[1]
SKILL_SHA256 = "164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead"
CHECK_JSON_SHA256 = "92a6891b0889a89cd09f16ed960e9f72a4df33f8114ce0ee22b9beefeff50140"
REVIEW_COMMIT = "7af2cb750b37826fb02a00e2d45cb73f3a85c239"
LIMIT_SKILL = 1_000_000
LIMIT_ZIP = 10 * 1024 * 1024
Q8_ANSWER = (
    "The official UGOS Skill Creation Tool generated the initial ProjectReady NAS "
    "Skill in Codex. Codex reported a static-pass with zero errors or warnings; "
    "the reviewed source and checker JSON hashes were independently matched. "
    "A safer expert-delegation revision is drafted. No registered Agent or real NAS "
    "has been tested; effective permissions, listing completeness, and model "
    "data-processing location remain unverified."
)
DISCLOSURES = """

# Development provenance and third-party disclosures

- **New hackathon functionality:** Original entrant-directed read-only ProjectReady NAS orchestration: owner-scoped file checklists, conservative evidence states, uncertain-version review, delegated NAS file/document experts, and fail-closed readiness reports.
- **AI development tools:** OpenAI ChatGPT (GPT-6) assisted workflow design, safety policies, offline review and drafting. OpenAI Codex, using the official UGREEN Uliya Skill Creation Tool, generated the initial Skill and assisted a subsequent reviewed update. The human entrant directs and must approve the final submission.
- **Third-party platform and licenses:** The planned platform dependency is the official UGREEN UGOS/Uliya Skill Kit, published at https://ai.ugreen.com/pages/hackathon-starter-kit . No UGREEN SDK source, executable, additional third-party code library or AI model weights are bundled in this Markdown-only package. Applicable UGREEN tool/service license rights are still pending entrant verification; this preview is not authorized for publication.
- **Data and external services:** Future operations require explicit per-folder permission and separately approved document references. No customer NAS information was accessed during drafting. No independent outbound integration is intentionally configured. Whether Uliya model processing happens locally or in a cloud service is unverified and must not be advertised as local-only.
- **Validation and ownership limits:** An original official-Creator source and an edited candidate were statically checked in participant Codex reports; this disclosure-augmented preview has **not** been rerun through the official checker. Actual NAS runtime, registered Agent permissions, contents privacy and the entrant's original-work/licensing approval remain unverified. This is a DRAFT, not UGREEN certification or a Devpost submission.
"""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verified_creator_source(skill: Path, checker_path: Path) -> bytes:
    """Require the pinned real GitHub review files, never a synthetic replacement."""
    if skill.is_symlink() or skill.parent.is_symlink() or not skill.is_file():
        raise ValueError("Creator review SKILL.md is missing, nonregular or symlinked")
    if skill.parent.name != "projectready-nas" or skill.name != "SKILL.md":
        raise ValueError("Not the expected creator review Skill path")
    if checker_path.is_symlink() or not checker_path.is_file():
        raise ValueError("Review checker JSON missing or symlinked")
    source = skill.read_bytes()
    checker_raw = checker_path.read_bytes()
    if len(source) > LIMIT_SKILL or digest(source) != SKILL_SHA256:
        raise ValueError("Review Skill content differs from pinned SHA256")
    if digest(checker_raw) != CHECK_JSON_SHA256:
        raise ValueError("Review checker JSON content differs from pinned SHA256")
    checker = json.loads(checker_raw)
    summary = checker.get("summary") or {}
    files = checker.get("files") or []
    if (checker.get("status") != "static-pass" or
        summary.get("errors") != 0 or summary.get("warnings") != 0 or
        summary.get("info") != 0 or len(files) != 1 or
        files[0].get("path") != "SKILL.md" or
        files[0].get("sha256") != SKILL_SHA256):
        raise ValueError("Checker report does not agree with the exact official source")
    decoded = source.decode("utf-8")
    front = re.match(r"\A---\s*\n(.*?)\n---\s*\n", decoded, re.S)
    if (not front or not re.search(r"(?m)^name:\s*projectready-nas\s*$", front.group(1)) or
        re.search(r"\]\(references/[^)]*\.md\)", decoded)):
        raise ValueError("Expected official-generated one-file Skill with no linked references")
    if SECRET.search(decoded) or UNFINISHED.search(decoded):
        raise ValueError("Unexpected secret or unfinished placeholder")
    return source


def candidate_bytes(original: bytes) -> bytes:
    text = original.decode("utf-8").rstrip() + "\n" + DISCLOSURES.lstrip()
    if SECRET.search(text) or UNFINISHED.search(text):
        raise ValueError("Candidate contains possible secret or unfinished placeholder")
    raw = text.encode("utf-8")
    if len(raw) > LIMIT_SKILL:
        raise ValueError("Creator candidate exceeds 1 MB")
    return raw


def creator_proposal() -> dict:
    d = copy.deepcopy(json.loads(JSON_PATH.read_text(encoding="utf-8")))
    if "No official Uliya validator" not in d["questions"][7]["answer"]:
        raise ValueError("Original Q8 has changed; manually reconcile first")
    d["questions"][7]["answer"] = Q8_ANSWER
    d["disclosures"]["ai_assistance"] = (
        "OpenAI ChatGPT (GPT-6) helped design and review the Skill; OpenAI Codex "
        "used the official UGREEN UGOS Skill Creation Tool to generate the initial "
        "Skill and reported a static check pass. Human entrant retains editorial "
        "and submission control."
    )
    d["disclosures"]["platform"] = (
        "Official UGREEN UGOS/Uliya v0.7.3 Skill Kit, https://ai.ugreen.com/pages/hackathon-starter-kit , "
        "is referenced, not bundled. Applicable tool/service license terms and "
        "entrant intellectual-property rights still require review."
    )
    d["disclosures"]["other_libraries"] = (
        "No external executable library, vendor SDK source, scripts or binaries "
        "in the Skill ZIP. Python standard-library tools were used only for "
        "independent offline test prototyping, not NAS execution."
    )
    d["proof_status"]["creator_static_checker"] = (
        "CODEX_REPORTED_STATIC_PASS_0_0_REVIEW_SOURCE_SHA_VERIFIED_"
        "DISCLOSURE_AUGMENTED_CANDIDATE_NOT_OFFICIALLY_CHECKED"
    )
    d["substantive_words"] = sum(word_count(q["answer"]) for q in d["questions"])
    problems = errors(d, render_markdown(d))
    if problems:
        raise ValueError("Official 10-question proposal invalid: " + "; ".join(problems))
    return d


def zip_only_skill(skill_raw: bytes) -> bytes:
    """Deliberately no inherited references or review JSON in contest ZIP."""
    memory = io.BytesIO()
    info = zipfile.ZipInfo("projectready-nas/SKILL.md", (1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as f:
        f.writestr(info, skill_raw)
    archive = memory.getvalue()
    if len(archive) > LIMIT_ZIP:
        raise ValueError("ZIP above 10 MB")
    with zipfile.ZipFile(io.BytesIO(archive)) as f:
        if f.namelist() != ["projectready-nas/SKILL.md"]:
            raise ValueError("ZIP contains any unexpected entries")
        zinfo = f.infolist()[0]
        if zinfo.flag_bits & 1 or zinfo.is_dir() or zinfo.file_size > LIMIT_SKILL:
            raise ValueError("Unreviewable ZIP entry")
        if f.read(zinfo) != skill_raw:
            raise ValueError("ZIP not byte-equal to staged Skill")
    return archive


def build(skill: Path, checker: Path, out_dir: Path) -> dict:
    original = verified_creator_source(skill, checker)
    augmented = candidate_bytes(original)
    d = creator_proposal()
    out_dir = out_dir.resolve()
    if out_dir == skill.parent.resolve() or out_dir == checker.parent.resolve():
        raise ValueError("Refusing to overwrite official review source folder")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "ProjectReady_Creator_Proposal_DRAFT.pdf"
    zip_path = out_dir / "ProjectReady_Creator_Skill_DRAFT.zip"
    md_path = out_dir / "ProjectReady_Creator_Proposal_DRAFT.md"
    json_path = out_dir / "ProjectReady_Creator_Proposal_DRAFT.json"
    render(pdf_path, proposal=d)
    pdf_info = validate_pdf(pdf_path, d["questions"], d["disclosures"])
    archive = zip_only_skill(augmented)
    zip_path.write_bytes(archive)
    md_path.write_text(render_markdown(d), encoding="utf-8")
    json_path.write_text(json.dumps(d, indent=2, ensure_ascii=False)+"\n",encoding="utf-8")
    result = {
        "assessment":"OFFLINE_CREATOR_SOURCE_PREVIEW_PASS_RELEASE_NOT_APPROVED",
        "candidate_source":"pinned official Creator review branch and commit",
        "review_commit":REVIEW_COMMIT,
        "original_generated_skill_review_sha256":digest(original),
        "official_static_checker_report":"PARTICIPANT_CODEX_REPORTED_STATIC_PASS_0_ERRORS_0_WARNINGS_FOR_ORIGINAL_REVIEW_SHA_ONLY",
        "staged_skill_with_disclosure_sha256":digest(augmented),
        "staged_skill_official_checker":"NOT_RERUN_AFTER_DISCLOSURE_AUGMENTATION",
        "skill_zip_sha256":digest(archive),
        "skill_zip_bytes":len(archive),
        "skill_zip_entries":[{"path":"projectready-nas/SKILL.md","sha256":digest(augmented),"bytes":len(augmented)}],
        "pdf":pdf_info,
        "proposal_substantive_words":d["substantive_words"],
        "proposal_word_limit":500,
        "disclosures_in_pdf_and_skill":True,
        "original_four_file_skill_modified":False,
        "human_entrant_approval":"PENDING",
        "rights_and_license_review":"NOT_CLEARED",
        "expert_agent_permissions":"NOT_VERIFIED",
        "nas_runtime":"NOT_RUN",
        "devpost":"NOT_SUBMITTED",
        "skillhub":"NOT_PUBLISHED",
    }
    (out_dir / "ProjectReady_Creator_Preview_Manifest.json").write_text(
        json.dumps(result, indent=2)+"\n",encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--review-skill", required=True, type=Path)
    p.add_argument("--review-checker", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args()
    try:
        result=build(a.review_skill,a.review_checker,a.output_dir)
        print("CREATOR ROUND1 ISOLATED PREVIEW PASS",result["proposal_substantive_words"],
            "answer words; ZIP",result["skill_zip_bytes"],"bytes;",
            "PDF",result["pdf"]["bytes"],"bytes; NOT_APPROVED_NOT_SUBMITTED")
        return 0
    except (ValueError, OSError, UnicodeError, RuntimeError, zipfile.BadZipFile) as exc:
        print("CREATOR ROUND1 ISOLATED PREVIEW FAIL:",str(exc)[:360])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
