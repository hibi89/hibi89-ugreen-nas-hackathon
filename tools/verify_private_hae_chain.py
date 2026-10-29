"""Proof-gated, owner-local FlowPilot ↔ real HAE LA ↔ real SOVIA check.

Run from a trusted UGREEN checkout with separate, exact-source HAE and
SOVIA clones. Real external NAS/Uliya/customer-data access is NEVER involved.

Example:
  python tools/verify_private_hae_chain.py --hae-root ../HAE --sovia-root ../SOVIA_sovereign

Successful proof means: actual pinned LAExecutor executes synthetic SQLite
read/write/replay + redacted audit, and actual pinned SOVIA reviews an LA
plan preview. It does NOT prove NAS access or authorize any workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.flowpilot_ecosystem_showcase import showcase
from tools.verify_la_runtime_bridge import verify as verify_la

# Exact feature/develop HEAD identities independently verified via GitHub.
EXPECTED_HAE_SHA = "9cba6424dadf3fadb0ccd6ed10040e322c4a62fa"
EXPECTED_SOVIA_SHA = "7418b23aff9b3abbd3faf5d1477e7244ec82b681"


class ProofRefused(ValueError):
    """Cannot truthfully certify the requested source/evidence."""


def _git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProofRefused("LOCAL_GIT_UNAVAILABLE") from exc
    if completed.returncode != 0:
        raise ProofRefused("CHECKOUT_UNVERIFIED")
    return completed.stdout.strip()


def verify_checkout(
    root: Path, expected_sha: str, paths: tuple[str, ...]
) -> Path:
    """Accept an exact committed local checkout; never download its contents."""
    try:
        checked = Path(root).resolve(strict=True)
    except OSError as exc:
        raise ProofRefused("SOURCE_ROOT_MISSING") from exc
    if not checked.is_dir():
        raise ProofRefused("SOURCE_ROOT_NOT_DIRECTORY")
    if (len(expected_sha) != 40
            or any(char not in "0123456789abcdef" for char in expected_sha)):
        raise ProofRefused("EXPECTED_SOURCE_SHA_INVALID")
    if _git(checked, "rev-parse", "--show-toplevel") != str(checked):
        raise ProofRefused("SOURCE_ROOT_NOT_GIT_TOPLEVEL")
    if _git(checked, "rev-parse", "HEAD") != expected_sha:
        raise ProofRefused("SOURCE_SHA_MISMATCH")
    if _git(checked, "status", "--porcelain=v1", "--untracked-files=all",
            "--", *paths):
        raise ProofRefused("SOURCE_FILES_MODIFIED")
    return checked


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(hae_root: Path, sovia_root: Path) -> dict:
    """One direct, local proof with immutable, owner-selected source identity."""
    hae = verify_checkout(
        hae_root, EXPECTED_HAE_SHA, ("packages/lightning-azent",)
    )
    sovia = verify_checkout(
        sovia_root, EXPECTED_SOVIA_SHA,
        ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"),
    )
    la_package = hae / "packages" / "lightning-azent"
    la_code = la_package / "lightning_azent" / "runtime.py"
    sovia_code = sovia / "sovia_la_plan_preflight.py"
    if not la_code.is_file() or not sovia_code.is_file():
        raise ProofRefused("PINNED_SOURCE_FILE_MISSING")
    if any(x.is_symlink() for x in (la_code, sovia_code)):
        raise ProofRefused("PINNED_SOURCE_FILE_SYMLINK")

    # The only imports from HAE/SOVIA happen after source identity checks.
    sys.path.insert(0, str(la_package))
    sys.path.insert(0, str(sovia))
    from lightning_azent import LAExecutor
    from sovia_la_plan_preflight import assess

    # Real LA, disposable local SQLite, approved synthetic write and replay.
    la_proof = verify_la(la_package)
    if (la_proof.get("result") != "PASS"
            or la_proof.get("approved_synthetic_write_rows") != 1
            or la_proof.get("replay_duplicate_writes") != 0
            or la_proof.get("denied_write_created_db") is not False):
        raise ProofRefused("REAL_LA_SYNTHETIC_EXECUTION_NOT_PROVEN")

    results = {
        scenario: showcase(
            scenario, assess, la_api=LAExecutor, la_real_source=True
        )
        for scenario in ("read_only", "write_review", "missing_input", "declined")
    }
    if (results["read_only"].get("advisory_finding_count") != 0
            or results["write_review"].get("advisory_finding_count") != 1
            or results["write_review"].get("sovia") != "ADVISORY_ONLY"
            or results["missing_input"].get("la") != "NOT_CHECKED"
            or results["declined"].get("la") != "NOT_CHECKED"):
        raise ProofRefused("REAL_SOVIA_PREVIEW_REVIEW_NOT_PROVEN")
    if any(
        row.get("actual_nas_verified") is not False
        or row.get("registered_uliya_expert_invoked") is not False
        or row.get("la_workflow_executed") is not False
        or row.get("release_gate") != "HOLD"
        for row in results.values()
    ):
        raise ProofRefused("PROOF_SCOPE_ESCALATION")

    # Never print raw step IDs, private-source content or local checkout paths.
    return {
        "result": "PASS",
        "proof_type": "REAL_HAE_LA_AND_SOVIA_SYNTHETIC_LOCAL_ONLY",
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "la_runtime_sha256": _sha256(la_code),
        "sovia_preflight_sha256": _sha256(sovia_code),
        "real_la_synthetic_sqlite": "PASS",
        "real_la_approved_write_rows": la_proof["approved_synthetic_write_rows"],
        "real_la_replay_duplicate_writes": 0,
        "real_la_approval_receipts": la_proof["approval_receipts"],
        "real_sovia_advisory": "PASS",
        "scenario_count": len(results),
        "write_advisory_findings": results["write_review"]["advisory_finding_count"],
        "customer_data_used": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Exact-source, owner-local HAE LA + SOVIA synthetic proof"
    )
    parser.add_argument("--hae-root", type=Path, required=True)
    parser.add_argument("--sovia-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        proof = run(args.hae_root, args.sovia_root)
    except (OSError, ValueError, RuntimeError, ImportError, TypeError, KeyError) as exc:
        # Never expose local paths, dynamic error text, customer data or source.
        print(json.dumps({
            "result": "FAIL",
            "reason_code": str(exc) if isinstance(exc, ProofRefused)
                           else "LOCAL_SYNTHETIC_PROOF_FAILED",
            "real_la_synthetic_sqlite": "NOT_PROVEN",
            "actual_nas_verified": False,
            "release_gate": "HOLD",
        }), file=sys.stderr)
        return 1
    print(json.dumps(proof, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
