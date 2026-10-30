"""Owner-local four-source FlowPilot → LA → SOVIA → DBVORA synthetic matrix.

This script never touches owner files, NAS, Uliya or external services.
Default execution previews consent only; an explicit CLI flag allows an
isolated temporary fixture and disposable SQLite write for verification.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused,
)
from tools.verify_local_metadata_la_chain import EXPECTED_DBVORA_SHA, verify

GOALS = {
    1: "파일 누락 확인",
    2: "파일 누락 확인 그리고 인계 확인",
    3: "파일 누락 확인 그리고 인계 확인 그리고 버전 비교",
}
REQUIRED = ["README.md"]
REQUIRED_STATUS = "WAITING_EXACT_LOCAL_PLAN_APPROVAL"


def _pinned_source_claim_valid(row: dict, *, expect_dbvora: bool) -> bool:
    """Fail closed on stale/missing provenance before reporting real integration."""
    if type(row) is not dict:
        return False
    return (
        row.get("pinned_sources") == "PASS"
        and row.get("hae_la_commit") == EXPECTED_HAE_SHA
        and row.get("sovia_commit") == EXPECTED_SOVIA_SHA
        and row.get("dbvora_commit") == (
            EXPECTED_DBVORA_SHA if expect_dbvora else None
        )
        and row.get("dbvora_private_checkout_pinned") is expect_dbvora
        and row.get("dbvora_private_source_invoked_locally") is expect_dbvora
        and row.get("independent_public_ci_private_hae_executed") is False
    )


class FourSourceProofRefused(ValueError):
    """Safe machine-readable failure; never expose source paths."""


def run_matrix(hae_root: Path, sovia_root: Path, dbvora_root: Path, *,
               approve_disposable_synthetic: bool = False,
               intent_count: int = 2) -> dict:
    if type(approve_disposable_synthetic) is not bool:
        raise FourSourceProofRefused("INVALID_SYNTHETIC_APPROVAL")
    if type(intent_count) is not int or intent_count not in GOALS:
        raise FourSourceProofRefused("INVALID_INTENT_COUNT")
    goal = GOALS[intent_count]
    candidates = {"README.md": ["README_final.md"]} if intent_count == 3 else None
    # No caller-selected source folder, no NAS path or customer content.
    with tempfile.TemporaryDirectory(prefix="ugreen-4source-disposable-") as d:
        root = Path(d) / "input"
        root.mkdir(mode=0o700)
        (root / "README.md").write_text("synthetic fixture only\n", encoding="utf-8")
        if candidates:
            (root / "README_final.md").write_text(
                "synthetic competing version only\n", encoding="utf-8",
            )
        preview = verify(
            hae_root, sovia_root, goal, root, REQUIRED,
            candidates=candidates, metadata_consent=True,
        )
        if (preview.get("status") != REQUIRED_STATUS
                or type(preview.get("approve_plan_sha256")) is not str
                or len(preview["approve_plan_sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in preview["approve_plan_sha256"])
                or not _pinned_source_claim_valid(preview, expect_dbvora=False)
                or preview.get("local_inspection_performed") is not True
                or preview.get("sovia_advisory") != "REVIEW_ONLY"
                or preview.get("sovia_finding_count") != intent_count
                or preview.get("intent_count") != intent_count
                or preview.get("la_execution_verified") is not False
                or preview.get("dbvora_metadata_inspected") is not False
                or preview.get("synthetic_write_rows") != 0
                or preview.get("actual_nas_verified") is not False
                or preview.get("release_gate") != "HOLD"):
            raise FourSourceProofRefused("UNSAFE_SYNTHETIC_PREVIEW")
        if not approve_disposable_synthetic:
            return {
                "status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                "scenario_count": intent_count,
                "synthetic_write_rows": 0,
                "dbvora_private_source_invoked_locally": False,
                "nas_verified": False, "release_gate": "HOLD",
            }
        approved = verify(
            hae_root, sovia_root, goal, root, REQUIRED,
            candidates=candidates, metadata_consent=True,
            approved_sha256=preview["approve_plan_sha256"],
            dbvora_root=dbvora_root,
        )
        summary = approved.get("dbvora", {})
        if (approved.get("status") != "PASS"
                or not _pinned_source_claim_valid(approved, expect_dbvora=True)
                or approved.get("local_inspection_performed") is not True
                or approved.get("sovia_advisory") != "REVIEW_ONLY"
                or approved.get("sovia_finding_count") != intent_count
                or approved.get("intent_count") != intent_count
                or approved.get("file_contents_opened") is not False
                or approved.get("raw_paths_or_names_returned") is not False
                or approved.get("customer_file_contents_used") is not False
                or approved.get("la_execution_verified") is not True
                or approved.get("dbvora_metadata_inspected") is not True
                or approved.get("dbvora_private_source_invoked_locally") is not True
                or approved.get("synthetic_write_rows") != intent_count
                or approved.get("approval_receipts") != 1
                or approved.get("replay_duplicate_writes") != 0
                or approved.get("ephemeral_sqlite_deleted_after_run") is not True
                or type(summary) is not dict
                or summary.get("status") != "SYNTHETIC_SCHEMA_METADATA_ONLY"
                or summary.get("contract") != "ugreen-dbvora-p0-redacted.v1"
                or summary.get("scope") != "DISPOSABLE_LOCAL_LA_SQLITE_NOT_NAS"
                or summary.get("source_implementation_independently_verified") is not False
                or type(summary.get("column_count")) is not int
                or summary["column_count"] < 1
                or type(summary.get("main_database_file_bytes")) is not int
                or summary["main_database_file_bytes"] < 100
                or type(summary.get("table_count")) is not int
                or summary.get("table_count") < 1
                or summary.get("real_nas_or_customer_database_inspected") is not False
                or approved.get("actual_nas_verified") is not False
                or approved.get("registered_uliya_expert_invoked") is not False
                or approved.get("release_gate") != "HOLD"):
            raise FourSourceProofRefused("FOUR_SOURCE_SYNTHETIC_EVIDENCE_INCOMPLETE")
        return {
            "status": "PASS",
            "scope": "DISPOSABLE_SYNTHETIC_LOCAL_ONLY",
            "actual_private_hae_la_invoked": True,
            "actual_public_sovia_invoked": True,
            "actual_private_dbvora_invoked": True,
            "intent_count": intent_count,
            "la_write_rows": intent_count,
            "la_replay_duplicates": 0,
            "approval_receipts": 1,
            "dbvora_table_count": summary["table_count"],
            "dbvora_column_count": summary["column_count"],
            "temporary_fixture_deleted": True,
            "actual_nas_verified": False,
            "registered_uliya_expert_invoked": False,
            "release_gate": "HOLD",
        }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Four-source disposable synthetic local proof; no NAS/customer data"
    )
    p.add_argument("--hae-root", required=True, type=Path)
    p.add_argument("--sovia-root", required=True, type=Path)
    p.add_argument("--dbvora-root", required=True, type=Path)
    p.add_argument("--approve-disposable-synthetic", action="store_true")
    p.add_argument("--intent-count", type=int, choices=(1, 2, 3), default=2)
    options = p.parse_args(argv)
    try:
        result = run_matrix(
            options.hae_root, options.sovia_root, options.dbvora_root,
            approve_disposable_synthetic=options.approve_disposable_synthetic,
            intent_count=options.intent_count,
        )
    except (FourSourceProofRefused, ProofRefused, OSError, ValueError,
            TypeError, ImportError, RuntimeError, KeyError, sqlite3.Error):
        print(json.dumps({
            "status": "FAIL", "reason_code": "FOUR_SOURCE_PROOF_REFUSED",
            "actual_nas_verified": False, "release_gate": "HOLD",
        }), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
