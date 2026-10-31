"""G121 guided expert session: no native Uliya execution or NAS access."""
from __future__ import annotations
import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Callable

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"src"))
from flowpilot.planner import State,draft_plan
from flowpilot_task_compiler import compile_goal
from flowpilot_code_council import run_council
from flowpilot_native_expert_bridge import route_native_review
from flowpilot_uliya_contract_preflight import TrialPreflightRefused
from flowpilot_multi_read_intake import IntakeRefused
from sdk_semantic_index import EXPECTED_SHA256
from inspect_official_sdk import UnsafePackage

SCHEMA="flowpilot-guided-expert-session-v1"
RUNBOOK=(
    "1. Select one read-only goal and exact scoped folder/checklist.",
    "2. Privately review the scope; never expose paths in evidence.",
    "3. Approve read-only metadata and separately acknowledge unknown processing location.",
    "4. Inspect pinned official catalog and separately verify registered Expert signature.",
    "5. Verify effective read-only NAS permissions and actual native result schema.",
    "6. When authorized, collect complete paginated file metadata; never infer missing from partial scans.",
    "7. Reconcile evidence and resolve missing/incomplete/conflicting claims.",
    "8. Obtain independent live readback and new owner approval before any deploy.",
)
class GuidedRefused(ValueError):
    """Sanitized input refusal: no owner path in exception."""

def _base():
    return {"schema":SCHEMA,"release_gate":"HOLD","raw_owner_values_returned":False,
            "owner_folder_accessed":False,"actual_uliya_expert_invoked":False,
            "actual_nas_verified":False,"docker_executed":False,
            "production_applied":False,"devpost_submitted":False}

def _answer(ask:Callable[[str],str],prompt:str,limit:int)->str:
    try:
        data=ask(prompt)
    except (EOFError,KeyboardInterrupt,StopIteration) as exc:
        raise GuidedRefused("Incomplete response") from exc
    if type(data) is not str or not 0<len(data)<=limit or data!=data.strip() or any(ord(c)<32 or ord(c)==127 for c in data):
        raise GuidedRefused("Noncanonical bounded response")
    return data

def _scope(root:str,raw:str)->list[str]:
    if len(raw)>4096:
        raise GuidedRefused("Checklist too long")
    items=[v.strip() for v in raw.split(",")]
    if not 1<=len(items)<=100 or any(not v for v in items):
        raise GuidedRefused("Invalid checklist")
    try:
        plan=draft_plan("check required files",root,items,
                        metadata_approved=False,unknown_processing_accepted=False)
    except (ValueError,TypeError) as exc:
        raise GuidedRefused("Invalid or restricted owner scope") from exc
    if plan.state is not State.WAITING_APPROVAL:
        raise GuidedRefused("Unexpected scoped plan")
    return items

def _load_pinned_kit(path:Path)->bytes:
    """Read a user-selected local official ZIP only after both approvals."""
    if not isinstance(path, Path) or path.is_symlink() or path.parent.is_symlink():
        raise GuidedRefused("Kit path refused")
    try:
        meta=path.stat()
        if not stat.S_ISREG(meta.st_mode) or not 0<meta.st_size<=10*1024*1024:
            raise GuidedRefused("Invalid official kit file")
        data=path.read_bytes()
    except OSError as exc:
        raise GuidedRefused("Kit not accessible") from exc
    if hashlib.sha256(data).hexdigest()!=EXPECTED_SHA256:
        raise GuidedRefused("Official kit SHA mismatch")
    return data

