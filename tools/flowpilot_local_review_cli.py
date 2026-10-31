"""G137 one-entrypoint, locally scoped FlowPilot review: plan -> consented capture -> delta.

Reuses proven G64/G134/G136 contracts; NOT native Uliya, NAS, Docker or an LLM.
The accepted command is ONE exact Korean/English G64 stage, not arbitrary NLU.
Requires independent opt-ins before local metadata reads and SQLite writes.
Output and optional static offline HTML contain only indexed states, never paths.
"""
from __future__ import annotations

import argparse
from html import escape
import json
import os
from pathlib import Path
import stat

from flowpilot_text_workflow import parse_instructions, WorkflowRefused
from flowpilot_owner_local_audit import inspect_owner_folder, OwnerAuditError
from flowpilot_local_audit_ledger import run_local_audit_ledger
from flowpilot_local_audit_delta import compare_local_audits
from flowpilot_local_snapshot_review import inspect_local_snapshot

_SCHEMA = "flowpilot-local-review-cli-v1"
_ALLOWED_STATES = frozenset(("PRESENT", "MISSING", "VERSION_REVIEW", "NOT_CHECKED"))
_ALLOWED_RESULTS = frozenset(("SNAPSHOT_DELTA_REVIEW_REQUIRED", "SNAPSHOTS_EQUAL_REVIEW_REQUIRED"))
_MAX_CHANGES = 100


def _base() -> dict:
    return {"schema": _SCHEMA, "release_gate": "HOLD", "local_only": True,
            "owner_file_contents_opened": False, "raw_paths_returned": False,
            "nas_verified": False, "native_uliya_expert_invoked": False,
            "docker_executed": False, "production_applied": False,
            "external_api_called": False, "independently_notarized": False}


def _one_stage(instructions: str) -> tuple[str, list[str], dict[str, list[str]]]:
    recipe = parse_instructions(instructions)
    if len(recipe["steps"]) != 1:
        raise ValueError("ONLY_ONE_STAGE_SUPPORTED")
    step = recipe["steps"][0]
    return step["goal"], step["required"], step.get("candidates", {})


