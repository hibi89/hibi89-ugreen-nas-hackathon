"""Static, privacy-preserving FlowPilot 3.0 review Command Center.

Render only the REDACTED, checksum-validated synthetic owner-review JSON.
No JS, network, NAS, Uliya, local file discovery, or document content access.
The checksum detects accidental changes; it is NOT a trusted attestation.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re

MAX_JSON_BYTES = 1_000_000
SCHEMA = "flowpilot-synthetic-owner-review-v1"
STATE_ORDER = ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
DOC_STATES = frozenset({
    "NOT_REQUESTED", "CONTENT_NOT_CHECKED", "WAITING_METADATA_APPROVAL",
    "BLOCKED_UNVERIFIED_INVENTORY", "WAITING_USER",
    "WAITING_SEPARATE_DOCUMENT_APPROVAL", "BLOCKED_RUNTIME_PROVENANCE_UNVERIFIED",
    "SYNTHETIC_INSTRUCTION_DRAFT_NOT_EXECUTED", "SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW",
    "SYNTHETIC_INCOMPLETE_OR_FAILED_NEEDS_REVIEW",
})
OVERALL_STATES = frozenset({
    "SYNTHETIC_NEEDS_REVIEW", "SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW",
    "WAITING_OWNER_INPUT_OR_APPROVAL",
})


class DashboardRefused(ValueError):
    pass


def verify_public_report(report: dict) -> None:
    """Fail closed on altered or self-contradictory report, without trusting SHA as provenance."""
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise DashboardRefused("Unrecognized synthetic report")
    digest = report.get("public_report_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise DashboardRefused("Invalid report digest")
    try:
        base = {k: v for k, v in report.items() if k != "public_report_sha256"}
        data = json.dumps(base, ensure_ascii=False, sort_keys=True, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise DashboardRefused("Unserializable report") from exc
    if hashlib.sha256(data).hexdigest() != digest:
        raise DashboardRefused("Changed report digest")
    if (report.get("source") != "UNTRUSTED_OPERATOR_NORMALIZED_LOCAL_ONLY"
            or report.get("status") not in OVERALL_STATES
            or report.get("release_gate") != "HOLD"
            or report.get("checksum_kind") != "UNSIGNED_LOCAL_INTEGRITY_ONLY_NOT_PROVENANCE"):
        raise DashboardRefused("Unexpected or unsafe evidence state")
    for name in ("file_agent_live_verified", "document_agent_live_verified", "real_nas_verified",
                 "overall_ready_certified", "sovia_integrated", "dbvora_integrated",
                 "devpost_submitted", "contains_raw_paths_references_questions_or_answers"):
        if report.get(name) is not False:
            raise DashboardRefused("Unverified external capability claim")
    file_stage = report.get("file_stage")
    doc_stage = report.get("document_stage")
    if not isinstance(file_stage, dict) or not isinstance(doc_stage, dict):
        raise DashboardRefused("Missing report stages")
    items, counts = file_stage.get("items"), file_stage.get("counts")
    if (not isinstance(items, list) or len(items) > 100
            or not isinstance(counts, dict) or set(counts) != set(STATE_ORDER)
            or type(file_stage.get("item_count")) is not int
            or file_stage["item_count"] != len(items)
            or file_stage.get("official_registered_file_agent_invoked") is not False):
        raise DashboardRefused("Invalid file stage")
    actual = {state: 0 for state in STATE_ORDER}
    for index, row in enumerate(items, 1):
        if (not isinstance(row, dict) or set(row) != {"requirement_index", "unverified_state"}
                or type(row["requirement_index"]) is not int
                or row["requirement_index"] != index
                or not isinstance(row["unverified_state"], str)
                or row["unverified_state"] not in STATE_ORDER):
            raise DashboardRefused("Invalid or identifying file data")
        actual[row["unverified_state"]] += 1
    if any(type(counts[key]) is not int or counts[key] != actual[key] for key in STATE_ORDER):
        raise DashboardRefused("Contradictory file counts")
    if (doc_stage.get("status") not in DOC_STATES
            or type(doc_stage.get("selected_count")) is not int
            or type(doc_stage.get("claimed_answer_count")) is not int
            or not 0 <= doc_stage["claimed_answer_count"] <= doc_stage["selected_count"] <= 10
            or doc_stage.get("actual_document_agent_invoked") is not False):
        raise DashboardRefused("Invalid document stage")
    if doc_stage["status"] == "NOT_REQUESTED" and (
            doc_stage["selected_count"] != 0 or doc_stage["claimed_answer_count"] != 0):
        raise DashboardRefused("Unexpected document result")
    if report["status"] == "SYNTHETIC_NEEDS_REVIEW" and counts["MISSING"] > 0:
        raise DashboardRefused("Blocked file cannot be marked non-blocked")
    if "trace" not in report or not isinstance(report["trace"], list):
        raise DashboardRefused("Missing audit trace")
    trace = report["trace"]
    expected_stages = ("file_agent", "separate_document_consent", "document_agent", "owner_review")
    if len(trace) != 4 or any(not isinstance(x, dict) or x.get("stage") != stage
                             or not isinstance(x.get("state"), str)
                             for x, stage in zip(trace, expected_stages)):
        raise DashboardRefused("Invalid audit trace")
    if trace[2]["state"] != doc_stage["status"] or trace[3]["state"] != report["status"]:
        raise DashboardRefused("Trace and verdict conflict")


def _pill(status: str) -> str:
    safe = escape(status, quote=True)
    tone = ("danger" if "BLOCKED" in status or status == "MISSING"
            else "amber" if "WAITING" in status or "REVIEW" in status
            else "mint" if status == "PRESENT" else "neutral")
    return f'<span class="pill {tone}">{safe}</span>'


def render_owner_review(report: dict) -> str:
    verify_public_report(report)
    counts = report["file_stage"]["counts"]
    docs = report["document_stage"]
    rows = report["file_stage"]["items"]
    stages = [
        ("01", "File inventory", "Scoped metadata claim", "UNTRUSTED CLAIM"),
        ("02", "Separate consent", "Per-reference content permission", report["trace"][1]["state"]),
        ("03", "Document review", "Synthetic response validation", docs["status"]),
        ("04", "Owner decision", "Evidence without optimistic READY", report["status"]),
    ]
    stage_html = "".join(
        '<article class="stage"><span class="step-num">'+number+'</span><div><h3>'+escape(title)+'</h3>'
        '<p>'+escape(description)+'</p><small>'+escape(state)+'</small></div></article>'
        for number, title, description, state in stages
    )
    cards = [
        ("Total files", len(rows), "Approved checklist entries"),
        ("Present claim", counts["PRESENT"], "Not independently verified"),
        ("Missing claim", counts["MISSING"], "Only on claimed complete inventory"),
        ("Not checked", counts["NOT_CHECKED"]+counts["VERSION_REVIEW"],
         "Includes version conflicts requiring review"),
    ]
    card_html = "".join(
        f'<article class="metric"><small>{escape(name)}</small>'
        f'<strong>{number}</strong><p>{escape(desc)}</p></article>'
        for name, number, desc in cards
    )
    table_rows = "".join(
        f'<tr><td class="idx">{row["requirement_index"]:03d}</td><td>{_pill(row["unverified_state"])}</td>'
        '<td>Operator-normalized claim only</td></tr>'
        for row in rows
    ) or '<tr><td colspan="3">No reviewed items</td></tr>'
    actual = report["status"]
    digest = report["public_report_sha256"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer"><title>FlowPilot 3.0 | Owner Review</title>
<style>
:root{{color-scheme:dark;font-family:Inter,Segoe UI,system-ui,sans-serif;background:#081322;color:#eef6ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 24% 0%,#1b3654 0%,#081322 48%);min-height:100vh}}
main{{max-width:1450px;margin:auto;padding:38px clamp(16px,3vw,50px) 60px}}
header{{display:flex;justify-content:space-between;align-items:center;gap:28px;flex-wrap:wrap}}
.eyebrow{{font-size:11px;font-weight:800;color:#61cffa;letter-spacing:.16em}}
h1{{font-size:clamp(27px,3vw,40px);letter-spacing:-.035em;margin:9px 0}}
.subtitle{{color:#9fb5c9;font-size:14px;line-height:1.7;max-width:770px}}
h2{{font-size:17px;font-weight:740;margin:32px 0 15px}}
.panel{{background:#11263b;border:1px solid #31516c;border-radius:16px;padding:22px}}
.hero{{display:flex;justify-content:space-between;gap:18px;align-items:center;flex-wrap:wrap}}
.hero h2{{margin:0 0 12px}}.hero p{{color:#9fb5c9;margin:0;line-height:1.5}}
.pill{{display:inline-block;font-size:11px;padding:7px 11px;border:1px solid #48687e;border-radius:100px;
max-width:100%;overflow-wrap:anywhere;font-weight:750}}
.pill.amber{{color:#ffcf80;background:#382b21;border-color:#705536}}.pill.danger{{color:#ffadbb;background:#3b2633;border-color:#82445b}}
.pill.mint{{color:#85edc9;background:#153e39;border-color:#267568}}.pill.neutral{{color:#b3c5d8;background:#1d3046}}
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}
.metric{{background:#11263b;border:1px solid #31516c;border-radius:14px;padding:21px}}
.metric small{{color:#9fb5c9;font-size:12px}}.metric strong{{display:block;font-size:40px;margin-top:10px;letter-spacing:-.04em}}
.metric p{{color:#819ab2;font-size:12px;line-height:1.5;margin-bottom:0}}
.stages{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px}}
.stage{{background:#0d2236;border:1px solid #2d4b63;border-radius:14px;padding:17px;display:flex;gap:13px}}
.step-num{{color:#4bc9fa;font-weight:850;font-size:16px}}h3{{font-size:14px;margin:0 0 8px}}
.stage p{{font-size:12px;color:#a1b4c8;line-height:1.5;min-height:40px}}
.stage small{{color:#ffca7e;font-size:10px;overflow-wrap:anywhere}}
.content{{display:grid;grid-template-columns:1.3fr 1fr;gap:14px}}
.table-scroll{{overflow:auto}}table{{width:100%;border-collapse:collapse;text-align:left;font-size:12px}}
th,td{{padding:12px;border-bottom:1px solid #29445c;color:#aabbcc}}th{{color:#daeafa}}
.idx{{color:#6bd3ff;font-variant-numeric:tabular-nums;font-weight:650}}
.info-grid{{display:grid;gap:14px}}.info-grid p{{font-size:12px;color:#9db3c9;line-height:1.65}}
.value{{font-size:23px;font-weight:740;color:#eef6ff}}.hash{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#a5d9eb;overflow-wrap:anywhere;font-size:11px}}
footer{{padding-top:26px;font-size:12px;color:#8299ae;line-height:1.7}}
@media(max-width:1100px){{.metrics,.stages{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:700px){{.metrics,.stages,.content{{grid-template-columns:1fr}}.metric strong{{font-size:32px}}}}
</style></head><body><main>
<header><div><div class="eyebrow">NAS FLOWPILOT 3.0 · COMMAND CENTER · OFFLINE REVIEW</div>
<h1>Owner Review &amp; Audit Trail</h1>
<p class="subtitle">A private-by-design view of synthetic / operator-normalized evidence. No actual Uliya, NAS, Lightning Azent, SOVIA or DBVORA execution is claimed.</p>
</div><div>{_pill("LOCAL ONLY · UNVERIFIED")}</div></header>
<section class="panel hero" aria-label="Owner review status"><div><h2>Review verdict</h2><p>Owner decision required · never a production READY certificate</p></div>{_pill(actual)}</section>
<section><h2>Evidence scorecard</h2><div class="metrics">{card_html}</div></section>
<section><h2>Consent-gated 4-stage flow</h2><div class="stages">{stage_html}</div></section>
<section class="content"><article class="panel"><h2>Requirement evidence (redacted)</h2>
<div class="table-scroll"><table><thead><tr><th>Index</th><th>Claimed state</th><th>Proof boundary</th></tr></thead>
<tbody>{table_rows}</tbody></table></div></article>
<div class="info-grid"><article class="panel"><h2>Document review</h2>
<p>Stage status</p>{_pill(docs["status"])}
<p>Selected documents: <span class="value">{docs["selected_count"]}</span></p>
<p>Unverified answer claims: <span class="value">{docs["claimed_answer_count"]}</span></p>
<p>All content remains outside this HTML export.</p></article>
<article class="panel"><h2>Audit integrity</h2><p>Report checksum (SHA-256)</p><div class="hash">{digest}</div>
<p>Checksum checked against local report bytes. Not a signature or platform provenance.</p>
{_pill("RELEASE HOLD · NOT SUBMITTED")}</article></div></section>
<footer>Offline owner-review artifact · file paths, document references, prompts and answer text are not embedded. Original evidence must be separately verified in the authorized NAS runtime. Generated from a bounded local JSON report, with no remote resources or scripts.</footer>
</main></body></html>'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline redacted review dashboard. NOT NAS or Devpost.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        source, output = args.input, args.output
        if (source.is_symlink() or source.parent.is_symlink() or not source.is_file()
                or not 0 < source.stat().st_size <= MAX_JSON_BYTES):
            raise DashboardRefused("Invalid source file")
        if output.is_symlink() or output.parent.is_symlink() or output.resolve() == source.resolve():
            raise DashboardRefused("Unsafe output file")
        raw = json.loads(source.read_text(encoding="utf-8"))
        html = render_owner_review(raw)
        with output.open("x", encoding="utf-8") as sink:
            sink.write(html)
        print(json.dumps({"status": "LOCAL_REDACTED_DASHBOARD_CREATED_NOT_NAS",
                          "bytes": output.stat().st_size, "report_sha256": raw["public_report_sha256"]}))
        return 0
    except (DashboardRefused, OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"status": "OWNER_REVIEW_DASHBOARD_REFUSED", "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
