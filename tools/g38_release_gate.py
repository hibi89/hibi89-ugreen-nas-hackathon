"""G38: independent Round1 exact-original artifact review; never approve or submit.

Use a real GitHub Actions artifact extracted to an OUTSIDE-REPO folder, not a
re-rendered / rewritten PDF. Technical checks cannot substitute for entrant
ownership, official kit terms, or submission authorization.
"""
from __future__ import annotations
import argparse, hashlib, io, json, pathlib, re, sys, zipfile
from check_round1_proposal import errors, render_markdown, word_count
from round1_candidate_bundle import validate_pdf
ROOT=pathlib.Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs/submission/evidence/G37_G36_EXACT_ARTIFACT_AUDIT_20261026.json"
G36_SKILL=ROOT/"docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md"
PDF_NAME="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.pdf"
ZIP_NAME="ProjectReady_G37_G36_Skill_OWNER_REVIEW_NOT_SUBMITTED.zip"
PROPOSAL_NAME="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.json"
MARKDOWN_NAME="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.md"
MANIFEST_NAME="ProjectReady_G37_Manifest.json"
G36_SHA="e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4"
SHA_PDF="d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936"
SHA_ZIP="b3efbe261dc0ea35e90c290e362fc0efad70e59315d8cc5f0a009d445ece66d7"
SHA_JSON="6d2fee9cca12bb874e9687e7fb0ad8d96ce211bec730b0ec450fe7cc0199cb69"
SHA_MD="3ef647c1f23292516b4191faa7c4bee7e73069d21cc821018df462f7b7aae752"

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def immutable_blockers()->dict:
    """Read-only release matrix; never infer/auto-generate legal attestation."""
    return {
      "entrant_copyright_originality_new_core_work":"PENDING_ENTRANT_ASSERTION",
      "authorized_entrant_eligible_one_project":"PENDING_ENTRANT_ASSERTION",
      "official_creator_codex_provenance":"PARTICIPANT_REPORTED_NOT_INDEPENDENTLY_REPLAYED",
      "UGREEN_kit_platform_license_and_applicable_terms":"NOT_CLEARED",
      "third_party_component_source_license_disclosures":"REVIEW_REQUIRED",
      "human_editorial_pdf_zip_exact_files":"PENDING",
      "AI_assistance_and_local_cloud_dataflow_acceptance":"PENDING",
      "explicit_Devpost_submission_permission":"NOT_GIVEN",
      "Devpost_submission_receipt":"NOT_SUBMITTED"
    }

def status_for(blockers:dict)->str:
    if all(v in ("ACCEPTED", "CLEARED", "SUBMITTED") for v in blockers.values()):
        # Even if a future tool/user mistakenly marks everything approved, this
        # script never grants host submission authority or emits READY_TO_SUBMIT.
        return "HOLD_FOR_SEPARATE_OWNER_ACTION_NOT_SUBMITTED"
    return "HOLD_EXTERNAL_REVIEW_REQUIRED_NOT_SUBMITTED"

def safe_member(dir:pathlib.Path,name:str,limit:int)->bytes:
    p=dir/name
    if p.is_symlink() or not p.is_file() or p.parent.is_symlink():
        raise ValueError("Missing/unsafe artifact member: "+name)
    data=p.read_bytes()
    if not data or len(data)>limit:
        raise ValueError("Unexpected artifact size: "+name)
    return data

