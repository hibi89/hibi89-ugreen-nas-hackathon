"""Pinned public official catalog contract digest.

Emit only bounded machine-interface identifier metadata, not descriptions,
private SDK source, original JSON contents, examples or credentials.
Never run Uliya binaries/JS, invoke CLI or contact NAS.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import zipfile

from inspect_official_sdk import inspect_zip_bytes, download_public_official_zip, UnsafePackage
from sdk_semantic_index import EXPECTED_SHA256

FILE="uliya-skill-kit/data/capability-catalog.json"
SAFE=re.compile(r"[A-Za-z][A-Za-z0-9_.:/-]{0,79}\Z")
MAX_CLI=30
MAX_ACTIONS=32


def short(value):
    if not isinstance(value,str):
        return None
    value=value.strip()
    return value if SAFE.fullmatch(value) else None


def summarize_fields(value, depth=0):
    if depth>2:
        return type(value).__name__
    if isinstance(value,dict):
        result={}
        for k, v in list(value.items())[:16]:
            if short(k):
                result[k]=summarize_fields(v,depth+1)
        return result
    if isinstance(value,list):
        return {"kind":"array","length":len(value),"first_type":type(value[0]).__name__ if value else "empty"}
    return type(value).__name__


def catalog_digest(binary:bytes,expected=EXPECTED_SHA256):
    meta=inspect_zip_bytes(binary)
    if meta["sha256"]!=expected:
        raise UnsafePackage("Pinned official archive mismatch")
    with zipfile.ZipFile(io.BytesIO(binary)) as archive:
        catalog=json.loads(archive.read(FILE).decode("utf-8"))
    if not isinstance(catalog,dict) or not isinstance(catalog.get("clis"),list):
        raise UnsafePackage("Official catalog shape changed")
    clis=catalog["clis"]
    if len(clis)>MAX_CLI:
        raise UnsafePackage("Unexpected CLI count")
    extracted=[]
    for item in clis:
        if not isinstance(item,dict):
            raise UnsafePackage("CLI item malformed")
        actions=item.get("actions") or []
        if not isinstance(actions,list) or len(actions)>MAX_ACTIONS:
            raise UnsafePackage("Actions malformed/too many")
        a=[]
        for action in actions:
            if isinstance(action,dict):
                a.append({"name":short(action.get("name")),
                          "field_keys":[k for k in list(action)[:15] if short(k)]})
            elif isinstance(action,str):
                a.append({"name":short(action)})
            else:
                a.append({"name":None,"unexpected_shape":type(action).__name__})
        extracted.append({"cli_name":short(item.get("name")),
                          "domain":short(item.get("domain")),
                          "expert_agent_catalog_label":short(item.get("agent")),
                          "action_count":len(a),
                          "actions":a})
    inv=catalog.get("invocation") or {}
    command=inv.get("command") if isinstance(inv,dict) else None
    cmd_prefix=None
    if isinstance(command,str):
        parts=command.strip().split()
        if parts and len(parts)<=3 and all(short(p) for p in parts):
            cmd_prefix=" ".join(parts)
    envelope=inv.get("resultEnvelope") if isinstance(inv,dict) else None
    domains=catalog.get("domains") or []
    safe_domains=[short(d.get("id")) for d in domains if isinstance(d,dict)][:12]
    return {
        "evidence":"FIRST_PARTY_PINNED_CATALOG_STRUCTURED_IDENTIFIERS",
        "archive_sha256":expected,
        "catalog_version_type":type(catalog.get("catalogVersion")).__name__,
        "catalog_entries":len(clis),
        "supported_domain_ids_not_runtime_proof":safe_domains,
        "invocation_command_prefix_as_catalog_text":cmd_prefix,
        "result_envelope_field_shapes":summarize_fields(envelope),
        "cli_catalog_identifiers_not_runtime_verified":extracted,
        "cli_or_agent_registered_on_real_nas":False,
        "official_checker_executed":False,
        "real_nas_access":False,
        "sdk_license_verified":False,
        "original_catalog_republished":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--official-url",required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(catalog_digest(download_public_official_zip(args.official_url)),indent=2,sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"evidence":"CATALOG_DIGEST_FAILED","error_class":type(exc).__name__,
                          "official_checker_executed":False,"archive_saved":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