def review_local(*, action: str, instructions: str, root: Path,
                 db: Path | None = None, run_id: str | None = None,
                 previous_id: str | None = None, current_id: str | None = None,
                 mode: str | None = None, approve_local_metadata: bool = False,
                 approve_local_db_write: bool = False) -> dict:
    """No hidden IO: preview never touches owner folder or DB; capture requires two consents.

    The compare action uses only historical stored SQLite metadata, not owner files.
    It has no implicit release approval even if all previously missing items return.
    """
    base = _base()
    if type(approve_local_metadata) is not bool or type(approve_local_db_write) is not bool:
        return {**base, "status": "INVALID_FLAGS"}
    if type(action) is not str or action not in ("preview", "capture", "compare", "review"):
        return {**base, "status": "UNSUPPORTED_ACTION"}
    if not isinstance(root, Path):
        return {**base, "status": "INVALID_SCOPE"}
    try:
        goal, required, candidates = _one_stage(instructions)
        # Existing G62 preflight is mandatory for all actions; metadata_consent=False
        # does not inspect root nor access any file contents.
        preflight = inspect_owner_folder(root, required, version_candidates=candidates,
                                         goal=goal, metadata_consent=False)
        if preflight["status"] != "WAITING_APPROVAL":
            return {**base, "status": "UNSUPPORTED_SCOPE_OR_GOAL"}
        if action == "preview":
            if (db is not None or run_id is not None or mode is not None
                    or previous_id is not None or current_id is not None
                    or approve_local_metadata or approve_local_db_write):
                return {**base, "status": "PREVIEW_HAS_UNEXPECTED_OPTIONS"}
            return {**base, "status": "WAITING_TWO_SEPARATE_LOCAL_APPROVALS",
                    "planned_steps": 1, "required_item_count": len(required),
                    "local_folder_inspected": False, "database_modified": False,
                    "next_action": "OWNER_REVIEW_SCOPE_AND_CONSENT"}
        if action == "capture":
            if (not isinstance(db, Path) or type(run_id) is not str
                    or mode not in ("new", "append") or previous_id is not None
                    or current_id is not None):
                return {**base, "status": "INVALID_CAPTURE_ARGUMENTS"}
            if not (approve_local_metadata and approve_local_db_write):
                return {**base, "status": "WAITING_TWO_SEPARATE_LOCAL_APPROVALS"}
            captured = run_local_audit_ledger(
                db, run_id, mode=mode, root=root, required=required,
                candidates=candidates or None, goal=goal,
                approve_local_metadata=True, approve_local_db_write=True)
            return {**base, "status": captured["status"],
                    "item_count": captured.get("item_count", 0),
                    "audit_result": captured.get("audit_result", "NOT_CHECKED"),
                    "evidence_integrity": captured.get("evidence_integrity", "NOT_RUN"),
                    "database_modified": captured.get("database_modified", False),
                    "local_metadata_check_completed": captured.get("local_metadata_check_completed", False)}
        if action == "review":
            if (not isinstance(db, Path) or type(run_id) is not str
                    or mode is not None or previous_id is not None
                    or current_id is not None or approve_local_metadata
                    or approve_local_db_write):
                return {**base, "status": "INVALID_REVIEW_ARGUMENTS"}
            snapshot = inspect_local_snapshot(
                db, run_id, root=root, required=required,
                candidates=candidates or None, goal=goal)
            if snapshot["status"] != "LOCAL_SNAPSHOT_REVIEW_REQUIRED":
                return {**base, "status": snapshot["status"],
                        "database_modified": False, "local_folder_inspected": False}
            return {**base, **snapshot, "local_folder_inspected": False}
        if (not isinstance(db, Path) or type(previous_id) is not str
                or type(current_id) is not str or run_id is not None or mode is not None
                or approve_local_metadata or approve_local_db_write):
            return {**base, "status": "INVALID_COMPARE_ARGUMENTS"}
        comparison = compare_local_audits(
            db, previous_id, current_id, root=root,
            required=required, candidates=candidates or None, goal=goal)
        if comparison["status"] not in _ALLOWED_RESULTS:
            return {**base, "status": comparison["status"],
                    "database_modified": False, "local_folder_inspected": False}
        return {**base, **comparison, "local_only": True,
                "local_folder_inspected": False}
    except (WorkflowRefused, OwnerAuditError, KeyError, TypeError, ValueError, OSError):
        return {**base, "status": "LOCAL_REVIEW_REFUSED"}



