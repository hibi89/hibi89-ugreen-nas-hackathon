"""G48 deterministic evidence-report demonstration using invented NAS-like metadata.

DOES NOT access NAS, Uliya, network, user files, real experts or actual agents.
Only data already supplied in memory is handled, for development QA.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flowpilot.evidence import Observed, ObservationBatch, report


CASES: dict[str, dict[str, Any]] = {
    "complete_synthetic_handoff": {
        "required_paths": ["README.md", "release/output.pdf"],
        "observations": [
            {"relative_path": "README.md", "reference": "synthetic://readme", "contained": True},
            {"relative_path": "release/output.pdf", "reference": "synthetic://output", "contained": True},
        ],
        "permission_confirmed": True,
        "registered_adapter_confirmed": True,
        "scan_complete": True,
        "pagination_complete": True,
    },
    "missing_required_synthetic": {
        "required_paths": ["README.md", "release/output.pdf"],
        "observations": [{"relative_path": "README.md", "reference": "synthetic://readme", "contained": True}],
        "permission_confirmed": True,
        "registered_adapter_confirmed": True,
        "scan_complete": True,
        "pagination_complete": True,
    },
    "conflicting_versions_synthetic": {
        "required_paths": ["release/final.pdf"],
        "observations": [
            {"relative_path": "release/final.pdf", "reference": "synthetic://candidate1", "contained": True},
            {"relative_path": "release/final_v2.pdf", "reference": "synthetic://candidate2", "contained": True},
        ],
        "version_candidates": {"release/final.pdf": ["release/final_v2.pdf"]},
        "permission_confirmed": True,
        "registered_adapter_confirmed": True,
        "scan_complete": True,
        "pagination_complete": True,
    },
    "truncated_or_denied_synthetic": {
        "required_paths": ["release/final.pdf"],
        "observations": [],
        "permission_confirmed": False,
        "registered_adapter_confirmed": False,
        "scan_complete": False,
        "pagination_complete": False,
    },
    "symlink_unknown_synthetic": {
        "required_paths": ["release/final.pdf"],
        "observations": [{"relative_path": "release/final.pdf", "reference": "synthetic://link", "is_symlink": True}],
        "permission_confirmed": True,
        "registered_adapter_confirmed": True,
        "scan_complete": True,
        "pagination_complete": True,
    },
}


def simulate(name: str, fixture: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a self-contained synthetic fixture; never infer NAS provenance."""
    if not isinstance(name, str) or not name or len(name) > 96:
        raise ValueError("Invalid scenario label")
    if not isinstance(fixture, dict):
        raise ValueError("Expected a single in-memory fixture")
    allowed = {"required_paths", "observations", "version_candidates", "permission_confirmed",
               "registered_adapter_confirmed", "scan_complete", "pagination_complete", "failed"}
    if set(fixture) - allowed:
        raise ValueError("Unexpected fields: no NAS connection or filesystem input allowed")
    observations = tuple(Observed(**item) for item in fixture.get("observations", ()))
    batch = ObservationBatch(
        authorized_root="SYNTHETIC_OWNER_SCOPE_NOT_NAS",
        observations=observations,
        permission_confirmed=fixture.get("permission_confirmed", False),
        registered_adapter_confirmed=fixture.get("registered_adapter_confirmed", False),
        scan_complete=fixture.get("scan_complete", False),
        pagination_complete=fixture.get("pagination_complete", False),
        failed=fixture.get("failed", False),
    )
    result = report(fixture.get("required_paths", ()), batch,
                    version_candidates=fixture.get("version_candidates", {}))
    return {
        "scenario": name,
        "mode": "OFFLINE_SYNTHETIC_ONLY",
        "live_nas": "NOT_RUN",
        "registered_agent": "NOT_INVOKED",
        "official_creator": "NOT_RUN",
        "actual_nas_verified": False,
        "overall": result.overall.value,
        "scope_complete_claimed_by_fixture": result.scope_complete,
        "items": [
            {"path": item.relative_path, "state": item.state.value, "evidence": list(item.evidence),
             "reason": item.reason} for item in result.items
        ],
        "limitations": list(result.limitations),
    }


def run_cases() -> dict[str, Any]:
    return {
        "status": "SYNTHETIC_QA_ONLY_NO_NAS_EXECUTION",
        "cases": [simulate(name, fixture) for name, fixture in CASES.items()],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="G48 synthetic NAS handoff cases; no real NAS access")
    parser.add_argument("--output", type=Path, help="Write JSON summary to a chosen local path")
    args = parser.parse_args()
    data = json.dumps(run_cases(), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.is_symlink():
            raise ValueError("Output symlink refused")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
