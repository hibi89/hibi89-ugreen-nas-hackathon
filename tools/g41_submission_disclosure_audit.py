"""G41 exact-original PDF/Skill submission-disclosure review; no release, no mutation."""
from __future__ import annotations
import argparse,copy,hashlib,io,json,pathlib,sys,zipfile
from check_round1_proposal import errors,render_markdown,word_count
from round1_candidate_bundle import validate_pdf

ROOT=pathlib.Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"docs/submission/evidence/G37_G36_EXACT_ARTIFACT_AUDIT_20261026.json"
G36=ROOT/"docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md"
PDF="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.pdf"
ZIP="ProjectReady_G37_G36_Skill_OWNER_REVIEW_NOT_SUBMITTED.zip"
JSON="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.json"
MD="ProjectReady_G37_Round1_OWNER_REVIEW_NOT_SUBMITTED.md"
SHA_PDF="d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936"
SHA_ZIP="b3efbe261dc0ea35e90c290e362fc0efad70e59315d8cc5f0a009d445ece66d7"
SHA_SOURCE="e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4"
SHA_JSON="6d2fee9cca12bb874e9687e7fb0ad8d96ce211bec730b0ec450fe7cc0199cb69"
SHA_MD="3ef647c1f23292516b4191faa7c4bee7e73069d21cc821018df462f7b7aae752"

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def safe_read(folder:pathlib.Path,name:str,limit:int)->bytes:
    p=folder/name
    if p.is_symlink() or not p.is_file() or p.parent.is_symlink():
        raise ValueError("Unsafe or absent original review member: "+name)
    data=p.read_bytes()
    if not data or len(data)>limit:
        raise ValueError("Invalid original review member size: "+name)
    return data

def declarations(proposal:dict, skill_text:str)->dict:
    d=proposal.get("disclosures",{})
    if not isinstance(d,dict) or any(not isinstance(d.get(k),str) for k in
        ("ai_assistance","platform","other_libraries","data_flow")):
        raise ValueError("Original third-party and AI disclosures missing")
    ai=d["ai_assistance"].lower()
    if not all(term in ai for term in ("chatgpt","codex")):
        raise ValueError("Actual AI development tools not identified in PDF")
    if not all(term in skill_text.lower() for term in ("chatgpt","codex","ugreen","source")):
        raise ValueError("ZIP Markdown missing source/AI provenance section")
    if "local versus cloud" not in d["data_flow"].lower():
        raise ValueError("Unknown data processing location not disclosed")
    vendor_src="https://ai.ugreen.com/pages/hackathon-starter-kit"
    if vendor_src not in skill_text:
        raise ValueError("UGREEN official required tool source URL not disclosed")
    if not all(term in d["other_libraries"].lower() for term in
        ("python","reportlab","pypdf")):
        raise ValueError("Offline generation dependency inventory regressed")
    # A truthful 'not cleared' sentence is NOT an actual license grant.
    license_open=any(s in d["platform"].lower() for s in ("not cleared","not verified")) or any(
        s in skill_text.lower() for s in ("license rights are still pending","pending entrant verification"))
    if not license_open:
        raise ValueError("License uncertainty disappeared without independently supplied proof")
    # G37 QA's GitHub workflow installs and executes PyMuPDF, but the PDF names
    # only Python, ReportLab and pypdf in its development-tool list.
    pymupdf_named="pymupdf" in d["other_libraries"].lower()
    return {
        "ai_tools_in_pdf":["OpenAI ChatGPT","OpenAI Codex"],
        "official_tool_source_in_skill":vendor_src,
        "official_kit_applicable_license":"NOT_IDENTIFIED_OR_CLEARED",
        "applicable_license_disclosure_complete":False,
        "platform_dataflow":"LOCAL_CLOUD_UNKNOWN_AND_DISCLOSED",
        "qa_only_pymupdf_used_by_g37_workflow":True,
        "qa_only_pymupdf_named_in_pdf":pymupdf_named,
        "qa_only_pymupdf_disclosure_review":(
            "COMPLETE" if pymupdf_named else "OPEN_QA_DEPENDENCY_INVENTORY"),
        "ai_claims_human_editorially_approved":False,
    }

