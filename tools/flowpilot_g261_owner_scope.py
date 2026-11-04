"""G261: bounded owner-declared local NAS read-scope binder, NO native dispatch.

Never claims an approval is independently confirmed, a path exists, or any
registered Expert has accepted an instruction. No networking or filesystem
inspection of owner scope. Output only redacted typed metadata + hashes.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import PurePosixPath

SCHEMA = "flowpilot-g261-operator-scope-v1"
MODES = frozenset(("CHECK_DELIVERY", "REVIEW_VERSIONS", "PLAN_ONLY"))
PRINTABLE = re.compile(r"[\s\S]*")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
SENSITIVE = re.compile(r"(?i)(?:^|[/._-])(?:\.ssh|id_rsa|id_ed25519|\.env|secrets?|tokens?|credentials?|passwords?|private[_-]?key)(?:$|[/._-])")

class ScopeRefused(ValueError):
    pass


def _safe(value: object, *, root: bool = False) -> str:
    if (type(value) is not str or not value or len(value)>512 or
            value != unicodedata.normalize("NFC", value) or
            CONTROL.search(value) or "\\" in value or "'" in value or
            '"' in value or chr(96) in value or "$" in value or
            "<" in value or ">" in value or SENSITIVE.search(value)):
        raise ScopeRefused("UNSAFE_SCOPE_PATH")
    if root != value.startswith("/"):
        raise ScopeRefused("RELATIVE_OR_ABSOLUTE_SCOPE_MISMATCH")
    if value.startswith("//") or "//" in value or value.endswith("/"):
        raise ScopeRefused("NONCANONICAL_SCOPE_PATH")
    segments = value.split("/")
    if any(part in (".", "..", "") for part in (segments[1:] if root else segments)):
        raise ScopeRefused("TRAVERSAL_OR_EMPTY_COMPONENT")
    if root and value == "/":
        raise ScopeRefused("ROOT_FILESYSTEM_SCOPE_FORBIDDEN")
    if len(segments) > 14:
        raise ScopeRefused("SCOPE_DEPTH_LIMIT")
    return value


def bind_owner_scope(request: object) -> dict:
    """A user-declared owner request for a future read-only metadata *plan*.

    Never emits the raw owner path, required filenames or executable command.
    Consent flags are merely user-declared inputs, not provider permissions.
    """
    mandatory = {"schema", "mode", "authorized_root", "required_files",
                 "metadata_approved", "scope_authorized", "allow_symlinks",
                 "allow_content_read", "external_transfer_approved"}
    if type(request) is not dict or set(request) != mandatory:
        raise ScopeRefused("UNKNOWN_SCOPE_REQUEST_STRUCTURE")
    if request["schema"] != SCHEMA or request["mode"] not in MODES:
        raise ScopeRefused("UNSUPPORTED_OPERATOR_MODE")
    if (type(request["metadata_approved"]) is not bool or
            type(request["scope_authorized"]) is not bool or
            type(request["allow_symlinks"]) is not bool or
            type(request["allow_content_read"]) is not bool or
            type(request["external_transfer_approved"]) is not bool):
        raise ScopeRefused("INVALID_CONSENT_TYPES")
    if any((not request["metadata_approved"],
            not request["scope_authorized"], request["allow_symlinks"],
            request["allow_content_read"],
            request["external_transfer_approved"])):
        raise ScopeRefused("MISSING_OR_EXCESS_PERMISSIONS")
    root = _safe(request["authorized_root"], root=True)
    names = request["required_files"]
    if (type(names) is not list or not 1 <= len(names) <= 40 or
            len(names) != len(set(x for x in names if type(x) is str))):
        raise ScopeRefused("UNBOUNDED_OR_DUPLICATE_FILES")
    normalized = [_safe(x, root=False) for x in names]
    for name in normalized:
        # Restricted to bound root by construction: relative-only, no traversal.
        # Do NOT resolve symlinks here; real NAS Expert must reject those.
        combined = str(PurePosixPath(root) / name)
        if not combined.startswith(root + "/"):
            raise ScopeRefused("OUTSIDE_AUTHORIZED_SCOPE")
    canonical=json.dumps({"mode":request["mode"],"root":root,
                          "files":normalized,"metadata_approved":True,
                          "scope_authorized":True,"no_symlinks":True,
                          "no_content":True,"no_external_transfer":True},
                         ensure_ascii=False,sort_keys=True,separators=(",", ":"))
    digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema":"flowpilot-g261-redacted-owner-scope-receipt-v1",
            "status":"LOCAL_SCOPE_REQUEST_BOUND_AWAITING_REAL_EXPERT",
            "mode":request["mode"],"required_file_count":len(normalized),
            "request_sha256":digest,"owner_paths_exposed":False,
            "owner_declaration_is_live_permission_proof":False,
            "delegated_instruction_created":False,
            "nas_command_executed":False,
            "read_content_approved":False,"nas_verified":False,
            "release_gate":"HOLD"}