def run_guided_expert(goal:str,*,ask:Callable[[str],str],emit:Callable[[str],None],
                      kit_loader:Callable[[],bytes]|None=None,
                      normalized_receipts:dict|None=None,
                      synthetic_only_test_sha:str|None=None,
                      run_local_fixture:bool=False)->dict:
    """Only one canonical file-check intent. No implicit or bundled approval."""
    base=_base()
    plan=compile_goal(goal)
    if plan["status"]!="READY_FOR_SYNTHETIC_TEST":
        result={**base,"status":"BLOCKED_UNSUPPORTED_GOAL"}
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    if plan["template"]!="required_file_metadata_v1":
        result={**base,"status":"LOCAL_TEMPLATE_ONLY_NATIVE_UNSUPPORTED",
                "template":plan["template"],"fallback":"G114_G119_SYNTHETIC_ONLY"}
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    if type(run_local_fixture) is not bool:
        raise GuidedRefused("Invalid fixture selection")
    root=_answer(ask,"OWNER_AUTHORIZED_NAS_ROOT (no NAS access): ",1024)
    raw=_answer(ask,"REQUIRED_RELATIVE_FILES (comma-separated): ",4096)
    required=_scope(root,raw)
    del raw
    preview={**base,"status":"WAITING_TWO_SEPARATE_APPROVALS",
             "template":plan["template"],"required_item_count":len(required),
             "catalog_action_label":"ug-filesystem find",
             "operator_runbook":RUNBOOK,
             "next_action":"APPROVE_METADATA_THEN_ACK_UNKNOWN_PROCESSING"}
    emit("FLOWPILOT_PREVIEW="+json.dumps(preview,ensure_ascii=True))
    if _answer(ask,"Type APPROVE_METADATA or DECLINE: ",64)!="APPROVE_METADATA":
        result={**base,"status":"DECLINED_NO_ACTION"}
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    if _answer(ask,"Type ACK_UNKNOWN_PROCESSING or DECLINE: ",64)!="ACK_UNKNOWN_PROCESSING":
        result={**base,"status":"DECLINED_NO_ACTION"}
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    result={**base,"status":"AWAITING_PINNED_OFFICIAL_KIT",
            "required_item_count":len(required),"two_owner_consent_claims_collected":True,
            "operator_runbook":RUNBOOK,
            "next_action":"PROVIDE_LOCAL_SHA_PINNED_OFFICIAL_KIT_FILE"}
    if kit_loader is None:
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    try:
        binary=kit_loader()
        if type(binary) is not bytes:
            raise GuidedRefused("Unsupported kit object")
        digest=synthetic_only_test_sha if synthetic_only_test_sha is not None else EXPECTED_SHA256
        if type(digest) is not str or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
            raise GuidedRefused("Invalid archive digest")
        response=route_native_review(
            binary,goal=goal,authorized_root=root,required_paths=required,
            metadata_approved=True,unknown_processing_accepted=True,
            normalized_receipts=normalized_receipts,expected_sha=digest)
    except (GuidedRefused,TrialPreflightRefused,IntakeRefused,UnsafePackage,
            ValueError,TypeError,KeyError,OSError,RecursionError):
        result["status"]="OFFICIAL_CATALOG_OR_RECEIPT_REFUSED"
        result["next_action"]="REVIEW_CATALOG_AND_SCOPE"
        emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
        return result
    if response.get("status")!="AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA":
        result["status"]="OFFICIAL_CATALOG_OR_SCOPE_BLOCKED"
    else:
        result.update({
            "status":"OFFLINE_GUIDED_REVIEW_READY_NOT_NAS",
            "catalog_provenance":response["source"],
            "catalog_action_label":response["chosen_action_label"],
            "parameter_name_count":len(response["declared_parameter_identifiers_only"]),
            "next_action":"VERIFY_LIVE_EXPERT_SIGNATURE_PERMISSIONS_AND_RESULT_SCHEMA",
        })
        if response.get("receipt_status")=="REVIEW_PREPARED_UNVERIFIED":
            result["untrusted_receipts_only"]=True
            result["provisional_consistency"]=response["claimed_consistency"]
            result["provisional_findings"]=response["item_results"]
        if run_local_fixture:
            test=run_council(goal)
            result["local_synthetic_fixture_test"]=(
                "PASS_NOT_NAS" if test.get("status")=="OFFLINE_COUNCIL_REHEARSAL_PASS"
                else "FAIL_RELEASE_HOLD")
    emit("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
    return result

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="G121 guided Expert PLAN, not Uliya execution")
    parser.add_argument("--goal",required=True)
    parser.add_argument("--official-kit-zip",type=Path)
    parser.add_argument("--local-synthetic-test",action="store_true")
    args=parser.parse_args(argv)
    try:
        loader=(lambda:_load_pinned_kit(args.official_kit_zip)) if args.official_kit_zip else None
        result=run_guided_expert(args.goal,ask=input,emit=print,kit_loader=loader,
                                 run_local_fixture=args.local_synthetic_test)
    except GuidedRefused:
        result={**_base(),"status":"GUIDED_SESSION_REFUSED"}
        print("FLOWPILOT_RESULT="+json.dumps(result,ensure_ascii=True))
    return 0 if result["status"] in (
        "OFFLINE_GUIDED_REVIEW_READY_NOT_NAS","AWAITING_PINNED_OFFICIAL_KIT",
        "DECLINED_NO_ACTION","LOCAL_TEMPLATE_ONLY_NATIVE_UNSUPPORTED") else 2

if __name__=="__main__":
    raise SystemExit(main())
