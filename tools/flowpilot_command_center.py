"""Static offline FlowPilot Command Center dashboard.

Shows only local prototype state. Not proof of official NAS/Uliya, LA/n8n,
SOVIA, DBVORA or Devpost integration. All dynamic text is HTML-escaped.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

MAX_JSON_BYTES = 1_000_000


def _t(value: object) -> str:
    return escape(str(value)[:160], quote=True)


def _status(payload: dict) -> tuple[str, str]:
    if payload.get("status") == "WAITING_USER":
        return "Missing inputs", "waiting"
    if payload.get("status") == "WAITING_EXECUTION_APPROVAL":
        return "Awaiting explicit approval", "waiting"
    if payload.get("status") == "DECLINED":
        return "Declined — nothing executed", "blocked"
    if payload.get("status") == "LOCAL_REPORT_CREATED_NOT_NAS" and payload.get("executed") is True:
        return "Local report created", "done"
    return "Not verified", "blocked"


def render_dashboard(payload: dict) -> str:
    if not isinstance(payload, dict):
        raise ValueError("E2E result must be a JSON object")
    status, state = _status(payload)
    request = payload.get("request") if isinstance(payload.get("request"), dict) else {}
    graph = payload.get("workflow_graph") if isinstance(payload.get("workflow_graph"), dict) else {}
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    nodes = [n for n in nodes[:30] if isinstance(n, dict)]
    cards = [
        ("01", "Natural Language Request", "Bounded Korean / English intent"),
        ("02", "HAE-style Dialogue", "Missing-slot prompts — local adapter only"),
        ("03", "Workflow & User Approval", "Review graph, then explicitly approve or reject"),
        ("04", "CSV Execution & Report", "Decimal aggregation, new output file"),
        ("05", "SQLite Audit", "Local run trace; NOT SOVIA integration"),
    ]
    pipeline = "".join(
        f'<article class="step"><small>{no}</small><h3>{_t(name)}</h3><p>{_t(desc)}</p></article>'
        for no, name, desc in cards
    )
    graph_html = "".join(
        '<li><span class="node-type">' + _t(node.get("type", "unknown")) +
        '</span><span>' + _t(node.get("label", "Unnamed node")) + '</span></li>'
        for node in nodes
    ) or "<li>Workflow unavailable until required slots are supplied.</li>"
    missing = request.get("missing_inputs") if isinstance(request.get("missing_inputs"), list) else []
    missing_text = ", ".join(_t(x) for x in missing[:20]) or "None"
    execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
    result = execution.get("result") if isinstance(execution.get("result"), dict) else {}
    report = result.get("result") if isinstance(result.get("result"), dict) else result
    output = _t(report.get("output", "Not produced"))
    packages = [
        ("Skill ZIP", "Official compatible Skill package verification pending"),
        ("English Summary PDF", "Up to 500 words · at most 1 MB"),
        ("Demo Video", "Round 1: not required; finalist Round 2: real NAS demo <=3 min"),
        ("Devpost", "Round 1: SKILL ZIP + English PDF; NOT SUBMITTED"),
    ]
    package_html = "".join(
        '<article class="artifact"><h3>' + _t(name) + '</h3><p>' + _t(desc) +
        '</p><b>NOT VERIFIED</b></article>' for name, desc in packages
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NAS FlowPilot 3.0 — Command Center</title>
<style>
:root{{color-scheme:dark;font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;background:#081322;color:#e9f3ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at top,#142e4b,#081322 64%);min-height:100vh}}
main{{max-width:1540px;margin:auto;padding:38px 28px 56px}}header{{display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap}}
h1{{font-size:clamp(28px,3vw,43px);margin:3px 0}}.eyebrow{{letter-spacing:.16em;color:#5dd7ff;font-size:12px;font-weight:800}}
.subtitle{{color:#9db2c9}}.pill{{border:1px solid #50768e;border-radius:28px;padding:11px 16px;color:#bbdcf0}}
section{{margin-top:32px}}h2{{font-size:18px;margin:0 0 15px;color:#e3f3ff}}.pipeline{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}}
.step,.panel,.artifact{{border:1px solid #24455d;background:#112339dd;border-radius:14px;padding:22px;box-shadow:0 10px 32px #0002}}
.step{{min-height:192px}}.step small{{display:block;color:#53d3ff;font-weight:800;margin-bottom:17px}}h3{{font-size:16px;margin:0 0 12px}}
p{{line-height:1.6;color:#9db3c7;font-size:13px}}.grid{{display:grid;grid-template-columns:1.3fr 1fr;gap:16px}}
.status{{font-weight:750;font-size:21px}}.waiting{{color:#f8c267}}.blocked{{color:#ff8c92}}.done{{color:#58e2b1}}
.node-list{{padding:0;list-style:none;display:grid;gap:9px}}.node-list li{{background:#081a2c;border:1px solid #24445c;padding:9px 12px;border-radius:8px;display:flex;gap:12px;align-items:center}}
.node-type{{font-size:11px;color:#6adeff;min-width:122px}}.artifact-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}
.artifact b{{font-size:10px;color:#f6c170}}footer{{margin-top:25px;color:#718ba6;font-size:12px}}
@media(max-width:1080px){{.pipeline,.artifact-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:650px){{main{{padding:22px 14px}}.pipeline,.grid,.artifact-grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><div class="eyebrow">UGREEN NAS AI HACKATHON · LOCAL PROTOTYPE</div>
<h1>NAS FlowPilot 3.0</h1><p class="subtitle">Natural Language to NAS Automation · Command Center</p></div>
<div class="pill">LOCAL ONLY · NAS UNVERIFIED</div></header>
<section><h2>E2E pipeline · target architecture</h2><div class="pipeline">{pipeline}</div></section>
<section class="grid"><article class="panel"><h2>Workflow preview</h2><ul class="node-list">{graph_html}</ul></article>
<article class="panel"><h2>Execution and approval</h2><div class="status {state}">{_t(status)}</div>
<p>Raw status: {_t(payload.get("status", "UNKNOWN"))}</p><p>Missing slots: {missing_text}</p>
<p>Report output: {output}</p><p>Explicit approval is required for local CSV writes.</p></article></section>
<section><h2>Final submission package · checklist</h2><div class="artifact-grid">{package_html}</div></section>
<footer>Static development visualization. Workflow graph is deterministic, not an actual LA/n8n graph.
No official NAS/Uliya runtime, SOVIA, DBVORA or Devpost completion is asserted.</footer>
</main></body></html>'''


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Offline dashboard from local E2E JSON")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        if (args.input.is_symlink() or not args.input.is_file() or
                not 0 < args.input.stat().st_size <= MAX_JSON_BYTES):
            raise ValueError("Invalid input")
        page = render_dashboard(json.loads(args.input.read_text(encoding="utf-8")))
        if args.output.is_symlink():
            raise ValueError("Output symlink refused")
        with args.output.open("x", encoding="utf-8") as out:
            out.write(page)
    except (ValueError, OSError, UnicodeError):
        print(json.dumps({"status": "DASHBOARD_REFUSED"}))
        return 2
    print(json.dumps({"status": "LOCAL_DASHBOARD_CREATED_NOT_NAS", "path": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
