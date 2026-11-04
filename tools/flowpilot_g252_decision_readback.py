"""G252 read-only owner decision/evidence binding verification, LOCAL ONLY.

No source-file scan, Uliya Expert, NAS, repair, output writes or third-party calls.
A SHA binds two local artifacts but is NOT an origin signature or NAS proof.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from hmac import compare_digest
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

from flowpilot_g251_owner_decision import (
    _private_path, _read_redacted_evidence, _unique_pairs,
    _reject_nonfinite, OwnerDecisionRefused, DECISION_SCHEMA,
)

DECISION_MAX_BYTES = 8192
CHOICES = frozenset(("OWNER_HOLD", "OWNER_SELECTED_PRIMARY", "OWNER_SELECTED_ALTERNATIVE"))
EXPECTED_DECISION_KEYS = frozenset((
    "schema", "status", "owner_choice", "review_scope_sha256", "source_evidence_sha256",
    "manual_selection_not_source_verified", "nas_capability_verified",
    "original_files_modified", "auto_selected_final_version", "ready_for_delivery", "release_gate",
))


class ReadbackRefused(ValueError):
    """Safe code-only refusal; no local path, owner record or content."""


def _read_decision_file(path: Path) -> tuple[dict[str, Any], str]:
    try:
        _private_path(path)
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)
                or bool(getattr(before, "st_file_attributes", 0) & 0x400)
                or before.st_size > DECISION_MAX_BYTES):
            raise ReadbackRefused("UNTRUSTED_DECISION_FILE")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as file:
            current = os.fstat(file.fileno())
            if (current.st_dev != before.st_dev or current.st_ino != before.st_ino
                    or not stat.S_ISREG(current.st_mode) or
                    current.st_size > DECISION_MAX_BYTES):
                raise ReadbackRefused("DECISION_REPLACED_OR_TOO_LARGE")
            blob = file.read(DECISION_MAX_BYTES + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, ReadbackRefused):
            raise
        raise ReadbackRefused("DECISION_READ_REFUSED") from exc
    if not blob or len(blob) > DECISION_MAX_BYTES:
        raise ReadbackRefused("DECISION_SIZE_REFUSED")
    try:
        doc = json.loads(blob.decode("utf-8"), object_pairs_hook=_unique_pairs,
                         parse_constant=_reject_nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ReadbackRefused("DECISION_JSON_REFUSED") from exc
    if (type(doc) is not dict or set(doc) != EXPECTED_DECISION_KEYS
            or doc.get("schema") != DECISION_SCHEMA
            or doc.get("status") != "LOCAL_OWNER_DECISION_RECORDED_NOT_NAS"
            or doc.get("owner_choice") not in CHOICES
            or doc.get("manual_selection_not_source_verified") is not True
            or any(doc.get(k) is not False for k in (
                "nas_capability_verified", "original_files_modified",
                "auto_selected_final_version", "ready_for_delivery"))
            or doc.get("release_gate") != "HOLD"
            or type(doc.get("review_scope_sha256")) is not str
            or re.fullmatch(r"[0-9a-f]{64}", doc["review_scope_sha256"]) is None
            or type(doc.get("source_evidence_sha256")) is not str
            or re.fullmatch(r"[0-9a-f]{64}", doc["source_evidence_sha256"]) is None):
        raise ReadbackRefused("UNVERIFIED_DECISION_SCHEMA")
    return doc, sha256(blob).hexdigest()


def verify(evidence: Path, decision: Path, *, approve_local_read: bool = False,
           expected_decision_sha256: str | None = None) -> dict:
    """Verify exact local byte hashes against the separately held G251 receipt."""
    if type(approve_local_read) is not bool:
        raise ReadbackRefused("EXACT_READ_CONSENT_REQUIRED")
    if not approve_local_read:
        return {"status": "WAITING_EXPLICIT_LOCAL_READ_APPROVAL",
                "input_read": False, "nas_verified": False, "release_gate": "HOLD"}
    if (type(expected_decision_sha256) is not str or
            re.fullmatch(r"[0-9a-f]{64}", expected_decision_sha256) is None):
        raise ReadbackRefused("EXPECTED_G251_DECISION_SHA_REQUIRED")
    try:
        source, source_digest = _read_redacted_evidence(evidence)
        user, decision_digest = _read_decision_file(decision)
    except (OwnerDecisionRefused, ReadbackRefused) as exc:
        raise ReadbackRefused("LOCAL_EVIDENCE_OR_DECISION_INVALID") from exc
    if (not compare_digest(decision_digest, expected_decision_sha256)
            or not compare_digest(user["source_evidence_sha256"], source_digest)
            or not compare_digest(user["review_scope_sha256"], source["scope_sha256"])):
        raise ReadbackRefused("LOCAL_DECISION_EVIDENCE_CONFLICT")
    return {"status": "LOCAL_OWNER_DECISION_BINDING_VERIFIED_NOT_NAS",
            "owner_choice": user["owner_choice"],
            "review_scope_sha256": source["scope_sha256"],
            "evidence_sha256": source_digest, "decision_sha256": decision_digest,
            "source_file_contents_opened": False, "external_transfer": False,
            "nas_verified": False, "decision_receipt_sha_verified": True,
            "decision_is_authenticated": False,
            "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read-only LOCAL owner version decision binding; not NAS")
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--decision", type=Path, required=True)
    p.add_argument("--approve-local-read", action="store_true")
    p.add_argument("--expected-decision-sha256",
                   help="Original G251 create-only output SHA; keep separately from decision file")
    args = p.parse_args(argv)
    try:
        print(json.dumps(verify(args.evidence, args.decision,
                                approve_local_read=args.approve_local_read,
                                expected_decision_sha256=args.expected_decision_sha256),sort_keys=True))
        return 0
    except ReadbackRefused as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
                          "nas_verified":False,"release_gate":"HOLD"},sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
