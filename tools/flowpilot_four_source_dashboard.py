"""Static local-only four-source FlowPilot evidence view. Never executes sources/NAS."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

MAX_INPUT_BYTES = 32768


class EvidenceViewRefused(ValueError):
    """Do not echo any JSON values or local file paths on failure."""


def _count(data: dict, key: str, minimum: int, maximum: int) -> int:
    value = data.get(key)
    if type(value) is not int or not minimum <= value <= maximum:
        raise EvidenceViewRefused("INVALID_EVIDENCE_COUNTER")
    return value


def render_proof(result: dict) -> str:
    """Only display verified-shape counters; never interpolate untrusted fields."""
    if type(result) is not dict:
        raise EvidenceViewRefused("INVALID_EVIDENCE_SHAPE")
    state = result.get("status")
    if state == "PASS":
        n = _count(result, "intent_count", 1, 3)
        rows = _count(result, "la_write_rows", n, n)
        columns = _count(result, "dbvora_column_count", 1, 500)
        tables = _count(result, "dbvora_table_count", 1, 1000)
        trusted = (
            result.get("scope") == "DISPOSABLE_SYNTHETIC_LOCAL_ONLY"
            and result.get("actual_private_hae_la_invoked") is True
            and result.get("actual_public_sovia_invoked") is True
            and result.get("actual_private_dbvora_invoked") is True
            and result.get("la_replay_duplicates") == 0
            and result.get("approval_receipts") == 1
            and result.get("temporary_fixture_deleted") is True
            and result.get("actual_nas_verified") is False
            and result.get("registered_uliya_expert_invoked") is False
            and result.get("release_gate") == "HOLD"
        )
        if not trusted:
            raise EvidenceViewRefused("UNCERTIFIED_SOURCE_OR_RELEASE_CLAIM")
        headline = "Operator-reported synthetic integration PASS"
        subtitle = "Four-source local self-report; not independently attested by this viewer"
        stages = [
            ("01", "FlowPilot", f"{n} bounded intents"),
            ("02", "HAE / Lightning Azent", f"{rows} synthetic writes · replay 0"),
            ("03", "SOVIA", "Public assessor invoked (operator report)"),
            ("04", "DBVORA", f"{tables} synthetic SQLite tables · {columns} columns"),
            ("05", "NAS / Uliya", "NOT VERIFIED · no external calls"),
        ]
    elif state == "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL":
        n = _count(result, "scenario_count", 1, 3)
        _count(result, "synthetic_write_rows", 0, 0)
        if (result.get("dbvora_private_source_invoked_locally") is not False
                or result.get("nas_verified") is not False
                or result.get("release_gate") != "HOLD"):
            raise EvidenceViewRefused("UNSAFE_PREVIEW_CLAIM")
        headline = "Synthetic preview · explicit write approval required"
        subtitle = "No private DBVORA execution or synthetic write is certified"
        stages = [
            ("01", "FlowPilot", f"{n} bounded intents preview"),
            ("02", "HAE / Lightning Azent", "Write NOT EXECUTED"),
            ("03", "SOVIA", "Read-only synthetic preview only"),
            ("04", "DBVORA", "NOT INVOKED"),
            ("05", "NAS / Uliya", "NOT VERIFIED"),
        ]
    else:
        raise EvidenceViewRefused("UNKNOWN_EVIDENCE_STATUS")

    pipeline = "".join(
        '<article class="step"><span>' + escape(num) + '</span><h2>' +
        escape(title) + '</h2><p>' + escape(detail) + '</p></article>'
        for num, title, detail in stages
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FlowPilot 3.0 · Synthetic Local Evidence</title>
<style>
:root{{color-scheme:dark;font:14px system-ui,Segoe UI,sans-serif;background:#071522;color:#edf5ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(at top left,#123753,#071522 66%)}}
main{{max-width:1260px;margin:auto;padding:48px 22px}}
small{{color:#58d2ef;letter-spacing:.13em;font-weight:800}}h1{{font-size:clamp(28px,4vw,48px);margin:10px 0}}
.lead{{color:#aec4d7;max-width:760px;line-height:1.65}}.label{{display:inline-block;border:1px solid #5f8aa3;
border-radius:99px;padding:9px 14px;color:#ffcc85;margin-top:16px}}
.grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:38px 0}}
.step{{background:#11273c;border:1px solid #28516b;border-radius:15px;padding:23px;min-height:205px}}
.step span{{color:#63d8ff;font-weight:800;font-size:12px}}h2{{font-size:18px;margin:17px 0}}
.step p{{color:#b5c6d6;line-height:1.6}}footer{{margin-top:32px;padding-top:20px;border-top:1px solid #31506b;
color:#95b5cf;line-height:1.7}}@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><small>UGREEN NAS HACKATHON · OFFLINE DEVELOPMENT EVIDENCE</small>
<h1>NAS FlowPilot 3.0</h1><p class="lead">{escape(headline)}</p>
<p class="lead">{escape(subtitle)}</p><div class="label">RELEASE HOLD · NAS / ULIYA UNVERIFIED</div>
<section class="grid" aria-label="Five stage pipeline">{pipeline}</section>
<footer>No user/NAS/customer content was taken from the input JSON. This static display
is not a vendor integration test, audit signature, public CI result, submission,
or proof of installed NAS permissions. A PASS can be asserted only from a
separate exact-SHA source-pinned local execution log.</footer></main></body></html>"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create static local-only proof HTML")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if (args.input.is_symlink() or not args.input.is_file()
                or not 0 < args.input.stat().st_size <= MAX_INPUT_BYTES
                or args.output.is_symlink() or args.output.exists()):
            raise EvidenceViewRefused("UNSAFE_EVIDENCE_INPUT_OR_OUTPUT")
        proof = json.loads(args.input.read_text(encoding="utf-8"))
        html = render_proof(proof)
        with args.output.open("x", encoding="utf-8") as fh:
            fh.write(html)
    except (EvidenceViewRefused, ValueError, OSError, UnicodeError):
        print(json.dumps({"status": "FOUR_SOURCE_DASHBOARD_REFUSED"}))
        return 2
    print(json.dumps({"status": "SYNTHETIC_DASHBOARD_CREATED_NOT_NAS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
