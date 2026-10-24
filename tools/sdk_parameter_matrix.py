"""Bounded first-party ZIP catalog parameter metadata only; never execute SDK."""
import argparse,io,json,re,zipfile
from inspect_official_sdk import download_public_official_zip,inspect_zip_bytes,UnsafePackage
from sdk_semantic_index import EXPECTED_SHA256
from sdk_action_contract_digest import SELECTION,SOURCE

SAFE=re.compile(r"[A-Za-z][A-Za-z0-9_.:/-]{0,63}\Z")
def identifier(value):
    return value if isinstance(value,str) and SAFE.fullmatch(value) else None

def classification(value):
    if isinstance(value,dict):
        return {"kind":"object","keys":[k for k in list(value)[:12] if identifier(k)],
                "knowledge_status":identifier(value.get("knowledgeStatus"))}
    if isinstance(value,list):return {"kind":"array","count":len(value)}
    return {"kind":"scalar","value":identifier(value)}

def matrix(blob,sha=EXPECTED_SHA256):
    if inspect_zip_bytes(blob)["sha256"]!=sha:raise UnsafePackage("SHA pin failure")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        catalog=json.loads(z.read(SOURCE).decode("utf-8"))
    if not isinstance(catalog,dict) or not isinstance(catalog.get("clis"),list):
        raise UnsafePackage("Malformed catalog")
    cli_index={x.get("name"):x for x in catalog["clis"] if isinstance(x,dict)}
    rows=[]
    for cli,wanted in SELECTION.items():
        if cli not in cli_index:raise UnsafePackage("Missing selected CLI group")
        group=cli_index[cli]
        found={x.get("name"):x for x in group.get("actions",[]) if isinstance(x,dict)}
        for action_name in sorted(wanted):
            if action_name not in found:raise UnsafePackage("Missing selected action")
            a=found[action_name]
            params=a.get("parameters")
            if not isinstance(params,list) or len(params)>20:raise UnsafePackage("Unsupported parameters")
            out=[]
            for p in params:
                if not isinstance(p,dict):raise UnsafePackage("Malformed parameter")
                name,typ=identifier(p.get("name")),identifier(p.get("type"))
                req,rep=p.get("required"),p.get("repeatable")
                if not name or not typ or not isinstance(req,bool):raise UnsafePackage("Ambiguous mandatory parameter")
                if rep is not None and not isinstance(rep,bool):raise UnsafePackage("Ambiguous repeatability")
                out.append({"name":name,"type":typ,"required":req,"repeatable":rep})
            rows.append({"cli":cli,"agent_label":identifier(group.get("agent")),"action":action_name,
                         "parameters":out,"effect":classification(a.get("effect")),
                         "approval":classification(a.get("approval")),
                         "permissions":classification(a.get("permissions")),
                         "error_codes":classification(a.get("errorCodes"))})
    if len(rows)!=sum(map(len,SELECTION.values())):raise UnsafePackage("Missing contracted actions")
    return {"evidence":"PINNED_FIRST_PARTY_CATALOG_PARAMETER_IDENTIFIERS_ONLY",
            "sha256":sha,"actions":rows,"action_count":len(rows),
            "live_nas_verified":False,"checker_run":False,"license_verified":False,
            "original_catalog_uploaded":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--official-url",required=True);a=p.parse_args()
    try:
        print(json.dumps(matrix(download_public_official_zip(a.official_url)),indent=2,sort_keys=True))
        return 0
    except Exception as e:
        print(json.dumps({"evidence":"MATRIX_FAILED","error_class":type(e).__name__,
                          "sdk_executed":False,"source_republished":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())