def audit(folder:pathlib.Path)->dict:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Artifact dir missing or symlink")
    evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (evidence.get("source_sha256")!=G36_SHA or
        evidence.get("pdf",{}).get("sha256")!=SHA_PDF or
        evidence.get("zip",{}).get("sha256")!=SHA_ZIP or
        evidence.get("workflow",{}).get("artifact_id")!=12644844524 or
        evidence.get("first_party_checker",{}).get("verdict")!="static-pass"):
        raise ValueError("Tampered independent G37 evidence")
    pdf=safe_member(folder,PDF_NAME,1_000_000)
    rawzip=safe_member(folder,ZIP_NAME,10_000_000)
    proposal_raw=safe_member(folder,PROPOSAL_NAME,100_000)
    markdown_raw=safe_member(folder,MARKDOWN_NAME,100_000)
    manifest_raw=safe_member(folder,MANIFEST_NAME,100_000)
    found={"PDF":digest(pdf),"ZIP":digest(rawzip),
           "proposal_JSON":digest(proposal_raw),"proposal_Markdown":digest(markdown_raw)}
    want={"PDF":SHA_PDF,"ZIP":SHA_ZIP,"proposal_JSON":SHA_JSON,"proposal_Markdown":SHA_MD}
    if found!=want:
        raise ValueError("Exact original bytes mismatch; re-rendered PDF is NOT validated")
    m=json.loads(manifest_raw.decode("utf-8"))
    proposal=json.loads(proposal_raw.decode("utf-8"))
    if (m.get("status")!="G37_OFFLINE_OWNER_REVIEW_PREVIEW_NOT_SUBMITTED"
        or m.get("pdf",{}).get("sha256")!=SHA_PDF
        or m.get("pdf",{}).get("bytes")!=len(pdf)
        or m.get("skill_zip_sha256")!=SHA_ZIP
        or m.get("skill_zip_bytes")!=len(rawzip)
        or m.get("candidate_skill_sha256")!=G36_SHA
        or m.get("proposal_answer_words")!=378
        or m.get("devpost")!="NOT_SUBMITTED"
        or m.get("human_entrant_approval")!="PENDING"):
        raise ValueError("Manifest not exact unapproved original")
    if G36_SKILL.is_symlink() or digest(G36_SKILL.read_bytes())!=G36_SHA:
        raise ValueError("Official checker G36 source changed")
    with zipfile.ZipFile(io.BytesIO(rawzip)) as z:
        if z.namelist()!=["projectready-nas/SKILL.md"]:
            raise ValueError("Skill ZIP is not single Markdown entry")
        x=z.getinfo("projectready-nas/SKILL.md")
        if x.flag_bits & 1 or x.is_dir() or x.file_size!=14522:
            raise ValueError("Unsafe Skill ZIP entry")
        if z.read(x)!=G36_SKILL.read_bytes():
            raise ValueError("ZIP Skill not byte-identical to approved-source G36")
    if (len(proposal.get("questions",[]))!=10
        or sum(word_count(q["answer"]) for q in proposal["questions"])!=378
        or proposal["proof_status"]["official_validator"]!="G36_EXACT_SHA_FIRST_PARTY_STATIC_PASS"
        or proposal["proof_status"]["devpost"]!="NOT_SUBMITTED"):
        raise ValueError("Proposal claims/length inconsistent")
    # Canonical checker refuses every non-NOT_RUN proof status; only mask it in
    # an in-memory validation copy, never in the PDF, JSON, or approval ledger.
    import copy
    validation=copy.deepcopy(proposal)
    validation["proof_status"]["official_validator"]="NOT_RUN"
    if errors(validation,render_markdown(validation)):
        raise ValueError("Official ten-question text validation rejected proposal")
    if markdown_raw.decode("utf-8")!=render_markdown(proposal):
        raise ValueError("Markdown source differs from exact PDF candidate")
    pdfinfo=validate_pdf(folder/PDF_NAME,proposal["questions"],proposal["disclosures"])
    if pdfinfo["pages"]!=1 or pdfinfo["sha256"]!=SHA_PDF:
        raise ValueError("PDF readability or full Q/A text mismatch")
    blockers=immutable_blockers()
    return {
      "status":"TECHNICAL_ORIGINAL_BYTES_MATCHED_BUT_NOT_RELEASED",
      "release_decision":status_for(blockers),
      "source_sha256":G36_SHA, "pdf_sha256":SHA_PDF,"zip_sha256":SHA_ZIP,
      "pdf_bytes":len(pdf),"zip_bytes":len(rawzip),
      "pdf_pages":1, "official_questions":10,
      "english_answer_words":378, "disclosures_in_pdf":4,
      "first_party_static_checker":"G36_EXACT_STATIC_PASS_NOT_RUNTIME",
      "re_download_original_required_if_modified":True,
      "rights_and_entrant_approval_gates":blockers,
      "live_nas":"NOT_RUN","skillhub":"NOT_PUBLISHED","devpost":"NOT_SUBMITTED"
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",type=pathlib.Path,required=True)
    ap.add_argument("--output",type=pathlib.Path,required=True)
    args=ap.parse_args()
    try:
        report=audit(args.artifact_dir)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(report,ensure_ascii=False))
        print("G38 ORIGINAL BYTE CHECK PASS; EXTERNAL RIGHTS AND SUBMISSION GATE HOLD")
        return 0
    except (ValueError,KeyError,TypeError,RuntimeError,IOError,zipfile.BadZipFile) as exc:
        print("G38 EXACT RELEASE GATE ERROR:",str(exc))
        return 1
if __name__=="__main__":
    sys.exit(main())
