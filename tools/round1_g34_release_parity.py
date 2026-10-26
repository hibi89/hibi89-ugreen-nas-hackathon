"""G34: build exact G32 / G33-proven Round 1 owner REVIEW package, never submit.

The original Round 1 proposal, G29 PDF/ZIP and all prior Skill candidates
remain immutable. The official Uliya checker static-pass applies ONLY to
the exact G32 sha256 recorded in an independently-run G33 action.
"""
from __future__ import annotations
import argparse, copy, hashlib, io, json, zipfile
from pathlib import Path

from check_round1_proposal import JSON_PATH, errors, render_markdown, word_count
from render_round1_proposal_pdf import render
from round1_candidate_bundle import validate_pdf
from round1_official_creator_preview import zip_only_skill

ROOT = Path(__file__).resolve().parents[1]
G32 = ROOT / "docs/submission/checker_inputs/G32_20261026/projectready-nas/SKILL.md"
G33 = ROOT / "docs/submission/evidence/G33_FIRST_PARTY_G32_OFFICIAL_CHECKER_20261026.json"
G32_SHA = "2baf409f990e8b5ba78bdb378b86dbf81ca83eec2dfa4cc605e1642ffd38feaa"
G33_RUN = 40306076413
G33_VENDOR_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"

Q8 = (
    "The entrant reports using UGREEN's official UGOS Skill Creation Tool in Codex "
    "for the original Skill. The exact G32 revision passed the first-party Uliya "
    "static checker in isolated GitHub Actions (exit 0, zero diagnostics). "
    "Real NAS and Expert Agent access, permissions, model data flow, "
    "third-party rights, and submission approval remain unverified or pending."
)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def pinned_source() -> bytes:
    if G32.is_symlink() or not G32.is_file() or G33.is_symlink() or not G33.is_file():
        raise ValueError("Required regular source and first-party evidence are missing")
    source = G32.read_bytes()
    if digest(source) != G32_SHA or len(source) != 14389:
        raise ValueError("G32 exact verified SHA/size changed; no inherited static-pass")
    j = json.loads(G33.read_text(encoding="utf-8"))
    s = j.get("checker_summary", {})
    if (j.get("evidence_type") != "FIRST_PARTY_CHECKER_RUN_ISOLATED_NO_NETWORK"
        or j.get("candidate") != "G32_20261026/projectready-nas/SKILL.md"
        or j.get("skill_sha256_before_after") != G32_SHA
        or j.get("bytes") != len(source)
        or j.get("vendor_archive_sha256") != G33_VENDOR_SHA
        or j.get("workflow_run_id") != G33_RUN
        or j.get("checker_exit_code") != 0
        or j.get("checker_result_status") != "static-pass"
        or s != {"errors": 0, "warnings": 0, "info": 0}
        or j.get("diagnostics_codes") != []
        or not j.get("first_party_checker_executed")
        or j.get("real_nas_or_expert_agent_executed") is not False
        or j.get("unapproved_external_network_access") is not False
        or j.get("devpost_submitted") is not False
        or not isinstance(j.get("checker_json_sha256"), str)
        or len(j["checker_json_sha256"]) != 64):
        raise ValueError("G33 official static checker evidence does not support exact G32")
    return source

def staged_proposal() -> dict:
    p = copy.deepcopy(json.loads(JSON_PATH.read_text(encoding="utf-8")))
    if ("No official Uliya validator" not in p["questions"][7]["answer"]
        or p["proof_status"].get("official_validator") != "NOT_RUN"):
        raise ValueError("Original proposal unexpectedly changed; review manually")
    p["dated_kst"] = "2026-10-26"
    p["questions"][7]["answer"] = Q8
    p["disclosures"]["ai_assistance"] = (
        "OpenAI ChatGPT assisted design, review, coding and tests. The entrant reports "
        "that Codex used UGREEN's official Skill Creation Tool to produce the initial "
        "Skill; human entrant controls final rights and submission."
    )
    p["disclosures"]["platform"] = (
        "UGREEN UGOS/Uliya public Skill Kit v0.7.3 is referenced, not bundled; its "
        "first-party static checker ran in a network-isolated CI container on exact "
        "G32. Platform license, service terms, live Agent availability and data "
        "processing location are not cleared or verified."
    )
    p["disclosures"]["other_libraries"] = (
        "The ZIP contains one Markdown SKILL.md only. Python, ReportLab and pypdf "
        "run in the offline development/packaging pipeline, not on a NAS or in "
        "the delivered Skill; no official vendor binaries are redistributed."
    )
    p["disclosures"]["data_flow"] = (
        "No user NAS files or credentials have been accessed. Any future owner-scoped "
        "file listing requires permission; document content needs separate consent. "
        "Local versus cloud processing and actual runtime permissions are unverified."
    )
    p["proof_status"]["official_validator"] = "G32_EXACT_SHA_FIRST_PARTY_STATIC_PASS"
    p["proof_status"]["g34_release_status"] = "OWNER_REVIEW_PENDING_NOT_SUBMITTED"
    p["proof_status"]["nas"] = "NOT_RUN"
    p["proof_status"]["devpost"] = "NOT_SUBMITTED"
    p["proof_status"]["participant_approval"] = "PENDING"
    p["substantive_words"] = sum(word_count(q["answer"]) for q in p["questions"])
    # The canonical legacy validator deliberately only accepts NOT_RUN on the
    # original draft. Temporarily mask this one proof flag to reuse its strict
    # 10-prompt/500-word/disclosure checks, without weakening it globally.
    validation = copy.deepcopy(p)
    validation["proof_status"]["official_validator"] = "NOT_RUN"
    issues = errors(validation, render_markdown(validation))
    if issues:
        raise ValueError("Proposal format rejected: " + "; ".join(issues))
    if not 1 <= p["substantive_words"] <= 500:
        raise ValueError("Invalid 500-word constraint")
    return p

