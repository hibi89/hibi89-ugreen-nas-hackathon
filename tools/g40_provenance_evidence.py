"""G40: independently cross-check old Creator-review source and current G36 proof.

Historical reviewer source in GitHub is real but cannot prove Codex Creator was
run locally. A successful official static checker is a separate claim. This
script makes no external requests and never approves/releases an entry.
"""
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
PINNED_COMMIT="7af2cb750b37826fb02a00e2d45cb73f3a85c239"
REVIEW_FILE="skill/projectready-nas/SKILL.md"
REVIEW_SHA="164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead"
G36_FILE="docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md"
G36_SHA="e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4"
G20_CHECK="docs/submission/G20_P1_OFFICIAL_CHECK_RESULT.json"
G36_RECEIPT="docs/submission/evidence/G36_FIRST_PARTY_STATIC_PASS_20261026.json"
G37_AUDIT="docs/submission/evidence/G37_G36_EXACT_ARTIFACT_AUDIT_20261026.json"
G39_AUDIT="docs/submission/evidence/G39_OFFICIAL_LICENSE_AND_CREATOR_PROVENANCE_20261026.json"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def git_source_at(commit:str,path:str)->bytes:
    """Only fixed repo object; no shell expansion, remote fetch or NAS access."""
    obj=f"{commit}:{path}"
    p=subprocess.run(["git","show",obj],cwd=ROOT,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,check=False)
    if p.returncode!=0:raise ValueError("Pinned git source unavailable")
    return p.stdout

def read_j(path:str)->dict:
    p=ROOT/path
    if p.is_symlink() or not p.is_file():raise ValueError("Unsafe/missing evidence "+path)
    return json.loads(p.read_text(encoding="utf-8"))

def assess(review_bytes:bytes,current_bytes:bytes,g20:dict,g36:dict,g37:dict,g39:dict)->dict:
    if sha(review_bytes)!=REVIEW_SHA:raise ValueError("G20 review source drift")
    if sha(current_bytes)!=G36_SHA or len(current_bytes)!=14522:
        raise ValueError("G36 exact first-party checker source drift")
    if (g20.get("status")!="static-pass" or
        g20.get("summary")!={"errors":0,"warnings":0,"info":0} or
        len(g20.get("files",[]))!=1 or
        g20["files"][0].get("sha256")!=REVIEW_SHA or
        g20["files"][0].get("path")!="SKILL.md"):
        raise ValueError("Review commit checker JSON not bound to review source")
    if (g36.get("checker_status")!="static-pass" or
        g36.get("checker_exit")!=0 or g36.get("source_sha256")!=G36_SHA or
        g36.get("source_bytes")!=len(current_bytes) or
        g36.get("summary")!={"errors":0,"warnings":0,"info":0} or
        g36.get("checker_run_id")!=40311253113 or
        g36.get("nas_runtime")!="NOT_RUN"):
        raise ValueError("G36 independently executed checker evidence not bound")
    if (g37.get("source_sha256")!=G36_SHA or
        g37.get("zip",{}).get("contained_skill_sha256")!=G36_SHA or
        g37.get("pdf",{}).get("sha256")!="d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936" or
        g37.get("workflow",{}).get("artifact_id")!=12644844524 or
        g37.get("limitations",{}).get("devpost")!="NOT_SUBMITTED"):
        raise ValueError("G37 artifact lineage unverified")
    kit=g39.get("official_pinned_archive",{})
    if (kit.get("sha256")!="cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
        or kit.get("checked_file_count")!=26 or
        kit.get("license_candidate_file_count")!=0 or
        g39.get("actual_vendor_kit_license")!="NOT_IDENTIFIED_FROM_PINNED_ARCHIVE_OR_LINKED_PUBLIC_TERMS"):
        raise ValueError("G39 pinned kit license inventory drift")
    return {
      "status":"PROVENANCE_ARTIFACT_CHAIN_TECHNICALLY_VERIFIED_RELEASE_HOLD",
      "pinned_review_commit":PINNED_COMMIT,
      "pinned_review_source_path":REVIEW_FILE,
      "pinned_review_source_sha256":REVIEW_SHA,
      "pinned_review_source_bytes":len(review_bytes),
      "pinned_review_checker":"IN_REPO_JSON_STATIC_PASS_BOUND_TO_PINNED_SOURCE",
      "source_git_bytes_verified":True,
      "current_g36_sha256":G36_SHA,
      "current_g36_bytes":len(current_bytes),
      "current_g36_first_party_checker":"INDEPENDENT_CI_STATIC_PASS_RUN_40311253113",
      "g37_pdf_zip_exact_to_g36":True,
      "g39_vendor_archive_license_filename_hits":0,
      "g39_license_grant_established":False,
      "creator_run_locally_replayed":False,
      "creator_original_generation_claim":"PARTICIPANT_REPORTED",
      "originality_and_third_party_license_cleared":False,
      "user_signed_submission":False,
      "devpost_submitted":False,
      "nas_tested":False,
      "release_decision":"HOLD_LICENSE_CREATOR_PROVENANCE_AND_ENTRANT_SIGNOFF"
    }

def audit()->dict:
    old=git_source_at(PINNED_COMMIT,REVIEW_FILE)
    current=(ROOT/G36_FILE)
    if current.is_symlink() or not current.is_file():raise ValueError("Invalid G36 source path")
    return assess(old,current.read_bytes(),json.loads(git_source_at(PINNED_COMMIT,G20_CHECK).decode("utf-8")),
      read_j(G36_RECEIPT),read_j(G37_AUDIT),read_j(G39_AUDIT))

def main()->int:
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True,type=pathlib.Path)
    args=ap.parse_args()
    try:
        record=audit()
        if args.output.resolve()==ROOT or ROOT in args.output.resolve().parents:
            raise ValueError("Do not write provenance proof into tracked workspace")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(record,ensure_ascii=False))
        return 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError) as exc:
        print("G40_PROVENANCE_AUDIT_FAIL:",str(exc)[:250])
        return 1
if __name__=="__main__":sys.exit(main())
