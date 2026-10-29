"""Owner-local, pinned real-HAA/LA + SOVIA bounded goal synthetic proof.

This opt-in command does NOT use actual UGREEN NAS or registered Uliya agents.
Without --approve-plan-sha256 it creates no database. To execute, copy the
SHA from an earlier preview using the exact same goal and required file slots.
Only fixed NOT_CHECKED synthetic intent markers reach local disposable SQLite.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integrations.bounded_goal_runtime import run_bounded_compiled_goal
from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused, verify_checkout,
)


def parse_candidates(items: list[str]) -> dict[str, list[str]] | None:
    if not items:
        return None
    if len(items) > 100:
        raise ValueError("CANDIDATE_COUNT_EXCEEDED")
    grouped: dict[str, list[str]] = {}
    for item in items:
        if type(item) is not str or item.count("=") != 1:
            raise ValueError("INVALID_CANDIDATE_FORMAT")
        source, alternative = item.split("=", 1)
        grouped.setdefault(source, []).append(alternative)
    return grouped


def verify(
    hae_root: Path, sovia_root: Path, goal: str, required: list[str],
    *, candidates: dict[str, list[str]] | None = None,
    approve_plan_sha256: str | None = None,
) -> dict:
    hae = verify_checkout(hae_root, EXPECTED_HAE_SHA, ("packages/lightning-azent",))
    sovia = verify_checkout(sovia_root, EXPECTED_SOVIA_SHA,
                            ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"))
    package = hae / "packages" / "lightning-azent"
    if not (package / "lightning_azent" / "runtime.py").is_file():
        raise ProofRefused("PINNED_LA_SOURCE_NOT_FOUND")
    if not (sovia / "sovia_la_plan_preflight.py").is_file():
        raise ProofRefused("PINNED_SOVIA_SOURCE_NOT_FOUND")
    sys.path.insert(0, str(package))
    sys.path.insert(0, str(sovia))
    from lightning_azent import LAExecutor
    from sovia_la_plan_preflight import assess
    result = run_bounded_compiled_goal(
        goal, LAExecutor, assess, required=required, candidates=candidates,
        approve_plan_sha256=approve_plan_sha256,
    )
    return {
        **result,
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "pinned_source_check": "PASS",
        "independently_replayed_in_public_ci": False,
        "real_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Pinned LA/SOVIA multi-goal preflight and opt-in disposable SQLite proof (NOT NAS)",
    )
    parser.add_argument("--hae-root", type=Path, required=True)
    parser.add_argument("--sovia-root", type=Path, required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--required", action="append", required=True)
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument(
        "--approve-plan-sha256",
        help="Exact 64-char approval SHA from a preview of the SAME goal and paths",
    )
    args = parser.parse_args(argv)
    try:
        result = verify(
            args.hae_root, args.sovia_root, args.goal, args.required,
            candidates=parse_candidates(args.candidate),
            approve_plan_sha256=args.approve_plan_sha256,
        )
    except (OSError, ValueError, TypeError, RuntimeError,
            ImportError, KeyError, sqlite3.Error) as exc:
        code = str(exc) if isinstance(exc, ProofRefused) else "BOUNDED_GOAL_LOCAL_PROOF_REFUSED"
        print(json.dumps({
            "status": "FAIL", "reason_code": code,
            "actual_nas_verified": False, "release_gate": "HOLD",
        }), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
