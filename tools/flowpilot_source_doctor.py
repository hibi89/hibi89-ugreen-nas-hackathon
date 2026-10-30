"""Read-only exact Git source readiness for owner-local synthetic integration.

No private module imports, document content reads, network calls or NAS access.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Direct execution (including PowerShell from any working directory) puts
# tools/ rather than the repository root on sys.path. Fix before imports.
PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from tools.verify_private_hae_chain import (
    EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA, ProofRefused, verify_checkout,
)
from tools.verify_local_metadata_la_chain import EXPECTED_DBVORA_SHA

SOURCES = (
    ("hae_la", EXPECTED_HAE_SHA, ("packages/lightning-azent",),
     "packages/lightning-azent/lightning_azent/runtime.py"),
    ("sovia", EXPECTED_SOVIA_SHA,
     ("sovia_la_plan_preflight.py", "sovia_pii_preflight.py"),
     "sovia_la_plan_preflight.py"),
    ("dbvora", EXPECTED_DBVORA_SHA, ("dbvora",), "dbvora/inventory.py"),
)

SAFE_FAILURES = frozenset({
    "SOURCE_ROOT_MISSING", "SOURCE_ROOT_NOT_DIRECTORY",
    "SOURCE_ROOT_NOT_GIT_TOPLEVEL", "SOURCE_SHA_MISMATCH",
    "SOURCE_FILES_MODIFIED", "CHECKOUT_UNVERIFIED",
    "LOCAL_GIT_UNAVAILABLE", "EXPECTED_SOURCE_SHA_INVALID",
})


def inspect_sources(hae_root: Path, sovia_root: Path, dbvora_root: Path) -> dict:
    """Checks only explicitly supplied Git roots and never reports their paths."""
    python_ok = sys.version_info >= (3, 11)
    git_ok = shutil.which("git") is not None
    statuses = {}
    for (key, sha, paths, entry), root in zip(
        SOURCES, (hae_root, sovia_root, dbvora_root)
    ):
        status = "NOT_CHECKED"
        if not python_ok:
            status = "PYTHON_3_11_REQUIRED"
        elif not git_ok:
            status = "GIT_UNAVAILABLE"
        elif not isinstance(root, Path) or root.is_symlink():
            status = "INVALID_SOURCE_ROOT"
        else:
            try:
                checked = verify_checkout(root, sha, paths)
                source = checked / entry
                status = ("EXACT_SOURCE_READY"
                          if source.is_file() and not source.is_symlink()
                          else "PINNED_ENTRYPOINT_UNAVAILABLE")
            except ProofRefused as exc:
                status = str(exc) if str(exc) in SAFE_FAILURES else "LOCAL_SOURCE_UNVERIFIED"
            except (OSError, ValueError, RuntimeError):
                status = "LOCAL_SOURCE_UNVERIFIED"
        statuses[key] = {"status": status, "expected_sha": sha}
    preview_ready = all(statuses[key]["status"] == "EXACT_SOURCE_READY"
                        for key in ("hae_la", "sovia"))
    ready = preview_ready and statuses["dbvora"]["status"] == "EXACT_SOURCE_READY"
    return {
        "status": ("READY_FOR_LOCAL_SYNTHETIC_PREVIEW"
                   if preview_ready else "BLOCKED"),
        "python_3_11_or_newer": python_ok,
        "git_available": git_ok,
        "sources": statuses,
        "owner_local_synthetic_preview_readiness": preview_ready,
        "owner_local_synthetic_execution_readiness": ready,
        "owner_local_synthetic_source_readiness": ready,
        "private_source_executed": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only checkout readiness, no NAS")
    parser.add_argument("--hae-root", type=Path, required=True)
    parser.add_argument("--sovia-root", type=Path, required=True)
    parser.add_argument("--dbvora-root", type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        row = inspect_sources(options.hae_root, options.sovia_root, options.dbvora_root)
    except (OSError, ValueError, TypeError, RuntimeError):
        row = {"status": "BLOCKED", "reason": "SOURCE_PROBE_REFUSED",
               "actual_nas_verified": False, "release_gate": "HOLD"}
    print(json.dumps(row, sort_keys=True))
    return 0 if row.get("owner_local_synthetic_preview_readiness") else 2


if __name__ == "__main__":
    raise SystemExit(main())
