"""G122: one redacted guided-session timeline + replay-safe synthetic QA HTML.

All receipts in this file are LOCAL developer evidence, never registered Expert,
UGREEN NAS, live Docker, user file read/write or independent notarization.
No persistent files unless a caller explicitly chooses an output file path.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from html import escape
import json
import re
import sqlite3
import tempfile
from pathlib import Path
from typing import Callable

from flowpilot_guided_expert_session import run_guided_expert, GuidedRefused
from flowpilot_repair_ledger import run_once, verify_record

_SCHEMA = "flowpilot-session-timeline-v1"
_RUN = re.compile(r"run_[A-Za-z0-9_-]{8,48}\Z")
_SAFE_STAGE = frozenset(("INTENT", "SCOPE_AND_CONSENT", "OFFICIAL_CATALOG",
                          "SYNTHETIC_QA", "INTEGRITY", "REVIEW_AND_RELEASE"))
_SAFE_STATE = frozenset(("PASS", "WAITING", "BLOCKED", "NOT_RUN"))
_SAFE_ROLES = frozenset(("Architect", "Security", "Builder", "Repair", "QA"))
_SAFE_ROLE_STATUS = frozenset(("PASS", "REJECTED"))
_STEPS = {
    "INTENT": "Review a single known natural-language file-inspection intent.",
    "SCOPE_AND_CONSENT": "Confirm owner scope and both independent consent prompts.",
    "OFFICIAL_CATALOG": "Check pinned public catalog labels; registered Expert still not verified.",
    "SYNTHETIC_QA": "Run disposable fixture only; no NAS files or native SDK.",
    "INTEGRITY": "Verify local SQLite SHA-256 chain; not externally notarized.",
    "REVIEW_AND_RELEASE": "User review and native result proof required; release stays on HOLD.",
}

def _base(run_id: str) -> dict:
    return {
        "schema": _SCHEMA, "run_id": run_id, "release_gate": "HOLD",
        "nas_verified": False, "native_expert_invoked": False,
        "actual_docker_executed": False, "owner_data_read": False,
        "production_applied": False, "external_call_performed": False,
        "raw_paths_refs_contents_returned": False,
        "ledger_is_independently_notarized": False,
    }

def _stage(name: str, status: str) -> dict:
    assert name in _SAFE_STAGE and status in _SAFE_STATE
    return {"index": list(_STEPS).index(name) + 1, "code": name,
            "status": status, "description": _STEPS[name]}

def _role_summary(db: sqlite3.Connection, run_id: str) -> list[dict]:
    """Only use hardcoded role/status values from a chain already validated."""
    rows = db.execute(
        "SELECT kind, detail FROM fp119_events WHERE run_id=? ORDER BY seq",
        (run_id,),
    ).fetchall()
    out = []
    for kind, detail in rows:
        if kind != "ROLE":
            continue
        try:
            value = json.loads(detail)
        except (TypeError, ValueError):
            return []
        if (type(value) is not dict or set(value) != {"role", "status"}
                or value["role"] not in _SAFE_ROLES
                or value["status"] not in _SAFE_ROLE_STATUS):
            return []
        out.append({"role": value["role"], "status": value["status"]})
    return out[:8]


def run_session_timeline(
    goal: str, run_id: str, db: sqlite3.Connection,
    *, ask: Callable[[str], str], emit: Callable[[str], None] | None = None,
    kit_loader: Callable[[], bytes] | None = None,
    normalized_receipts: dict | None = None,
    synthetic_only_test_sha: str | None = None,
    approved_synthetic_qa: bool = False,
    inject_test_fault: bool = False,
) -> dict:
    """Consent-first review + opt-in synthetic-only QA + replay barrier.

    This inherits G119 duplicate protection per run ID/goal. It does not bind
    run IDs to real NAS scopes or authorize any repeated production operation.
    """
    if type(run_id) is not str or _RUN.fullmatch(run_id) is None:
        raise ValueError("Invalid opaque run ID")
    if not isinstance(db, sqlite3.Connection) or db.in_transaction:
        raise ValueError("Independent SQLite connection required")
    if type(approved_synthetic_qa) is not bool or type(inject_test_fault) is not bool:
        raise ValueError("Invalid opt-in/fault flag")
    output: list[str] = []
    def capture(value: str) -> None:
        # G121 emits *redacted structured* plan/result, never owner paths.
        if not isinstance(value, str) or not value.startswith(("FLOWPILOT_PREVIEW=", "FLOWPILOT_RESULT=")):
            raise ValueError("Untrusted guided emission")
        output.append(value)
        if emit is not None:
            emit(value)

    try:
        guided = run_guided_expert(
            goal, ask=ask, emit=capture, kit_loader=kit_loader,
            normalized_receipts=normalized_receipts,
            synthetic_only_test_sha=synthetic_only_test_sha,
            run_local_fixture=False,
        )
    except GuidedRefused:
        guided = {"status": "GUIDED_SESSION_REFUSED"}
    guided_status = guided.get("status", "GUIDED_SESSION_REFUSED")
    consent_ok = guided_status in (
        "AWAITING_PINNED_OFFICIAL_KIT", "OFFLINE_GUIDED_REVIEW_READY_NOT_NAS",
    )
    catalog_ok = guided_status == "OFFLINE_GUIDED_REVIEW_READY_NOT_NAS"
    stages = [
        _stage("INTENT", "BLOCKED" if guided_status == "BLOCKED_UNSUPPORTED_GOAL" else "PASS"),
        _stage("SCOPE_AND_CONSENT", "PASS" if consent_ok else "BLOCKED" if "REFUSED" in guided_status or "DECLINED" in guided_status else "WAITING"),
        _stage("OFFICIAL_CATALOG", "PASS" if catalog_ok else "BLOCKED" if "REFUSED" in guided_status or "BLOCKED" in guided_status else "WAITING"),
    ]
    qa = None
    integrity = "NOT_RUN"
    roles: list[dict] = []
    if consent_ok and approved_synthetic_qa:
        qa = run_once(goal, run_id, db, inject_test_fault=inject_test_fault)
        qa_status = qa["status"]
        if qa_status in ("SYNTHETIC_LEDGER_PASS", "SYNTHETIC_LEDGER_BLOCKED"):
            checked = verify_record(db, run_id)
            integrity = checked["status"]
            if integrity == "LOCAL_CHAIN_INTACT":
                roles = _role_summary(db, run_id)
                if not roles:
                    integrity = "LOCAL_CHAIN_INVALID"
        qa_state = "PASS" if (qa_status == "SYNTHETIC_LEDGER_PASS"
                              and integrity == "LOCAL_CHAIN_INTACT") else "BLOCKED"
        stages.append(_stage("SYNTHETIC_QA", qa_state))
        stages.append(_stage("INTEGRITY", "PASS" if integrity == "LOCAL_CHAIN_INTACT" else "BLOCKED"))
    else:
        stages.extend((_stage("SYNTHETIC_QA", "NOT_RUN"), _stage("INTEGRITY", "NOT_RUN")))
    stages.append(_stage("REVIEW_AND_RELEASE", "WAITING"))
    native_gate = (
        "VERIFY_REGISTERED_EXPERT_SIGNATURE_PERMISSIONS_AND_RESULT_SCHEMA"
        if catalog_ok else "PROVIDE_TRUSTED_OFFICIAL_KIT_AND_CONFIRM_CAPABILITY"
        if consent_ok else "REVIEW_AND_APPROVE_REQUIRED_INPUTS"
    )
    if qa is None:
        outcome = "NO_SYNTHETIC_EXECUTION"
    elif qa["status"] in ("DUPLICATE_BLOCKED", "RUN_ID_GOAL_CONFLICT"):
        # A prior run ID is never launched again. If the old chain exists,
        # an invalid history must not be disguised as a benign duplicate.
        try:
            prior_integrity = verify_record(db, run_id)["status"]
        except sqlite3.Error:
            prior_integrity = "LOCAL_CHAIN_INVALID"
        if prior_integrity != "LOCAL_CHAIN_INTACT":
            outcome = "PRIOR_LOCAL_EVIDENCE_INVALID"
            integrity = "LOCAL_CHAIN_INVALID"
        else:
            outcome = qa["status"]
    elif integrity != "LOCAL_CHAIN_INTACT":
        outcome = "LOCAL_EVIDENCE_UNVERIFIED"
    elif qa["status"] == "SYNTHETIC_LEDGER_PASS":
        outcome = "LOCAL_SYNTHETIC_QA_PASS_NATIVE_HOLD"
    else:
        outcome = "LOCAL_SYNTHETIC_QA_BLOCKED"
    result = {
        **_base(run_id),
        "status": outcome,
        "guided_status": guided_status,
        "catalog_verified_as_live_runtime": False,
        "local_synthetic_qa_opted_in": approved_synthetic_qa,
        "local_synthetic_qa_attempted": qa is not None,
        "local_synthetic_qa_executed_again": bool(qa is not None and
                            qa["status"] in ("SYNTHETIC_LEDGER_PASS", "SYNTHETIC_LEDGER_BLOCKED")),
        "evidence_integrity": integrity,
        "repair_count": (qa.get("repair_count", 0)
                         if qa is not None and integrity == "LOCAL_CHAIN_INTACT" else 0),
        "council_roles": roles,
        "steps": stages,
        "next_action": native_gate,
        "operator_runbook": list(guided.get("operator_runbook", ()))[:8],
    }
    # The G121 session never returns raw owner values; G119 hashes only
    # deterministic synthetic events. Keep all outward fields allowlisted.
    if emit is not None:
        emit("FLOWPILOT_TIMELINE=" + json.dumps(result, ensure_ascii=True))
    return result


def render_offline_dashboard(result: dict) -> str:
    """Self-contained static HTML, no scripts/remote assets, escape every field."""
    if type(result) is not dict or result.get("schema") != _SCHEMA:
        raise ValueError("Not a G122 timeline")
    for key in ("run_id", "status", "guided_status", "next_action"):
        if type(result.get(key)) is not str:
            raise ValueError("Invalid dashboard value")
    rows = result.get("steps")
    if type(rows) is not list or len(rows) != 6:
        raise ValueError("Invalid timeline")
    steps = []
    for index, row in enumerate(rows, 1):
        if (type(row) is not dict or row.get("code") not in _SAFE_STAGE
                or row.get("status") not in _SAFE_STATE
                or row.get("index") != index
                or row.get("description") != _STEPS[row["code"]]):
            raise ValueError("Invalid timeline step")
        steps.append(
            "<li><b>"+escape(row["code"])+"</b>"
            + " <small>"+escape(row["status"])+"</small><p>"
            +escape(row["description"])+"</p></li>"
        )
    roles = result.get("council_roles")
    if type(roles) is not list or len(roles) > 8 or any(
        type(x) is not dict or x.get("role") not in _SAFE_ROLES
        or x.get("status") not in _SAFE_ROLE_STATUS for x in roles
    ):
        raise ValueError("Invalid council summary")
    role_html = "".join(
        "<span>"+escape(x["role"])+": "+escape(x["status"])+"</span>"
        for x in roles
    ) or "<span>No verified local role trace</span>"
    runbook = result.get("operator_runbook")
    if type(runbook) is not list or len(runbook) > 8 or any(
        type(x) is not str or len(x) > 400 for x in runbook
    ):
        raise ValueError("Invalid operator runbook")
    instruction_html = "".join("<li>"+escape(x)+"</li>" for x in runbook)
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>FlowPilot Offline Review</title><style>"
        "body{font:15px system-ui,sans-serif;max-width:900px;margin:40px auto;padding:16px;color:#15232c;background:#f5f7f8}"
        "main{background:white;padding:28px;border:1px solid #d9e0e4;border-radius:14px}"
        "h1{font-size:24px}h2{font-size:18px;margin-top:28px}"
        "small{background:#f0f2f4;border-radius:6px;padding:4px 7px}"
        "li{margin:12px 0}p{color:#53636e;margin:5px 0}"
        "span{display:inline-block;padding:7px;border:1px solid #ccd6dc;border-radius:7px;margin:3px}"
        "footer{font-weight:650;margin-top:24px}</style></head><body><main>"
        "<h1>FlowPilot 3.0 — Offline session review</h1>"
        "<p>Run: "+escape(result["run_id"])+"</p>"
        "<p>Status: "+escape(result["status"])+"</p>"
        "<p>Guided plan: "+escape(result["guided_status"])+"</p>"
        "<h2>Execution and approval timeline</h2><ol>"
        +"".join(steps)+"</ol><h2>Deterministic council evidence</h2><div>"
        +role_html+"</div><h2>Operator runbook</h2><ol>"
        +instruction_html+"</ol><p>Next action: "+escape(result["next_action"])+"</p>"
        "<footer>RELEASE HOLD · NOT A LIVE ULIYA EXPERT, DOCKER OR NAS TEST</footer>"
        "</main></body></html>"
    )


def write_new_offline_html(path: Path, result: dict) -> None:
    """Explicit create-only local file: never replace an existing original."""
    if not isinstance(path, Path) or not path.is_absolute() or path.suffix.lower() != ".html":
        raise ValueError("Explicit absolute new .html output required")
    if any(p.is_symlink() for p in (path.parent, *path.parent.parents)) or str(path).startswith(("//", "\\\\")):
        raise ValueError("Network/reparse output location unsupported")
    content = render_offline_dashboard(result)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(content)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Redacted timeline + synthetic QA; NOT NAS")
    ap.add_argument("--goal", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--synthetic-qa", action="store_true",
                    help="Explicit opt-in for code-owned disposable QA")
    ap.add_argument("--inject-test-fault", action="store_true")
    ap.add_argument("--html-out", type=Path,
                    help="Optional absolute NEW local HTML report, never overwrite")
    args = ap.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g122-") as tmp:
            with closing(sqlite3.connect(Path(tmp)/"evidence.sqlite")) as db:
                result = run_session_timeline(
                    args.goal, args.run_id, db, ask=input, emit=None,
                    approved_synthetic_qa=args.synthetic_qa,
                    inject_test_fault=args.inject_test_fault,
                )
                if args.html_out is not None:
                    write_new_offline_html(args.html_out, result)
    except (ValueError, OSError, sqlite3.Error, GuidedRefused):
        result = {"status": "OFFLINE_TIMELINE_REFUSED", "release_gate": "HOLD"}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] not in ("OFFLINE_TIMELINE_REFUSED",) else 2

if __name__ == "__main__":
    raise SystemExit(main())
