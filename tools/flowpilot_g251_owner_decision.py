"""G251: offline, consented owner choice for a *redacted* local version review.

This is not a registered NAS Expert action and never reads a real source file.
Consumes only an already exported G249 JSON evidence file. The choice is a
manual owner statement, not validation that a version is authoritative.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

EVIDENCE_SCHEMA = "flowpilot-local-version-evidence-g249-v1"
DECISION_SCHEMA = "flowpilot-local-owner-version-decision-g251-v1"
READ_LIMIT = 10000
CHOICES = {"hold": "OWNER_HOLD", "primary": "OWNER_SELECTED_PRIMARY", "alternative": "OWNER_SELECTED_ALTERNATIVE"}
EXPECTED_KEYS = frozenset({
    "schema", "status", "scope_sha256", "required_count", "version_candidate_count",
    "stages", "findings", "manual_owner_review_required",
    "auto_selected_final_version", "owner_file_contents_opened",
    "original_files_modified", "owner_paths_included", "nas_verified", "release_gate",
})
EXPECTED_STAGES = ["SCOPED_READ", "VERSION_COMPARE", "OWNER_REVIEW", "REDACTED_EVIDENCE"]

class OwnerDecisionRefused(ValueError):
    """Never place a private path or the evidence text in an error."""


def _private_path(path: Path, *, require_json: bool = True) -> None:
    if (not isinstance(path, Path) or not path.is_absolute()
            or len(str(path)) > 2048 or str(path).startswith(("//", "\\\\"))
            or (require_json and path.suffix.lower() != ".json")):
        raise OwnerDecisionRefused("INVALID_ABSOLUTE_JSON_PATH")
    for parent in (path.parent, *path.parent.parents):
        try:
            s = parent.lstat()
        except (OSError, ValueError) as exc:
            raise OwnerDecisionRefused("UNTRUSTED_PARENT_PATH") from exc
        if (stat.S_ISLNK(s.st_mode) or bool(getattr(s, "st_file_attributes", 0) & 0x400)):
            raise OwnerDecisionRefused("SYMLINK_OR_REPARSE_PARENT_REFUSED")


def _unique_pairs(pairs):
    obj = {}
    for k,v in pairs:
        if k in obj:
            raise OwnerDecisionRefused("DUPLICATE_EVIDENCE_JSON_KEY")
        obj[k] = v
    return obj


def _reject_nonfinite(value):
    raise OwnerDecisionRefused("NONFINITE_JSON_NUMBER")


def _read_redacted_evidence(path: Path) -> tuple[dict[str,Any], str]:
    _private_path(path)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as source:
            info = os.fstat(source.fileno())
            if (not stat.S_ISREG(info.st_mode) or
                    bool(getattr(info, "st_file_attributes", 0) & 0x400) or
                    info.st_size > READ_LIMIT):
                raise OwnerDecisionRefused("UNTRUSTED_EVIDENCE_FILE")
            raw = source.read(READ_LIMIT + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, OwnerDecisionRefused):
            raise
        raise OwnerDecisionRefused("EVIDENCE_READ_REFUSED") from exc
    if not raw or len(raw) > READ_LIMIT:
        raise OwnerDecisionRefused("EVIDENCE_LIMIT_EXCEEDED")
    try:
        item = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                          parse_constant=_reject_nonfinite)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise OwnerDecisionRefused("INVALID_REDACTED_JSON") from exc
    if (type(item) is not dict or set(item) != EXPECTED_KEYS or
            item.get("schema") != EVIDENCE_SCHEMA or
            item.get("status") != "REDACTED_LOCAL_VERSION_EVIDENCE_NOT_NAS" or
            item.get("stages") != EXPECTED_STAGES or
            item.get("manual_owner_review_required") is not True or
            any(item.get(k) is not False for k in (
                "auto_selected_final_version", "owner_file_contents_opened",
                "original_files_modified", "owner_paths_included", "nas_verified")) or
            item.get("release_gate") != "HOLD" or
            type(item.get("scope_sha256")) is not str or
            re.fullmatch(r"[0-9a-f]{64}",item["scope_sha256"]) is None or
            type(item.get("required_count")) is not int or item["required_count"] != 1 or
            type(item.get("version_candidate_count")) is not int or item["version_candidate_count"] != 1 or
            item.get("findings") != [{"index": 1, "state": "VERSION_REVIEW"}]):
        raise OwnerDecisionRefused("UNSUPPORTED_OR_UNVERIFIED_VERSION_EVIDENCE")
    return item, sha256(raw).hexdigest()


def run(evidence_path: Path, output_path: Path | None, owner_choice: str | None,
        *, approve_read_evidence: bool = False, approve_save_decision: bool = False) -> dict:
    if type(approve_read_evidence) is not bool or type(approve_save_decision) is not bool:
        raise OwnerDecisionRefused("INVALID_APPROVAL_TYPE")
    if not approve_read_evidence:
        if approve_save_decision:
            raise OwnerDecisionRefused("INDEPENDENT_READ_APPROVAL_REQUIRED")
        return {"status": "WAITING_LOCAL_EVIDENCE_READ_APPROVAL",
                "evidence_read": False, "output_created": False,
                "nas_verified": False, "release_gate": "HOLD"}
    evidence, evidence_digest = _read_redacted_evidence(evidence_path)
    if not approve_save_decision:
        return {"status": "WAITING_SEPARATE_OWNER_DECISION_APPROVAL",
                "scope_sha256": evidence["scope_sha256"],
                "evidence_sha256": evidence_digest,
                "choices": ["hold", "primary", "alternative"],
                "output_created": False, "nas_verified": False, "release_gate": "HOLD"}
    if type(owner_choice) is not str or owner_choice not in CHOICES:
        raise OwnerDecisionRefused("EXACT_OWNER_CHOICE_REQUIRED")
    if output_path is None:
        raise OwnerDecisionRefused("OUTPUT_PATH_REQUIRED")
    # No 'READY' claim, despite deliberate manual choice. Real NAS provenance
    # and relative file identities cannot be recovered from the G249 report.
    decision = {
        "schema": DECISION_SCHEMA,
        "status": "LOCAL_OWNER_DECISION_RECORDED_NOT_NAS",
        "owner_choice": CHOICES[owner_choice],
        "review_scope_sha256": evidence["scope_sha256"],
        "source_evidence_sha256": evidence_digest,
        "manual_selection_not_source_verified": True,
        "nas_capability_verified": False,
        "original_files_modified": False,
        "auto_selected_final_version": False,
        "ready_for_delivery": False,
        "release_gate": "HOLD",
    }
    raw = (json.dumps(decision, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("ascii")
    _private_path(output_path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(output_path, flags, 0o600)
    except (OSError, ValueError) as exc:
        raise OwnerDecisionRefused("CREATE_ONLY_DECISION_OUTPUT_REFUSED") from exc
    try:
        with os.fdopen(fd,"wb") as dest:
            dest.write(raw)
            dest.flush()
            os.fsync(dest.fileno())
    except OSError as exc:
        raise OwnerDecisionRefused("OUTPUT_WRITE_UNCERTAIN_NO_RETRY") from exc
    return {"status": decision["status"], "decision_sha256": sha256(raw).hexdigest(),
            "decision_bytes": len(raw), "output_created": True,
            "nas_verified": False, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local redacted version owner decision, NOT NAS")
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--owner-choice", choices=tuple(CHOICES))
    parser.add_argument("--approve-read-evidence", action="store_true")
    parser.add_argument("--approve-save-decision", action="store_true")
    args = parser.parse_args(argv)
    try:
        response = run(args.evidence, args.output, args.owner_choice,
                       approve_read_evidence=args.approve_read_evidence,
                       approve_save_decision=args.approve_save_decision)
        print(json.dumps(response, sort_keys=True))
        return 0
    except OwnerDecisionRefused as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "release_gate": "HOLD", "nas_verified": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
