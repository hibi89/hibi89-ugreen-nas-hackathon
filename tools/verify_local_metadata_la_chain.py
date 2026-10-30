"""Optional owner-local lstat -> real pinned HAE LA -> real SOVIA proof.

The caller must approve exact local metadata reading and then a separate
SHA-bound plan before synthetic SQLite writes. No NAS, Uliya, external API,
customer-content reading or network requests. Do not point at an untrusted
concurrently mutating directory or mapped NAS drive.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Exact private DBVORA feature SHA was read from its repository; code stays private.
EXPECTED_DBVORA_SHA = "7f9a1c0d0f0e31f68fb600e47d04ccff1e22faaf"

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from integrations.local_metadata_la_chain import run_local_observation_chain
from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused, verify_checkout,
)


def _candidates(items: list[str]) -> dict[str, list[str]] | None:
    if not items:
        return None
    if len(items) > 100:
        raise ValueError("EXCESSIVE_CANDIDATES")
    values: dict[str, list[str]] = {}
    for item in items:
        if type(item) is not str or item.count("=") != 1:
            raise ValueError("INVALID_CANDIDATE_ASSIGNMENT")
        source, candidate = item.split("=", 1)
        values.setdefault(source, []).append(candidate)
    return values


def load_pinned_dbvora_reader(dbvora_root: Path):
    """Opt-in local import only; never fetch or copy private source to UGREEN."""
    checked = verify_checkout(
        dbvora_root, EXPECTED_DBVORA_SHA, ("dbvora",),
    )
    entry = checked / "dbvora" / "inventory.py"
    if not entry.is_file() or entry.is_symlink():
        raise ProofRefused("DBVORA_PRIVATE_ENTRYPOINT_UNVERIFIED")
    sys.path.insert(0, str(checked))
    from dbvora.inventory import inspect_sqlite
    source = Path(inspect_sqlite.__code__.co_filename).resolve()
    if source != entry.resolve():
        raise ProofRefused("DBVORA_PRIVATE_IMPORT_SOURCE_MISMATCH")
    return inspect_sqlite


def verify(
    hae_root: Path,
    sovia_root: Path,
    goal: str,
    root: Path,
    required: list[str],
    *,
    candidates: dict[str, list[str]] | None = None,
    metadata_consent: bool = False,
    approved_sha256: str | None = None,
    dbvora_root: Path | None = None,
) -> dict:
    # Private DBVORA may inspect only after both consent gates. The preview
    # without exact SHA must never load private source or touch its runtime.
    if dbvora_root is not None and (metadata_consent is not True
                                    or approved_sha256 is None):
        raise ProofRefused("DBVORA_REQUIRES_EXACT_PLAN_APPROVAL")
    hae = verify_checkout(
        hae_root, EXPECTED_HAE_SHA, ("packages/lightning-azent",),
    )
    sovia = verify_checkout(
        sovia_root, EXPECTED_SOVIA_SHA,
        ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"),
    )
    la_package = hae / "packages/lightning-azent"
    if not (la_package / "lightning_azent/runtime.py").is_file():
        raise ProofRefused("PINNED_LA_RUNTIME_MISSING")
    if not (sovia / "sovia_la_plan_preflight.py").is_file():
        raise ProofRefused("PINNED_SOVIA_ASSESSOR_MISSING")
    sys.path.insert(0, str(la_package))
    sys.path.insert(0, str(sovia))
    from lightning_azent import LAExecutor
    from sovia_la_plan_preflight import assess

    dbvora_reader = (load_pinned_dbvora_reader(dbvora_root)
                     if dbvora_root is not None else None)
    result = run_local_observation_chain(
        goal, root, required, LAExecutor, assess,
        candidates=candidates, approve_local_metadata=metadata_consent,
        approve_plan_sha256=approved_sha256,
        dbvora_reader=dbvora_reader,
    )
    return {
        **result,
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "pinned_sources": "PASS",
        "dbvora_private_checkout_pinned": dbvora_root is not None,
        "dbvora_private_source_invoked_locally": (
            dbvora_root is not None and result.get("dbvora_metadata_inspected") is True
        ),
        "dbvora_commit": EXPECTED_DBVORA_SHA if dbvora_root is not None else None,
        "independent_public_ci_private_hae_executed": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Consented LOCAL lstat + pinned LA/SOVIA synthetic proof, never NAS",
    )
    ap.add_argument("--hae-root", required=True, type=Path)
    ap.add_argument("--sovia-root", required=True, type=Path)
    ap.add_argument("--dbvora-root", type=Path,
                    help="Optional exact-source PRIVATE DBVORA checkout; only with both approval flags")
    ap.add_argument("--root", required=True, type=Path,
                    help="Owner-selected existing LOCAL directory, not NAS/UNC")
    ap.add_argument("--goal", required=True)
    ap.add_argument("--required", required=True, action="append",
                    help="Exact relative file name, repeatable (1-12)")
    ap.add_argument("--candidate", action="append", default=[],
                    help="Exact required=alternative mapping, repeatable")
    ap.add_argument("--approve-local-metadata", action="store_true",
                    help="Explicit read-only lstat consent for this root/paths")
    ap.add_argument("--approve-plan-sha256",
                    help="Exact fingerprint from prior approved-metadata preview")
    a = ap.parse_args(argv)
    try:
        result = verify(
            a.hae_root, a.sovia_root, a.goal, a.root, a.required,
            candidates=_candidates(a.candidate),
            metadata_consent=a.approve_local_metadata,
            approved_sha256=a.approve_plan_sha256,
            dbvora_root=a.dbvora_root,
        )
    except (OSError, ValueError, TypeError, RuntimeError, ImportError,
            KeyError, sqlite3.Error) as exc:
        code = str(exc) if isinstance(exc, ProofRefused) else "OWNER_LOCAL_METADATA_PROOF_REFUSED"
        print(json.dumps({
            "status": "FAIL", "reason_code": code, "actual_nas_verified": False,
            "release_gate": "HOLD",
        }), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
