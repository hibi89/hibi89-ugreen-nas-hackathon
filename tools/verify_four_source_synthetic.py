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

from tools.verify_private_hae_chain import ProofRefused
from tools.verify_local_metadata_la_chain import verify

GOAL = "파일 누락 확인 그리고 인계 확인"
REQUIRED = ["README.md"]
REQUIRED_STATUS = "WAITING_EXACT_LOCAL_PLAN_APPROVAL"


class FourSourceProofRefused(ValueError):
    """Safe machine-readable failure; never expose source paths."""


def run_matrix(hae_root: Path, sovia_root: Path, dbvora_root: Path, *,
               approve_disposable_synthetic: bool = False) -> dict:
    if type(approve_disposable_synthetic) is not bool:
        raise FourSourceProofRefused("INVALID_SYNTHETIC_APPROVAL")
    # No caller-selected source folder, no NAS path or customer content.
    with tempfile.TemporaryDirectory(prefix="ugreen-4source-disposable-") as d:
        root = Path(d) / "input"
        root.mkdir(mode=0o700)
        (root / "README.md").write_text("synthetic fixture only\n", encoding="utf-8")
        preview = verify(
            hae_root, sovia_root, GOAL, root, REQUIRED,
            metadata_consent=True,
        )
        if (preview.get("status") != REQUIRED_STATUS
                or type(preview.get("approve_plan_sha256")) is not str
                or len(preview["approve_plan_sha256"]) != 64
                or preview.get("la_execution_verified") is not False
                or preview.get("dbvora_metadata_inspected") is not False
                or preview.get("synthetic_write_rows") != 0
                or preview.get("actual_nas_verified") is not False
                or preview.get("release_gate") != "HOLD"):
            raise FourSourceProofRefused("UNSAFE_SYNTHETIC_PREVIEW")
        if not approve_disposable_synthetic:
            return {
                "status": "WAITING_DISPOSABLE_SYNTHETIC_WRITE_APPROVAL",
                "scenario_count": 2,
                "synthetic_write_rows": 0,
                "dbvora_private_source_invoked_locally": False,
                "nas_verified": False, "release_gate": "HOLD",
            }
        approved = verify(
            hae_root, sovia_root, GOAL, root, REQUIRED,
            metadata_consent=True,
            approved_sha256=preview["approve_plan_sha256"],
            dbvora_root=dbvora_root,
        )
        summary = approved.get("dbvora", {})
        if (approved.get("status") != "PASS"
                or approved.get("la_execution_verified") is not True
                or approved.get("dbvora_metadata_inspected") is not True
                or approved.get("dbvora_private_source_invoked_locally") is not True
                or approved.get("synthetic_write_rows") != 2
                or approved.get("approval_receipts") != 1
                or approved.get("replay_duplicate_writes") != 0
                or approved.get("ephemeral_sqlite_deleted_after_run") is not True
                or type(summary) is not dict
                or summary.get("status") != "SYNTHETIC_SCHEMA_METADATA_ONLY"
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
            "la_write_rows": 2,
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
    options = p.parse_args(argv)
    try:
        result = run_matrix(
            options.hae_root, options.sovia_root, options.dbvora_root,
            approve_disposable_synthetic=options.approve_disposable_synthetic,
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