def render_single_snapshot_html(value: dict) -> str:
    """Static, allowlisted index-only HTML for a single scoped LOCAL receipt."""
    if (type(value) is not dict
            or value.get("schema") != "flowpilot-local-snapshot-review-v1"
            or value.get("status") != "LOCAL_SNAPSHOT_REVIEW_REQUIRED"
            or value.get("release_gate") != "HOLD"
            or value.get("scope_match_verified_locally") is not True
            or value.get("nas_verified") is not False
            or value.get("database_modified") is not False
            or value.get("owner_folder_inspected_again") is not False):
        raise ValueError("INVALID_LOCAL_SNAPSHOT")
    items = value.get("items")
    count = value.get("item_count")
    if (type(items) is not list or type(count) is not int
            or not 1 <= count <= 100 or len(items) != count
            or value.get("audit_result") not in ("BLOCKED", "NEEDS_REVIEW")):
        raise ValueError("INVALID_SNAPSHOT_ITEMS")
    rows = []
    has_missing = False
    for idx, item in enumerate(items, 1):
        if (type(item) is not dict
                or set(item) != {"index", "state", "local_reference_count"}
                or type(item["index"]) is not int or item["index"] != idx
                or type(item["state"]) is not str
                or item["state"] not in _ALLOWED_STATES
                or type(item["local_reference_count"]) is not int
                or not 0 <= item["local_reference_count"] <= 20):
            raise ValueError("UNTRUSTED_SNAPSHOT_ITEM")
        has_missing |= item["state"] == "MISSING"
        rows.append("<tr><td>" + str(idx) + "</td><td>"
                    + escape(item["state"]) + "</td><td>"
                    + str(item["local_reference_count"]) + "</td></tr>")
    if (value["audit_result"] == "BLOCKED") != has_missing:
        raise ValueError("INCONSISTENT_SNAPSHOT_RESULT")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>FlowPilot local single snapshot</title>"
            "<style>body{font:15px system-ui,sans-serif;max-width:860px;margin:32px auto;padding:20px;color:#1d2935}"
            "table{border-collapse:collapse;width:100%}td,th{padding:10px;border:1px solid #bfc9d2;text-align:left}"
            "h1{font-size:24px}footer{margin-top:30px;font-weight:700}small{color:#59687a}</style></head>"
            "<body><main><h1>FlowPilot 3.0 local snapshot review</h1>"
            "<p>Local audit result: " + escape(value["audit_result"]) + "</p>"
            "<p>Items reviewed: " + str(count) + "</p>"
            "<table><thead><tr><th>Item index</th><th>State</th><th>Local reference count</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table>"
            "<p><small>Read-only local SQLite checksum; no filenames, paths, contents,"
            " signed timestamps or independently attested provenance.</small></p>"
            "<footer>RELEASE HOLD — NOT A REAL ULIYA EXPERT OR NAS TEST</footer></main></body></html>")


def render_review_html(value: dict) -> str:
    """Render recognized scope-bound receipts as self-contained inert HTML."""
    if type(value) is dict and value.get("schema") == "flowpilot-local-snapshot-review-v1":
        return render_single_snapshot_html(value)
    if (type(value) is not dict or value.get("status") not in _ALLOWED_RESULTS
            or value.get("schema") != "flowpilot-local-audit-delta-v1"
            or value.get("release_gate") != "HOLD"
            or value.get("nas_verified") is not False
            or value.get("database_modified") is not False
            or value.get("owner_folder_inspected_again") is not False):
        raise ValueError("INVALID_REVIEW_RESULT")
    changes = value.get("changes")
    if (type(changes) is not list or len(changes) > _MAX_CHANGES
            or value.get("change_count") != len(changes)):
        raise ValueError("INVALID_CHANGES")
    rows = []
    for change in changes:
        if (type(change) is not dict
                or set(change) != {"index", "before", "after", "reference_count_before", "reference_count_after"}
                or type(change["index"]) is not int or not 1 <= change["index"] <= 100
                or change["before"] not in _ALLOWED_STATES
                or change["after"] not in _ALLOWED_STATES
                or any(type(change[k]) is not int or not 0 <= change[k] <= 20
                       for k in ("reference_count_before", "reference_count_after"))):
            raise ValueError("UNTRUSTED_CHANGE")
        rows.append("<tr><td>" + str(change["index"]) + "</td><td>"
                    + escape(change["before"]) + "</td><td>"
                    + escape(change["after"]) + "</td></tr>")
    counters = ("new_missing_count", "newly_observed_missing_from_uncertain_count",
                "resolved_missing_to_present_count", "new_uncertainty_count")
    if any(type(value.get(k)) is not int or not 0 <= value[k] <= 100 for k in counters):
        raise ValueError("INVALID_COUNTERS")
    if type(value.get("item_count")) is not int or not 1 <= value["item_count"] <= 100:
        raise ValueError("INVALID_ITEM_COUNT")
    status = escape(value["status"])
    table = "".join(rows) if rows else "<tr><td colspan='3'>No recorded changes</td></tr>"
    counts = "".join("<li>" + escape(k.replace("_", " ")) + ": " + str(value[k]) + "</li>" for k in counters)
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>FlowPilot local audit comparison</title>"
            "<style>body{font:15px system-ui,sans-serif;max-width:860px;margin:32px auto;padding:20px;color:#1d2935}"
            "table{border-collapse:collapse;width:100%}td,th{padding:10px;border:1px solid #bfc9d2;text-align:left}"
            "h1{font-size:24px}footer{margin-top:30px;font-weight:700}small{color:#59687a}</style></head>"
            "<body><main><h1>FlowPilot 3.0 local audit history</h1><p>Status: " + status + "</p>"
            "<p>Items reviewed: " + str(value["item_count"]) + "</p><ul>" + counts + "</ul>"
            "<h2>Indexed changes</h2><table><thead><tr><th>Item</th><th>Previous</th><th>Current</th></tr></thead>"
            "<tbody>" + table + "</tbody></table><p><small>Local SQLite checksums only."
            " No signed timestamps, immutable provenance, names, paths or file contents.</small></p>"
            "<footer>RELEASE HOLD — NOT A REAL ULIYA EXPERT OR NAS TEST</footer></main></body></html>")