def build(out_dir: Path) -> dict:
    src = pinned_source()
    proposal = staged_proposal()
    dest = out_dir.resolve()
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError("G34 only writes outside repository")
    dest.mkdir(parents=True, exist_ok=True)
    pdf_path = dest / "ProjectReady_G34_Round1_OWNER_REVIEW_NOT_SUBMITTED.pdf"
    zip_path = dest / "ProjectReady_G34_G32_Skill_OWNER_REVIEW_NOT_SUBMITTED.zip"
    archive = zip_only_skill(src)
    zip_path.write_bytes(archive)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.namelist() != ["projectready-nas/SKILL.md"]:
            raise ValueError("Unexpected ZIP member")
        if z.read("projectready-nas/SKILL.md") != src:
            raise ValueError("ZIP content is not first-party checked G32")
    # Shared renderer guards the original unverified canonical proposal status.
    # The staged JSON and manifest retain the real G32 pass; this local copy
    # adapts only that legacy guard (not the rendered answers/disclosures).
    render_view = copy.deepcopy(proposal)
    render_view["proof_status"]["official_validator"] = "NOT_RUN"
    render(pdf_path, proposal=render_view)
    pdf = validate_pdf(pdf_path, proposal["questions"], proposal["disclosures"])
    if pdf["pages"] != 1:
        raise ValueError("G34 must fit on exactly one readable PDF page")
    source_md = render_markdown(proposal)
    (dest / "ProjectReady_G34_Round1_OWNER_REVIEW_NOT_SUBMITTED.md").write_text(
        source_md, encoding="utf-8")
    (dest / "ProjectReady_G34_Round1_OWNER_REVIEW_NOT_SUBMITTED.json").write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    report = {
        "status": "G34_OFFLINE_OWNER_REVIEW_PREVIEW_NOT_SUBMITTED",
        "official_checker": "G32_FIRST_PARTY_STATIC_PASS_EXACT_SHA_ONLY",
        "checker_run_id": G33_RUN,
        "checker_exit": 0,
        "checker_errors_warnings_info": [0, 0, 0],
        "candidate_skill_sha256": digest(src),
        "candidate_skill_bytes": len(src),
        "skill_zip_sha256": digest(archive),
        "skill_zip_bytes": len(archive),
        "skill_zip_members": [{"path": "projectready-nas/SKILL.md",
                                "sha256": digest(src), "bytes": len(src)}],
        "pdf": pdf,
        "proposal_answer_words": proposal["substantive_words"],
        "proposal_word_cap": 500,
        "proposal_json_sha256": digest(json.dumps(proposal, indent=2, ensure_ascii=False).encode("utf-8")+b"\n"),
        "proposal_markdown_sha256": digest(source_md.encode("utf-8")),
        "rights_and_license": "PENDING_ENTRANT_REVIEW",
        "official_creator_participant_report": "REPORTED_UNVERIFIED_ON_OWNER_LOCAL_MACHINE",
        "runtime_registered_agents": "NOT_VERIFIED",
        "real_nas": "NOT_RUN",
        "human_entrant_approval": "PENDING",
        "devpost": "NOT_SUBMITTED",
    }
    (dest / "ProjectReady_G34_Manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True, type=Path)
    ns = ap.parse_args()
    try:
        m = build(ns.output_dir)
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, UnicodeError) as exc:
        print("G34 OWNER REVIEW BUILD FAIL:", str(exc)[:800])
        return 1
    print("G34 EXACT G32 STATIC-PASS MATCHING PDF/ZIP BUILT:",
          m["proposal_answer_words"], "words;",
          m["pdf"]["pages"], "page;",
          "NOT SUBMITTED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
