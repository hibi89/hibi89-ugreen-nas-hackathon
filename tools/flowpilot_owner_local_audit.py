"""G62: user-consented local-folder metadata audit, never UGREEN NAS/Uliya execution.

Read-only exact relative path lstat: no recursive listing, content reads,
hashing, network requests, writes, uploads, subprocess or external delegation.
This is a separate offline development pilot, NOT part of the Skill ZIP.

Filesystem metadata checks are non-atomic on Windows (junction/race risk).
Never use this tool for untrusted concurrently mutable directories or assume
it proves platform agent permissions or real NAS behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from flowpilot.evidence import ObservationBatch, Observed, report, safe_path, ItemState, Overall
from flowpilot.planner import draft_plan, State

SCOPE_LABEL = "/owner-approved-local-metadata-only"
MAX_ITEMS = 100
MAX_VERSIONS_PER_ITEM = 20
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class OwnerAuditError(ValueError):
    """Deliberately do not include actual paths, file names, or contents."""


def _valid_relative(value: str) -> str:
    try:
        return safe_path(value)
    except (TypeError, ValueError) as exc:
        raise OwnerAuditError("Invalid or restricted relative file name") from exc


def _reparse_or_link(metadata: os.stat_result) -> bool:
    # Junction/reparse detection supplements is_symlink on Windows.
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT
    )


def _valid_root(root: Path) -> Path:
    p = Path(root)
    if not p.is_absolute():
        raise OwnerAuditError("Select an absolute local folder")
    # UNC, Windows device paths and mapped remote drives are not validated
    # as local by this tool. Reject explicit UNC/device roots; the user must
    # separately ensure that any mapped mount is NOT a NAS.
    raw = os.fspath(p)
    if raw.startswith(("\\\\", "//")) or (os.name == "nt" and p.drive.startswith("\\\\")):
        raise OwnerAuditError("UNC or device network root not supported")
    for ancestor in (p, *p.parents):
        try:
            info = ancestor.lstat()
        except (OSError, ValueError) as exc:
            raise OwnerAuditError("Unverifiable root or ancestor") from exc
        if _reparse_or_link(info):
            raise OwnerAuditError("Symlink or reparse point in selected root")
    try:
        info = p.lstat()
    except OSError as exc:
        raise OwnerAuditError("Selected local root not accessible") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise OwnerAuditError("Selected local root must be a directory")
    return p


def _inspect_one(root: Path, relative: str, serial: int) -> tuple[Observed | None, bool]:
    child = root
    parts = relative.split("/")
    for index, part in enumerate(parts):
        child = child / part
        try:
            entry = child.lstat()
        except FileNotFoundError:
            return None, True
        except (OSError, ValueError):
            return Observed(relative, "", contained=None), False
        if _reparse_or_link(entry):
            return Observed(relative, "", is_symlink=True, contained=None), True
        if index + 1 < len(parts):
            if not stat.S_ISDIR(entry.st_mode):
                return Observed(relative, "", contained=None), True
        elif stat.S_ISREG(entry.st_mode):
            # The opaque reference deliberately contains no owner path,
            # content, original file name, hash or external stable identifier.
            return Observed(relative, f"local-metadata://item-{serial}", contained=True), True
        else:
            return Observed(relative, "", contained=None), True
    return None, False


def inspect_owner_folder(
    root: Path, required: Sequence[str], *, version_candidates: dict[str, Sequence[str]] | None = None,
    goal: str = "check required files", metadata_consent: bool = False
) -> dict[str, Any]:
    """Inspect only explicitly chosen local path metadata, never file content."""
    if not isinstance(goal, str) or not 0 < len(goal.strip()) <= 2048:
        raise OwnerAuditError("Provide one bounded file audit goal")
    if not isinstance(required, (list, tuple)) or not 1 <= len(required) <= MAX_ITEMS:
        raise OwnerAuditError("Provide 1–100 exact relative paths")
    normalized = tuple(_valid_relative(x) for x in required)
    if len(set(normalized)) != len(normalized):
        raise OwnerAuditError("Duplicate required paths")
    supplied = version_candidates or {}
    if not isinstance(supplied, dict) or set(supplied) - set(normalized):
        raise OwnerAuditError("Version candidate not bound to required path")
    versions: dict[str, tuple[str, ...]] = {}
    for owner_item, alternatives in supplied.items():
        if not isinstance(alternatives, (list, tuple)) or len(alternatives) > MAX_VERSIONS_PER_ITEM:
            raise OwnerAuditError("Too many candidate paths")
        names = tuple(_valid_relative(x) for x in alternatives)
        if len(names) != len(set(names)) or owner_item in names:
            raise OwnerAuditError("Duplicate or self-reference version candidate")
        versions[owner_item] = names
    paths = list(dict.fromkeys((*normalized, *(n for seq in versions.values() for n in seq))))
    if len(paths) > MAX_ITEMS:
        raise OwnerAuditError("Too many exact file observations")
    # All intent, scope, version and consent checks happen BEFORE touching
    # any owner-provided directory. No permission = no path metadata access.
    if type(metadata_consent) is not bool:
        raise OwnerAuditError("Metadata consent must be a boolean")
    plan = draft_plan(goal, SCOPE_LABEL, normalized,
                      metadata_approved=metadata_consent,
                      unknown_processing_accepted=metadata_consent)
    result = {
        "mode": "CONSENTED_OWNER_LOCAL_METADATA_ONLY_NOT_NAS",
        "status": plan.state.value,
        "goal_type": plan.intent.value if plan.intent else None,
        "items": [],
        "inspected_local_metadata": False,
        "item_count": len(normalized),
        "file_contents_opened": False,
        "raw_paths_or_file_names_in_output": False,
        "nas_verified": False,
        "registered_uliya_agent_invoked": False,
        "official_creator_invoked": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
        "limitations": ["LOCAL_ONLY", "NO_VENDOR_AGENT_EVIDENCE",
                        "FILESYSTEM_METADATA_RACE_NOT_EXCLUDED_ON_ALL_PLATFORMS"],
    }
    if plan.state is not State.READY_FOR_ADAPTER_CHECK:
        return result
    scope = _valid_root(Path(root))
    observed: list[Observed] = []
    locally_complete = True
    for index, name in enumerate(paths, start=1):
        item, checked = _inspect_one(scope, name, index)
        locally_complete = locally_complete and checked
        if item is not None:
            observed.append(item)
    # This batch models the LOCAL lstat metadata reader for reuse of the
    # conservative evidence rules; true flags must never be interpreted as
    # proof that an actual Uliya Expert is installed or registered.
    batch = ObservationBatch(
        authorized_root=SCOPE_LABEL, observations=tuple(observed),
        permission_confirmed=True, registered_adapter_confirmed=True,
        scan_complete=locally_complete, pagination_complete=locally_complete,
        failed=not locally_complete,
    )
    evidence = report(normalized, batch, version_candidates=versions)
    result["status"] = evidence.overall.value
    result["inspected_local_metadata"] = True
    result["items"] = [
        {"index": index + 1, "state": item.state.value,
         "local_reference_count": len(item.evidence)}
        for index, item in enumerate(evidence.items)
    ]
    result["limitations"].append("LOCAL_LSTAT_ONLY_NOT_OFFICIAL_AGENT")
    if not locally_complete:
        result["limitations"].append("ONE_OR_MORE_LOCAL_METADATA_CHECKS_FAILED")
    return result


def _versions(raw: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for pair in raw:
        if "=" not in pair:
            raise OwnerAuditError("Version mapping requires required=candidate")
        key, value = pair.split("=", 1)
        k, v = _valid_relative(key), _valid_relative(value)
        result.setdefault(k, []).append(v)
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Read-only owner local folder metadata pilot. NOT UGOS, Uliya or NAS.")
    ap.add_argument("--root", required=True, type=Path, help="Owner's local folder, not NAS")
    ap.add_argument("--required", required=True, action="append", help="Exact relative file, repeatable")
    ap.add_argument("--candidate", action="append", default=[], help="required=candidate, optional")
    ap.add_argument("--goal", default="check required files")
    ap.add_argument("--approve-local-metadata", action="store_true",
                    help="Explicitly consent to local metadata access")
    args = ap.parse_args(argv)
    try:
        row = inspect_owner_folder(args.root, args.required,
                                   version_candidates=_versions(args.candidate),
                                   goal=args.goal,
                                   metadata_consent=args.approve_local_metadata)
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0 if row["status"] != "BLOCKED" else 1
    except (OwnerAuditError, ValueError, OSError):
        print(json.dumps({"status": "LOCAL_AUDIT_REFUSED", "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