def write_new_report_html(path: Path, report: dict) -> None:
    """Create a NEW HTML report only, never replace owner originals or write DB."""
    html = render_review_html(report)
    if (not isinstance(path, Path) or not path.is_absolute() or path.suffix.lower() != ".html"
            or str(path).startswith(("//", "\\\\")) or not path.parent.is_dir()
            or any(p.is_symlink() for p in (path, path.parent, *path.parent.parents))):
        raise ValueError("INVALID_OUTPUT_PATH")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(html)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bounded local review CLI; NO actual NAS/Expert")
    ap.add_argument("--action", required=True, choices=("preview", "capture", "compare", "review"))
    ap.add_argument("--instructions", required=True, help="One G64 bounded command, e.g. '파일 확인: README.md'")
    ap.add_argument("--root", type=Path, required=True, help="Local directory (not a NAS mount)")
    ap.add_argument("--db", type=Path)
    ap.add_argument("--mode", choices=("new", "append"))
    ap.add_argument("--run-id")
    ap.add_argument("--previous-id")
    ap.add_argument("--current-id")
    ap.add_argument("--approve-local-metadata", action="store_true")
    ap.add_argument("--approve-local-db-write", action="store_true")
    ap.add_argument("--html-out", type=Path, help="EXPLICIT new absolute .html report; compare only")
    args = ap.parse_args(argv)
    if args.html_out is not None and args.action not in ("compare", "review"):
        result = {**_base(), "status": "HTML_ONLY_FOR_COMPARE"}
    else:
        result = review_local(
            action=args.action, instructions=args.instructions, root=args.root,
            db=args.db, run_id=args.run_id, previous_id=args.previous_id,
            current_id=args.current_id, mode=args.mode,
            approve_local_metadata=args.approve_local_metadata,
            approve_local_db_write=args.approve_local_db_write)
        if args.action in ("compare", "review") and args.html_out is not None and result["status"] in (_ALLOWED_RESULTS | {"LOCAL_SNAPSHOT_REVIEW_REQUIRED"}):
            try:
                write_new_report_html(args.html_out, result)
                result = {**result, "local_html_created": True}
            except (ValueError, FileExistsError, OSError):
                result = {**_base(), "status": "HTML_EXPORT_REFUSED"}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    accepted = {"WAITING_TWO_SEPARATE_LOCAL_APPROVALS", "LOCAL_METADATA_EVIDENCE_STORED_REVIEW_REQUIRED",
                "SNAPSHOT_DELTA_REVIEW_REQUIRED", "SNAPSHOTS_EQUAL_REVIEW_REQUIRED",
                "LOCAL_SNAPSHOT_REVIEW_REQUIRED"}
    return 0 if result["status"] in accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())