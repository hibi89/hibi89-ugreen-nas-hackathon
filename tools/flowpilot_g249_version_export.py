"""G249: opt-in, create-only privacy-redacted local version evidence.

Off-NAS development operator utility. Do not run on NAS mounts or mutable
untrusted folders. Never opens a source file or chooses a final version.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys

from flowpilot_g165_local_metadata_api import MetadataGate, MetadataRefused
from flowpilot_owner_local_audit import OwnerAuditError, _versions

SCHEMA = "flowpilot-local-version-evidence-g249-v1"
STATES = {"PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW"}


class ExportRefused(ValueError):
    """Errors deliberately never include a user path or file name."""


def _evidence(review: dict) -> dict:
    if (review.get("schema") != "flowpilot-owner-local-metadata-session-v1"
            or review.get("selected_intent") != "REVIEW_VERSIONS"
            or review.get("status") not in ("LOCAL_METADATA_FINDINGS_READY", "LOCAL_METADATA_BLOCKED")
            or review.get("approved_local_metadata_access") is not True
            or review.get("file_contents_opened") is not False
            or review.get("raw_filenames_returned") is not False
            or review.get("owner_root_returned") is not False
            or review.get("nas_verified") is not False
            or review.get("registered_expert_invoked") is not False
            or review.get("release_gate") != "HOLD"):
        raise ExportRefused("VERIFIED_LOCAL_REVIEW_REQUIRED")
    count, alternatives = review.get("required_count"), review.get("version_candidate_count")
    scope = review.get("scope_sha256")
    states = review.get("inspection_result")
    if (type(count) is not int or not 1 <= count <= 20
            or type(alternatives) is not int or not 1 <= alternatives <= 20
            or type(scope) is not str or len(scope) != 64
            or any(c not in "0123456789abcdef" for c in scope)
            or type(states) is not list or len(states) != count):
        raise ExportRefused("INVALID_LOCAL_EVIDENCE_SCOPE")
    clean = []
    for i, row in enumerate(states, 1):
        if (type(row) is not dict or row.get("index") != i
                or row.get("state") not in STATES):
            raise ExportRefused("INVALID_LOCAL_EVIDENCE_STATE")
        clean.append({"index": i, "state": row["state"]})
    return {
        "schema": SCHEMA,
        "status": "REDACTED_LOCAL_VERSION_EVIDENCE_NOT_NAS",
        "scope_sha256": scope,
        "required_count": count,
        "version_candidate_count": alternatives,
        "stages": ["SCOPED_READ", "VERSION_COMPARE", "OWNER_REVIEW", "REDACTED_EVIDENCE"],
        "findings": clean,
        "manual_owner_review_required": any(x["state"] == "VERSION_REVIEW" for x in clean),
        "auto_selected_final_version": False,
        "owner_file_contents_opened": False,
        "original_files_modified": False,
        "owner_paths_included": False,
        "nas_verified": False,
        "release_gate": "HOLD",
    }


def _write_new(path: Path, content: bytes) -> None:
    if (not isinstance(path, Path) or not path.is_absolute()
            or path.suffix.lower() != ".json" or len(str(path)) > 2048
            or str(path).startswith(("//", "\\\\"))):
        raise ExportRefused("INVALID_OUTPUT_DESTINATION")
    # Platform symlink/race protections vary; reject observed linked parents,
    # then rely on O_EXCL to refuse an existing file without overwrite.
    for parent in (path.parent, *path.parent.parents):
        try:
            info = parent.lstat()
        except (OSError, ValueError) as exc:
            raise ExportRefused("OUTPUT_PARENT_NOT_ACCESSIBLE") from exc
        if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400):
            raise ExportRefused("OUTPUT_PARENT_LINK_REFUSED")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except (OSError, ValueError) as exc:
        raise ExportRefused("CREATE_ONLY_OUTPUT_REFUSED") from exc
    try:
        with os.fdopen(fd, "wb") as fp:
            fp.write(content)
            fp.flush()
            os.fsync(fp.fileno())
    except OSError as exc:
        # A partial new file may remain; do not retry or delete an unknown path.
        raise ExportRefused("OUTPUT_WRITE_UNCERTAIN_NO_RETRY") from exc


def run(root: Path, required: list[str], candidates: list[str], output: Path | None,
        *, approve_metadata: bool = False, approve_create: bool = False) -> dict:
    if (type(approve_metadata) is not bool or type(approve_create) is not bool
            or approve_create and not approve_metadata):
        raise ExportRefused("TWO_DISTINCT_APPROVALS_REQUIRED")
    if type(candidates) is not list or not candidates:
        raise ExportRefused("VERSION_CANDIDATES_REQUIRED")
    try:
        versions = _versions(candidates)
        gate = MetadataGate(root)
        preview = gate.begin("review versions", required, versions=versions)
        if not approve_metadata:
            return {"status": "WAITING_LOCAL_METADATA_APPROVAL",
                    "required_count": preview["required_count"], "nas_verified": False,
                    "source_files_opened": False, "output_created": False, "release_gate": "HOLD"}
        inspected = gate.approve(preview["review_id"], preview["scope_sha256"],
                                 "APPROVE_LOCAL_METADATA_READ_ONLY")
        evidence = _evidence(inspected)
    except (OwnerAuditError, MetadataRefused, TypeError, ValueError) as exc:
        raise ExportRefused("LOCAL_VERSION_INSPECTION_REFUSED") from exc
    if not approve_create:
        return {"status": "WAITING_SEPARATE_REPORT_CREATION_APPROVAL",
                "findings": evidence["findings"], "output_created": False,
                "nas_verified": False, "release_gate": "HOLD"}
    if output is None:
        raise ExportRefused("EXPLICIT_OUTPUT_PATH_REQUIRED")
    raw = (json.dumps(evidence, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("ascii")
    if len(raw) > 10000:
        raise ExportRefused("OUTPUT_SIZE_LIMIT")
    _write_new(output, raw)
    return {"status": "LOCAL_VERSION_EVIDENCE_CREATED_NOT_NAS",
            "sha256": sha256(raw).hexdigest(), "byte_length": len(raw),
            "output_created": True, "source_files_opened": False,
            "nas_verified": False, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner-consented LOCAL version evidence, NOT Uliya/NAS.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--required", action="append", required=True)
    parser.add_argument("--candidate", action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approve-local-metadata", action="store_true")
    parser.add_argument("--approve-create-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.required, args.candidate, args.output,
                     approve_metadata=args.approve_local_metadata,
                     approve_create=args.approve_create_report)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ExportRefused as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "nas_verified": False, "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
