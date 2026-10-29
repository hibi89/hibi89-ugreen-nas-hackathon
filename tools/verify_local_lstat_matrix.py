"""One-command owner-local synthetic lstat -> pinned LA/SOVIA scenario matrix.

No user root argument. Every file is created by this script inside its own
disposable temporary directory; no customer data, NAS or Uliya is read.

Default mode previews *only*, without SQLite writes. A separate explicit
--approve-synthetic-writes flag permits disposable local SQLite write/replay
for a bounded, preflighted two-intent fixture. The exact approval SHA comes
from the immediately preceding in-process preview over the same synthetic
scope, never from untrusted user data. All output is sanitized counters.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from integrations.local_metadata_la_chain import (
    LocalObservationRefused, run_local_observation_chain,
)
from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused, verify_checkout,
)

SYNTHETIC_GOAL = "파일 누락 확인 그리고 인계 확인"
REQUIRED = ["README.md"]


class MatrixRefused(ValueError):
    """The synthetic matrix failed one of the mandatory safety/receipt checks."""


def require(value: bool, code: str) -> None:
    if value is not True:
        raise MatrixRefused(code)


def run_matrix(
    la_executor_type: object,
    sovia_assess: object,
    *,
    approve_synthetic_writes: bool = False,
) -> dict[str, Any]:
    """Inspect six independent synthetic states, execute only when opted in."""
    if type(approve_synthetic_writes) is not bool:
        raise MatrixRefused("INVALID_SYNTHETIC_WRITE_CONSENT")
    if not callable(la_executor_type) or not callable(sovia_assess):
        raise MatrixRefused("MISSING_REAL_OR_INJECTED_ENGINES")
    with tempfile.TemporaryDirectory(prefix="ugreen-lstat-matrix-") as location:
        root = Path(location)
        (root / "README.md").write_bytes(b"UGREEN disposable synthetic metadata fixture")
        (root / "README_final.md").write_bytes(b"UGREEN competing synthetic version")
        def check(goal: str, required: list[str], *,
                  candidates: dict[str, list[str]] | None = None,
                  metadata: bool = False,
                  approved: str | None = None) -> dict[str, Any]:
            return run_local_observation_chain(
                goal, root, required, la_executor_type, sovia_assess,
                candidates=candidates,
                approve_local_metadata=metadata,
                approve_plan_sha256=approved,
            )

        # 1. No consent, no local metadata access.
        unapproved = check("파일 누락 확인", REQUIRED)
        require(
            unapproved["status"] == "WAITING_LOCAL_METADATA_APPROVAL"
            and unapproved["local_inspection_performed"] is False
            and unapproved["synthetic_write_rows"] == 0,
            "PREVIEW_EXCEEDED_LOCAL_CONSENT",
        )

        # 2. Actual local OS lstat sees one present file after explicit
        # synthetic metadata approval, no database until separate SHA consent.
        present = check("파일 누락 확인", REQUIRED, metadata=True)
        require(
            present["status"] == "WAITING_EXACT_LOCAL_PLAN_APPROVAL"
            and present["local_state_counts"]["PRESENT"] == 1
            and present["local_inspection_performed"] is True
            and present["synthetic_write_rows"] == 0,
            "PRESENT_LOCAL_LSTAT_NOT_PROVEN",
        )

        # 3. Absent filename is NOT a successful handoff; LA blocked.
        missing = check("파일 누락 확인", ["missing.csv"], metadata=True)
        require(
            missing["status"] == "BLOCKED_LOCAL_MISSING_OR_UNVERIFIED"
            and missing["local_state_counts"]["MISSING"] == 1
            and missing["synthetic_write_rows"] == 0,
            "MISSING_LOCAL_LSTAT_NOT_BLOCKED",
        )

        # 4. A competing existing candidate must force VERSION_REVIEW,
        # with no automatic final-version selection or file changes.
        candidates = {"README.md": ["README_final.md"]}
        collision = check("버전 비교", REQUIRED, candidates=candidates, metadata=True)
        require(
            collision["status"] == "WAITING_EXACT_LOCAL_PLAN_APPROVAL"
            and collision["local_state_counts"]["VERSION_REVIEW"] == 1
            and collision["release_gate"] == "HOLD",
            "VERSION_CONFLICT_NOT_REVIEWED",
        )

        # 5. Changing the observed version state invalidates the old approval
        # fingerprint, even if the proposed intent and file list are unchanged.
        (root / "README_final.md").unlink()
        stale_blocked = False
        try:
            check(
                "버전 비교", REQUIRED, candidates=candidates,
                metadata=True, approved=collision["approve_plan_sha256"],
            )
        except LocalObservationRefused as exc:
            stale_blocked = str(exc) == "LOCAL_PLAN_APPROVAL_HASH_MISMATCH"
        require(stale_blocked, "STALE_VERSION_APPROVAL_NOT_REJECTED")

        # 6. Genuine two-intent FlowPilot preview + injected LA preflight +
        # injected SOVIA review. Only an opt-in explicit write mode persists
        # sanitized counts to a separate disposable local SQLite database.
        multigoal = check(SYNTHETIC_GOAL, REQUIRED, metadata=True)
        require(
            multigoal["status"] == "WAITING_EXACT_LOCAL_PLAN_APPROVAL"
            and multigoal["intent_count"] == 2
            and multigoal["local_state_counts"]["PRESENT"] == 2
            and multigoal["sovia_finding_count"] == 2
            and multigoal["synthetic_write_rows"] == 0,
            "MULTI_INTENT_LOCAL_PREFLIGHT_NOT_PROVEN",
        )
        execution = None
        if approve_synthetic_writes:
            execution = check(
                SYNTHETIC_GOAL, REQUIRED, metadata=True,
                approved=multigoal["approve_plan_sha256"],
            )
            require(
                execution["status"] == "PASS"
                and execution["la_execution_verified"] is True
                and execution["synthetic_write_rows"] == 2
                and execution["approval_receipts"] == 1
                and execution["replay_duplicate_writes"] == 0
                and execution["ephemeral_sqlite_deleted_after_run"] is True,
                "EXPLICIT_SYNTHETIC_SQLITE_AUDIT_NOT_PROVEN",
            )

        return {
            "result": "PASS",
            "proof_type": "REAL_LOCAL_LSTAT_WITH_INJECTED_LA_SOVIA_SYNTHETIC_ONLY",
            "scenario_count": 6,
            "unapproved_preview": "PASS_NO_LOCAL_METADATA_ACCESS",
            "actual_local_present": "PASS",
            "actual_local_missing": "BLOCKED_AS_EXPECTED",
            "actual_local_version_conflict": "REVIEW_REQUIRED",
            "changed_observation_reused_approval": "REFUSED_AS_EXPECTED",
            "two_intent_local_preflight": "PASS",
            "synthetic_sqlite_execution": "PASS" if execution else "NOT_RUN_NO_WRITE_APPROVAL",
            "synthetic_write_rows": execution["synthetic_write_rows"] if execution else 0,
            "approval_receipts": execution["approval_receipts"] if execution else 0,
            "replay_duplicate_writes": execution["replay_duplicate_writes"] if execution else 0,
            "disposable_fixture_deleted_after_run": True,
            "file_contents_opened": False,
            "user_project_folders_accessed": False,
            "customer_data_used": False,
            "actual_nas_verified": False,
            "registered_uliya_expert_invoked": False,
            "devpost_submitted": False,
            "release_gate": "HOLD",
        }


def run_pinned(
    hae_root: Path, sovia_root: Path, *, approve_synthetic_writes: bool = False
) -> dict[str, Any]:
    hae = verify_checkout(hae_root, EXPECTED_HAE_SHA, ("packages/lightning-azent",))
    sovia = verify_checkout(
        sovia_root, EXPECTED_SOVIA_SHA,
        ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"),
    )
    package = hae / "packages" / "lightning-azent"
    if not (package / "lightning_azent" / "runtime.py").is_file():
        raise ProofRefused("PINNED_HAE_LA_SOURCE_MISSING")
    if not (sovia / "sovia_la_plan_preflight.py").is_file():
        raise ProofRefused("PINNED_SOVIA_ASSESSOR_MISSING")
    sys.path.insert(0, str(package))
    sys.path.insert(0, str(sovia))
    from lightning_azent import LAExecutor
    from sovia_la_plan_preflight import assess

    report = run_matrix(
        LAExecutor, assess, approve_synthetic_writes=approve_synthetic_writes,
    )
    return {
        **report,
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "pinned_source_check": "PASS",
        "actual_private_hae_executed": bool(approve_synthetic_writes),
        "actual_public_sovia_assessor_invoked": True,
        "independent_public_ci_real_hae_executed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Six-scenario disposable LOCAL lstat + pinned HAE/SOVIA matrix (NOT NAS)",
    )
    parser.add_argument("--hae-root", required=True, type=Path)
    parser.add_argument("--sovia-root", required=True, type=Path)
    parser.add_argument(
        "--approve-synthetic-writes", action="store_true",
        help="Explicitly consent only to disposable synthetic SQLite writes/replay",
    )
    args = parser.parse_args(argv)
    try:
        report = run_pinned(
            args.hae_root, args.sovia_root,
            approve_synthetic_writes=args.approve_synthetic_writes,
        )
    except (OSError, TypeError, ValueError, RuntimeError, ImportError,
            KeyError, sqlite3.Error) as exc:
        print(json.dumps({
            "result": "FAIL",
            "reason_code": str(exc) if isinstance(exc, (ProofRefused, MatrixRefused))
            else "LOCAL_SYNTHETIC_MATRIX_FAILED",
            "actual_nas_verified": False, "release_gate": "HOLD",
        }, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
