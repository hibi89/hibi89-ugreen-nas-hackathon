"""Opt-in real HAE+SOVIA contiguous synthetic local E2E verifier.

Requires the same pinned, clean local checkouts as the previously owner-run
synthetic proof. Default is PREVIEW ONLY. The only write mode requires
--approve-synthetic-write and targets a disposable tempfile SQLite database.
Never reads customer folders or attempts NAS/Uliya activation.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from integrations.goal_la_sovia_runtime import run_connected_synthetic
from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused, verify_checkout,
)


def verify_connected(hae_root: Path, sovia_root: Path, *, approve: bool = False) -> dict:
    hae = verify_checkout(hae_root, EXPECTED_HAE_SHA, ("packages/lightning-azent",))
    sovia = verify_checkout(
        sovia_root, EXPECTED_SOVIA_SHA,
        ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"),
    )
    la_package = hae / "packages" / "lightning-azent"
    if not (la_package / "lightning_azent" / "runtime.py").is_file():
        raise ProofRefused("HAE_LA_SOURCE_UNAVAILABLE")
    if not (sovia / "sovia_la_plan_preflight.py").is_file():
        raise ProofRefused("SOVIA_SOURCE_UNAVAILABLE")
    sys.path.insert(0, str(la_package))
    sys.path.insert(0, str(sovia))
    from lightning_azent import LAExecutor
    from sovia_la_plan_preflight import assess

    proof = run_connected_synthetic(
        LAExecutor, assess, approve_synthetic_write=approve,
    )
    return {
        **proof,
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "pinned_source_check": "PASS",
        "independent_public_ci_real_hae_execution": False,
        "ephemeral_sqlite_deleted_after_run": True,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Pinned real HAE+SOVIA local synthetic connected E2E")
    parser.add_argument("--hae-root", required=True, type=Path)
    parser.add_argument("--sovia-root", required=True, type=Path)
    parser.add_argument(
        "--approve-synthetic-write", action="store_true",
        help="Explicitly authorize one disposable synthetic SQLite write and replay",
    )
    args = parser.parse_args(argv)
    try:
        result = verify_connected(
            args.hae_root, args.sovia_root, approve=args.approve_synthetic_write
        )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0 if (result["status"] == "PASS"
                     or result["status"] == "WAITING_EXPLICIT_SYNTHETIC_WRITE_APPROVAL") else 1
    except (OSError, RuntimeError, ValueError, TypeError, ImportError, sqlite3.Error) as exc:
        code = str(exc) if isinstance(exc, ProofRefused) else "SYNTHETIC_CONNECTED_CHAIN_FAILED"
        print(json.dumps({
            "status": "FAIL", "reason_code": code,
            "actual_nas_verified": False, "release_gate": "HOLD",
        }, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
