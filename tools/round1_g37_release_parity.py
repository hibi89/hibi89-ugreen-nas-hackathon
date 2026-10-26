"""G37: build exact G36 / G36-checker-proven Round 1 owner REVIEW package, never submit.

The original Round 1 proposal, G29 PDF/ZIP and all prior Skill candidates
remain immutable. The official Uliya checker static-pass applies ONLY to
the exact G36 sha256 recorded in an independently-run G36 action.
"""
from __future__ import annotations
import argparse, copy, hashlib, io, json, zipfile
from pathlib import Path

from check_round1_proposal import JSON_PATH, errors, render_markdown, word_count
from render_round1_proposal_pdf import render
from round1_candidate_bundle import validate_pdf
from round1_official_creator_preview import zip_only_skill

ROOT = Path(__file__).resolve().parents[1]
G36 = ROOT / "docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md"
G36_EVIDENCE = ROOT / "docs/submission/evidence/G36_FIRST_PARTY_STATIC_PASS_20261026.json"
G36_SHA = "e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4"
G36_RUN = 40311253113
G36_VENDOR_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"

Q8 = (
    "The initial Skill was generated using UGREEN's official Creation Tool in "
    "Codex, as reported by the entrant. The revised G36 Skill passed the actual "
    "first-party Uliya static checker on its exact SHA-256 (zero findings) in "
    "isolated CI. Read-only delegated file/document workflows and offline tests "
    "are drafted. Live NAS access, registered Agent permissions and data flow "
    "are unverified; rights and submission remain subject to entrant approval."
)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def pinned_source() -> bytes:
    """Fail closed on source bytes or real new-SHA vendor evidence drift."""
    if G36.is_symlink() or not G36.is_file() or G36.parent.is_symlink():
        raise ValueError("Expected original G36 regular file missing or symlinked")
    if G36_SHA != digest(G36.read_bytes()) or G36.stat().st_size != 14522:
        raise ValueError("G36 exact checked SHA/size changed; cannot inherit static pass")
    if G36_EVIDENCE.is_symlink() or not G36_EVIDENCE.is_file():
        raise ValueError("Official G36 checker evidence missing or symlink")
    source = G36.read_bytes()
    j = json.loads(G36_EVIDENCE.read_text(encoding="utf-8"))
    if (j.get("evidence_type") != "G36_INDEPENDENTLY_EXECUTED_FIRST_PARTY_ULIYA_STATIC_CHECK"
        or j.get("source_path") != "docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md"
        or j.get("source_sha256") != G36_SHA or j.get("source_bytes") != len(source)
        or j.get("official_vendor_zip_sha256") != G36_VENDOR_SHA
        or j.get("checker_run_id") != G36_RUN
        or j.get("checker_exit") != 0
        or j.get("checker_status") != "static-pass"
        or j.get("summary") != {"errors": 0, "warnings": 0, "info": 0}
        or j.get("diagnostics") != []
        or j.get("stderr_present") is not False
        or j.get("source_sha_before_after_equal") is not True
        or j.get("network_blocked_during_checker") is not True
        or j.get("candidate_mounted_read_only") is not True
        or j.get("nas_runtime") != "NOT_RUN"
        or j.get("devpost") != "NOT_SUBMITTED"
        or not isinstance(j.get("checker_json_sha256"), str)
        or len(j["checker_json_sha256"]) != 64):
        raise ValueError("G36 first-party receipt does not support pinned Skill exact SHA")
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
        "G36. Platform license, service terms, live Agent availability and data "
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
    p["proof_status"]["official_validator"] = "G36_EXACT_SHA_FIRST_PARTY_STATIC_PASS"
    p["proof_status"]["g37_release_status"] = "OWNER_REVIEW_PENDING_NOT_SUBMITTED"
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
        raise ValueError("G37 only writes outside repository")
    dest.mkdir(parents=True, exist_ok=True)
    pdf_path = dest / "ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.pdf"
    zip_path = dest / "ProjectReady_G37_G36_Skill_OWNER_REVIEW_NOT_SUBMITTED.zip"
    archive = zip_only_skill(src)
    zip_path.write_bytes(archive)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.namelist() != ["projectready-nas/SKILL.md"]:
            raise ValueError("Unexpected ZIP member")
        if z.read("projectready-nas/SKILL.md") != src:
            raise ValueError("ZIP content is not first-party checked G36")
    # Shared renderer guards the original unverified canonical proposal status.
    # The staged JSON and manifest retain the real G36 pass; this local copy
    # adapts only that legacy guard (not the rendered answers/disclosures).
    render_view = copy.deepcopy(proposal)
    render_view["proof_status"]["official_validator"] = "NOT_RUN"
    render(pdf_path, proposal=render_view)
    pdf = validate_pdf(pdf_path, proposal["questions"], proposal["disclosures"])
    if pdf["pages"] != 1:
        raise ValueError("G37 must fit on exactly one readable PDF page")
    source_md = render_markdown(proposal)
    (dest / "ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.md").write_text(
        source_md, encoding="utf-8")
    (dest / "ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.json").write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    report = {
        "status": "G37_OFFLINE_OWNER_REVIEW_PREVIEW_NOT_SUBMITTED",
        "official_checker": "G36_FIRST_PARTY_STATIC_PASS_EXACT_SHA_ONLY",
        "checker_run_id": G36_RUN,
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
    (dest / "ProjectReady_G37_Manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True, type=Path)
    ns = ap.parse_args()
    try:
        m = build(ns.output_dir)
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, UnicodeError) as exc:
        print("G37 OWNER REVIEW BUILD FAIL:", str(exc)[:800])
        return 1
    print("G37 EXACT G36 STATIC-PASS MATCHING PDF/ZIP BUILT:",
          m["proposal_answer_words"], "words;",
          m["pdf"]["pages"], "page;",
          "NOT SUBMITTED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