def assess(folder:pathlib.Path)->dict:
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Missing/symlinked artifact directory")
    evidence=json.loads(ORIGINAL.read_text(encoding="utf-8"))
    if (evidence.get("pdf",{}).get("sha256")!=SHA_PDF or
        evidence.get("zip",{}).get("sha256")!=SHA_ZIP or
        evidence.get("workflow",{}).get("artifact_id")!=12644844524):
        raise ValueError("G37 immutable source evidence mismatch")
    pdf=safe_read(folder,PDF,1_000_000)
    zipfile_bytes=safe_read(folder,ZIP,10_000_000)
    jbytes=safe_read(folder,JSON,100_000)
    mbytes=safe_read(folder,MD,100_000)
    if {sha(pdf),sha(zipfile_bytes),sha(jbytes),sha(mbytes)}!={
       SHA_PDF,SHA_ZIP,SHA_JSON,SHA_MD}:
        raise ValueError("Original G37 PDF/ZIP/JSON/MD SHA mismatch; do not audit regenerated output")
    source=G36.read_bytes()
    if G36.is_symlink() or sha(source)!=SHA_SOURCE or len(source)!=14522:
        raise ValueError("G36 exact first-party checked source drift")
    with zipfile.ZipFile(io.BytesIO(zipfile_bytes)) as z:
        if z.namelist()!=["projectready-nas/SKILL.md"]:
            raise ValueError("Unexpected ZIP members, executable or extra assets")
        zip_skill=z.read("projectready-nas/SKILL.md")
        if zip_skill!=source:
            raise ValueError("Archived Skill differs from G36 exact SHA")
    proposal=json.loads(jbytes)
    if (proposal.get("status")!="DRAFT_NOT_SUBMITTED" or
        proposal.get("proof_status",{}).get("official_validator")!="G36_EXACT_SHA_FIRST_PARTY_STATIC_PASS" or
        proposal.get("proof_status",{}).get("devpost")!="NOT_SUBMITTED" or
        len(proposal.get("questions",[]))!=10 or
        sum(word_count(x["answer"]) for x in proposal["questions"])!=378 or
        proposal.get("substantive_words")!=378):
        raise ValueError("Claim or word-count drift")
    check=copy.deepcopy(proposal)
    check["proof_status"]["official_validator"]="NOT_RUN"
    if errors(check,render_markdown(check)):
        raise ValueError("Official ten-prompt proposal structure rejected")
    if mbytes.decode("utf-8")!=render_markdown(proposal):
        raise ValueError("Markdown != JSON derived official answers")
    pdfinfo=validate_pdf(folder/PDF,proposal["questions"],proposal["disclosures"])
    if pdfinfo["pages"]!=1 or pdfinfo["sha256"]!=SHA_PDF:
        raise ValueError("Original PDF text parity failed")
    note=declarations(proposal,source.decode("utf-8"))
    return {
        "technical_status":"PASS_ACTUAL_IMMUTABLE_G37_PDF_ZIP_JSON_MD_AND_G36_SOURCE",
        "pdf_sha256":SHA_PDF,"zip_sha256":SHA_ZIP,"skill_sha256":SHA_SOURCE,
        "official_questions":10,"english_answer_words":378,"word_cap":500,
        "disclosures":{"count":4,**note},
        "human_entrant_originality_and_voice":"PENDING",
        "official_Codex_Creator_invocation":"PARTICIPANT_REPORTED_NOT_INDEPENDENTLY_REPLAYED",
        "official_Uliya_static_checker":"G36_EXACT_SHA_PASS_NOT_RUNTIME",
        "applicable_license":"UNRESOLVED",
        "rights_clearance":"NOT_CLEARED",
        "owner_submission_consent":"NOT_GIVEN",
        "nas_runtime":"NOT_RUN",
        "devpost":"NOT_SUBMITTED",
        "decision":"HOLD_EXTERNAL_LICENSE_ORIGINALITY_AND_OWNER_SIGNOFF"
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-dir",required=True,type=pathlib.Path)
    p.add_argument("--output",required=True,type=pathlib.Path)
    a=p.parse_args()
    try:
        result=assess(a.artifact_dir)
        o=a.output.resolve()
        if o==ROOT or ROOT in o.parents:
            raise ValueError("Write only to isolated output, not source repo")
        o.parent.mkdir(parents=True,exist_ok=True)
        o.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False))
        print("G41 ORIGINAL PDF/SKILL DISCLOSURE REVIEW TECH PASS; OWNER LICENSE HOLD")
        return 0
    except (OSError,ValueError,KeyError,RuntimeError,TypeError,zipfile.BadZipFile) as e:
        print("G41_DISCLOSURE_AUDIT_FAIL:",str(e)[:300])
        return 1
if __name__=="__main__":sys.exit(main())
