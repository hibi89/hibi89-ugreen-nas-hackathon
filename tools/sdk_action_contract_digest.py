"""Extract only bounded interface metadata for pinned first-party Uliya actions.

Never execute official SDK; no raw docs, examples, source ZIP or user data emitted.
Names are documented catalog claims, not evidence of real NAS runtime registration.
"""
import argparse
import io
import json
import re
import zipfile
from inspect_official_sdk import download_public_official_zip, inspect_zip_bytes, UnsafePackage
from sdk_semantic_index import EXPECTED_SHA256

SOURCE="uliya-skill-kit/data/capability-catalog.json"
SELECTION={"ug-filesystem":{"ls","find","stat","sha256sum","cat"},
           "ug-document":{"metadata","qa","extract","reconcile"}}
SAFE=re.compile(r"[A-Za-z][A-Za-z0-9_.:/-]{0,72}\Z")


def sanitized(value):
    return value if isinstance(value,str) and SAFE.fullmatch(value) else None


def shape_fields(value, depth=0):
    if depth>=2: return type(value).__name__
    if isinstance(value,dict):
        return {key:shape_fields(v,depth+1) for key,v in list(value.items())[:25] if sanitized(key)}
    if isinstance(value,list):
        if not value:return {"kind":"array","length":0}
        return {"kind":"array","length":len(value),"item_keys":list(value[0])[:20] if isinstance(value[0],dict) else type(value[0]).__name__}
    if isinstance(value,bool):return value
    return type(value).__name__


def action_contracts(binary, expected_sha=EXPECTED_SHA256):
    if inspect_zip_bytes(binary)["sha256"]!=expected_sha:
        raise UnsafePackage("Pinned ZIP differs")
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        catalog=json.loads(z.read(SOURCE).decode("utf-8"))
    groups={c.get("name"):c for c in catalog["clis"] if isinstance(c,dict)}
    rows=[]
    for group,names in SELECTION.items():
        if group not in groups:raise UnsafePackage("Expected official group missing")
        cli=groups[group]
        by_name={a.get("name"):a for a in cli.get("actions",[]) if isinstance(a,dict)}
        for name in sorted(names):
            if name not in by_name:raise UnsafePackage(f"Selected official action missing: {name}")
            act=by_name[name]
            rows.append({
                "cli":sanitized(group),
                "agent_catalog_label_not_runtime_proof":sanitized(cli.get("agent")),
                "action":sanitized(name),
                "parameters_structure_only":shape_fields(act.get("parameters")),
                "effect_structure_only":shape_fields(act.get("effect")),
                "approval_structure_only":shape_fields(act.get("approval")),
                "permissions_structure_only":shape_fields(act.get("permissions")),
                "error_code_identifiers_only": [sanitized(x) for x in act.get("errorCodes",[])[:12] if isinstance(x,str)] if isinstance(act.get("errorCodes"),list) else shape_fields(act.get("errorCodes")),
                "stability_structure_only":shape_fields(act.get("stability")),
            })
    return {"evidence":"FIRST_PARTY_PINNED_SELECTED_ACTION_STRUCTURE",
            "sha256":expected_sha,
            "selected_action_count":len(rows),
            "selected_contracts":rows,
            "registered_on_live_nas":False,
            "official_checker_executed":False,
            "nas_test_executed":False,
            "license_scope_verified":False,
            "original_catalog_republished":False}


def main():
    p=argparse.ArgumentParser();p.add_argument("--official-url",required=True);args=p.parse_args()
    try:
        print(json.dumps(action_contracts(download_public_official_zip(args.official_url)),sort_keys=True,indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"evidence":"ACTION_CONTRACT_SCAN_FAILED","exception_class":type(e).__name__,"sdk_executed":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
