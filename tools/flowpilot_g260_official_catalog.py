"""G260: exact original official Uliya Kit 0.7.3 catalog reader.

Executable owner-local pre-NAS route; reads bounded authenticated ZIP bytes and
the original public capability catalog, never invokes any Uliya tool/Checker,
opens owner files, downloads anything, grants permissions or starts NAS trial.
Unlike prior G257 private rehearsal, no synthetic SDK parser shim is needed.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import zipfile

EXPECTED_SHA256 = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
CATALOG = "uliya-skill-kit/data/capability-catalog.json"
SELECTED = {
    "ug-filesystem": ("file-agent", ("ls", "find", "stat", "sha256sum", "cat")),
    "ug-document": ("document-agent", ("metadata", "qa", "extract", "reconcile")),
}
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.:/-]{0,63}\Z")


class OfficialCatalogRefused(ValueError):
    """Refusal code carries no owner path or sensitive source data."""


def _unique(pairs):
    if len(pairs) != len({k for k, _ in pairs}):
        raise OfficialCatalogRefused("DUPLICATE_OFFICIAL_CATALOG_JSON_KEY")
    return dict(pairs)


def _id(value):
    return value if type(value) is str and IDENTIFIER.fullmatch(value) else None


def _shape(value):
    if type(value) is dict:
        return {
            "kind": "object",
            "keys": [key for key in list(value)[:12] if _id(key)],
            "knowledge_status": _id(value.get("knowledgeStatus")),
        }
    if type(value) is list:
        return {"kind": "array", "count": len(value)}
    return {"kind": "scalar", "value": _id(value)}


def matrix(binary: bytes, expected_sha: str = EXPECTED_SHA256, *,
           synthetic_only: bool = False) -> dict:
    """Mirror the existing selected-action metadata shape on real first-party ZIP.

    A test fixture SHA override is NEVER a production provenance override.
    Returned values are identifier/shape metadata only; no example text or
    runnable CLI parameters, live Expert or NAS claims.
    """
    if (type(binary) is not bytes or not 0 < len(binary) <= 500_000 or
            type(expected_sha) is not str or
            not re.fullmatch("[0-9a-f]{64}", expected_sha)):
        raise OfficialCatalogRefused("OFFICIAL_KIT_INPUT_BOUNDS_REFUSED")
    if not synthetic_only and expected_sha != EXPECTED_SHA256:
        raise OfficialCatalogRefused("OFFICIAL_KIT_SHA_OVERRIDE_REFUSED")
    if hashlib.sha256(binary).hexdigest() != expected_sha:
        raise OfficialCatalogRefused("OFFICIAL_KIT_SHA_MISMATCH")
    try:
        with zipfile.ZipFile(io.BytesIO(binary)) as z:
            members = z.infolist()
            if (not 1 <= len(members) <= 50 or
                    len(set(m.filename for m in members)) != len(members) or
                    sum(m.file_size for m in members) > 2_000_000 or
                    any(m.file_size > 500_000 or
                        stat.S_ISLNK(m.external_attr >> 16) or
                        m.filename.startswith("/") or ".." in m.filename.split("/")
                        for m in members) or
                    z.testzip() is not None or
                    CATALOG not in {m.filename for m in members}):
                raise OfficialCatalogRefused("OFFICIAL_KIT_ZIP_NOT_SAFE")
            member = z.getinfo(CATALOG)
            if not 0 < member.file_size <= 200_000:
                raise OfficialCatalogRefused("CATALOG_TOO_LARGE")
            raw = z.read(member)
    except (zipfile.BadZipFile, OSError, RuntimeError, KeyError) as ex:
        raise OfficialCatalogRefused("OFFICIAL_KIT_CATALOG_UNREADABLE") from ex
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (ValueError, UnicodeError) as ex:
        raise OfficialCatalogRefused("OFFICIAL_KIT_CATALOG_JSON_INVALID") from ex
    if (type(doc) is not dict or type(doc.get("clis")) is not list or
            len(doc["clis"]) > 100):
        raise OfficialCatalogRefused("OFFICIAL_CATALOG_SHAPE_INVALID")
    groups = {}
    for group in doc["clis"]:
        if type(group) is not dict:
            raise OfficialCatalogRefused("INVALID_CATALOG_GROUP")
        name = _id(group.get("name"))
        if not name or name in groups:
            raise OfficialCatalogRefused("DUPLICATE_OR_INVALID_CLI")
        groups[name] = group
    rows = []
    for cli, (agent, wanted) in SELECTED.items():
        group = groups.get(cli)
        if not group or (group.get("agent") !=
                         ("fake-agent" if synthetic_only else agent)):
            raise OfficialCatalogRefused("REGISTERED_AGENT_LABEL_UNKNOWN")
        actions = group.get("actions")
        if type(actions) is not list or len(actions) > 50:
            raise OfficialCatalogRefused("INVALID_CATALOG_ACTION_LIST")
        index = {}
        for action in actions:
            if type(action) is not dict:
                raise OfficialCatalogRefused("MALFORMED_CATALOG_ACTION")
            name = _id(action.get("name"))
            if not name or name in index:
                raise OfficialCatalogRefused("DUPLICATE_OR_UNKNOWN_ACTION")
            index[name] = action
        for action_name in sorted(wanted):
            action = index.get(action_name)
            if action is None:
                raise OfficialCatalogRefused("READ_ONLY_ACTION_NOT_LISTED")
            params = action.get("parameters")
            if type(params) is not list or len(params) > 20:
                raise OfficialCatalogRefused("CATALOG_PARAMETERS_INVALID")
            processed = []
            seen = set()
            for p in params:
                if type(p) is not dict:
                    raise OfficialCatalogRefused("MALFORMED_CATALOG_PARAMETER")
                name, kind = _id(p.get("name")), _id(p.get("type"))
                required, repeat = p.get("required"), p.get("repeatable")
                if (not name or not kind or name in seen or
                        type(required) is not bool or
                        (repeat is not None and type(repeat) is not bool)):
                    raise OfficialCatalogRefused("CATALOG_PARAMETER_UNSAFE")
                seen.add(name)
                processed.append({"name": name, "type": kind,
                                  "required": required, "repeatable": repeat})
            row = {
                "cli": cli, "agent_label": group.get("agent"),
                "action": action_name, "parameters": processed,
                "effect": _shape(action.get("effect")),
                "approval": _shape(action.get("approval")),
                "permissions": _shape(action.get("permissions")),
                "error_codes": _shape(action.get("errorCodes")),
            }
            if (row["effect"] != {"kind": "scalar", "value": "read"} or
                    row["approval"] != {"kind": "scalar", "value": "none"} or
                    row["permissions"].get("knowledge_status") != "unknown"):
                raise OfficialCatalogRefused("OFFICIAL_READ_ONLY_POLICY_MISMATCH")
            rows.append(row)
    if len(rows) != 9:
        raise OfficialCatalogRefused("OFFICIAL_SELECTED_ACTION_COUNT_CHANGED")
    return {
        "evidence": ("SYNTHETIC_ONLY_CATALOG_METADATA" if synthetic_only
                     else "EXACT_FIRST_PARTY_KIT_CATALOG_READ_ONLY_METADATA"),
        "sha256": expected_sha, "actions": rows, "action_count": 9,
        "live_nas_verified": False, "checker_run": False,
        "license_verified": False, "original_catalog_uploaded": False,
        "provider_calls": 0, "official_creator_verified": False,
        "release_gate": "HOLD",
    }
