"""One command: local disposable 1/2/3 intent verifier with sanitized evidence.

No NAS, Uliya, external connection or customer content. Even synthetic PASS
is only an owner-local report; it is not independently attested here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from tools.verify_four_source_synthetic import run_matrix, FourSourceProofRefused
from tools.flowpilot_four_source_dashboard import render_proof, EvidenceViewRefused

PASS_FIELDS = (
    "status", "scope", "intent_count", "la_write_rows", "la_replay_duplicates",
    "approval_receipts", "dbvora_table_count", "dbvora_column_count",
    "temporary_fixture_deleted", "actual_private_hae_la_invoked",
    "actual_public_sovia_invoked", "actual_private_dbvora_invoked",
    "actual_nas_verified", "registered_uliya_expert_invoked", "release_gate",
)
PREVIEW_FIELDS = (
    "status", "scenario_count", "synthetic_write_rows",
    "dbvora_private_source_invoked_locally", "nas_verified", "release_gate",
)


class ProofBundleRefused(ValueError):
    """Safe refusal that does not include local paths or raw source exceptions."""


def _new_output(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ProofBundleRefused("OUTPUT_MUST_BE_ABSOLUTE")
    if path.exists() or path.is_symlink():
        raise ProofBundleRefused("OUTPUT_ALREADY_EXISTS")
    parent = path.parent
    if not parent.is_dir() or any(p.is_symlink() for p in (parent, *parent.parents)):
        raise ProofBundleRefused("OUTPUT_PARENT_UNAVAILABLE")
    return path


def _sanitize(row: object, count: int, approved: bool) -> dict:
    if type(row) is not dict:
        raise ProofBundleRefused("INVALID_RESULT_TYPE")
    fields = PASS_FIELDS if approved else PREVIEW_FIELDS
    if any(key not in row for key in fields):
        raise ProofBundleRefused("MISSING_RESULT_EVIDENCE")
    safe = {key: row[key] for key in fields}
    if approved:
        correct = safe["status"] == "PASS" and safe["intent_count"] == count
    else:
        correct = (safe["status"] == "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL"
                   and safe["scenario_count"] == count)
    if not correct:
        raise ProofBundleRefused("INCORRECT_SCENARIO_EVIDENCE")
    try:
        render_proof(safe)
    except (EvidenceViewRefused, TypeError, ValueError):
        raise ProofBundleRefused("UNVERIFIED_SYNTHETIC_EVIDENCE") from None
    return safe


def _encode(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _index(rows: list[dict]) -> bytes:
    cards = "".join(
        '<a class="card" href="proof-' + str(n) + '.html"><small>SCENARIO ' +
        str(n) + '</small><h2>' + str(n) + ' bounded intents</h2><p>' +
        ('Synthetic execution self-reported PASS' if r["status"] == "PASS"
         else 'Approval preview — no writes') +
        '</p><strong>Open redacted evidence</strong></a>'
        for n, r in enumerate(rows, 1)
    )
    return ("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FlowPilot 3.0 — Local Synthetic Proof Matrix</title><style>
:root{font:15px system-ui,Segoe UI,sans-serif;color:#edf5ff;background:#091622}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(at top,#173653,#091622 62%)}
main{max-width:1200px;margin:auto;padding:48px 24px}
small{color:#66d9fa;letter-spacing:.1em;font-weight:800}
h1{font-size:clamp(30px,4vw,52px)}p{color:#b3c6d8;line-height:1.65}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:34px}
.card{display:block;text-decoration:none;color:#edf5ff;border:1px solid #335472;
background:#14293e;border-radius:16px;padding:25px;min-height:210px}
.card strong{color:#9cf1ce}.card h2{font-size:22px}
footer{border-top:1px solid #38546a;margin-top:36px;padding-top:18px;color:#a9bfd2}
@media(max-width:850px){.grid{grid-template-columns:1fr}}
</style></head><body><main><small>UGREEN · OFFLINE SYNTHETIC ONLY</small>
<h1>NAS FlowPilot 3.0</h1><p>One-, two- and three-intent local
workflow results. Never proof of actual NAS or Uliya Expert execution.</p>
<section class="grid">""" + cards + """</section>
<footer>RELEASE HOLD · No customer data · No vendor authorization ·
No Creator or Devpost submission. Refer to manifest.json for hashes.</footer>
</main></body></html>""").encode("utf-8")


def _bundle(target: Path, rows: list[dict]) -> None:
    stage = Path(tempfile.mkdtemp(prefix=".ugreen-synthetic-proof-",
                                  dir=str(target.parent)))
    try:
        files: dict[str, bytes] = {}
        for n, row in enumerate(rows, 1):
            files[f"proof-{n}.json"] = _encode(row)
            files[f"proof-{n}.html"] = render_proof(row).encode("utf-8")
        files["index.html"] = _index(rows)
        for name, data in files.items():
            with (stage / name).open("xb") as f:
                f.write(data)
        manifest = {
            "kind": "ugreen-four-source-synthetic-bundle.v1",
            "claim": ("OPERATOR_REPORTED_SYNTHETIC_PASS_NOT_NAS"
                      if rows[0]["status"] == "PASS"
                      else "APPROVAL_PREVIEW_NO_WRITES"),
            "file_sha256": {name: hashlib.sha256(data).hexdigest()
                            for name, data in sorted(files.items())},
            "actual_nas_verified": False,
            "registered_uliya_expert_invoked": False,
            "official_creator_verified": False,
            "release_gate": "HOLD",
        }
        with (stage / "manifest.json").open("xb") as f:
            f.write(_encode(manifest))
        if target.exists() or target.is_symlink():
            raise ProofBundleRefused("OUTPUT_BECAME_OCCUPIED")
        os.rename(stage, target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def run_suite(hae_root: Path, sovia_root: Path, dbvora_root: Path, *,
              approve_disposable_synthetic: bool = False,
              output_dir: Path | None = None) -> dict:
    if type(approve_disposable_synthetic) is not bool:
        raise ProofBundleRefused("INVALID_SYNTHETIC_APPROVAL")
    target = _new_output(output_dir) if output_dir is not None else None
    results = [
        _sanitize(run_matrix(
            hae_root, sovia_root, dbvora_root,
            approve_disposable_synthetic=approve_disposable_synthetic,
            intent_count=n,
        ), n, approve_disposable_synthetic)
        for n in (1, 2, 3)
    ]
    if target is not None:
        _bundle(target, results)
    return {
        "status": ("PASS_SYNTHETIC_LOCAL_ONLY" if approve_disposable_synthetic
                   else "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL"),
        "tested_intent_counts": [1, 2, 3],
        "scenario_count": 3,
        "evidence_bundle_created": target is not None,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="1-3 synthetic intent checks, no NAS")
    for root in ("hae", "sovia", "dbvora"):
        p.add_argument("--" + root + "-root", type=Path, required=True)
    p.add_argument("--approve-disposable-synthetic", action="store_true")
    p.add_argument("--output-dir", type=Path)
    a = p.parse_args(argv)
    try:
        report = run_suite(
            a.hae_root, a.sovia_root, a.dbvora_root,
            approve_disposable_synthetic=a.approve_disposable_synthetic,
            output_dir=a.output_dir,
        )
    except (ProofBundleRefused, FourSourceProofRefused,
            OSError, ValueError, TypeError, ImportError, RuntimeError,
            KeyError, sqlite3.Error):
        print(json.dumps({"status": "FAIL", "reason_code": "FOUR_SOURCE_SUITE_REFUSED",
                          "actual_nas_verified": False, "release_gate": "HOLD"}),
              file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
