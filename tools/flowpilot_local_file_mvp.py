"""G60 real OS-file metadata MVP on generated, temporary, synthetic files.

This CLI creates its own disposable noncustomer fixture. It CANNOT take a
user-selected local folder, contact NAS, invoke a registered Uliya Expert or
prove official Skill execution. Only relative path lstat is used for evidence.
"""
from __future__ import annotations

import argparse
import json
import stat
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from flowpilot.evidence import ObservationBatch, Observed, safe_path
from flowpilot.pipeline import evaluate_offline
from flowpilot_mvp_cli import DEFAULT_REQUESTS, DEMO_ROOT
from flowpilot_offline_demo import CASES

# Synthetic bytes only. Do not put real NAS/customer names or data here.
FILES = {
    "complete_synthetic_handoff": ("README.md", "release/output.pdf"),
    "missing_required_synthetic": ("README.md",),
    "conflicting_versions_synthetic": ("release/final.pdf", "release/final_v2.pdf"),
    "truncated_or_denied_synthetic": (),
    "symlink_unknown_synthetic": (),
}


def inspect_exact_local_fixture(root: Path, paths: tuple[str, ...]) -> tuple[tuple[Observed, ...], bool]:
    """Read exact relative names via lstat; never follow a symlink or open content."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected a real nonsymlink generated fixture folder")
    if len(paths) > 100 or len(set(paths)) != len(paths):
        raise ValueError("Duplicate or excessive inspection checklist")
    # Validate ALL names before looking at ANY path.
    for relative in paths:
        safe_path(relative)
    observed: list[Observed] = []
    scan_complete = True
    for relative in paths:
        child = root
        parts = relative.split("/")
        for i, part in enumerate(parts):
            child = child / part
            try:
                entry = child.lstat()
            except FileNotFoundError:
                # Exact path absent; no directory inventory or unrelated data.
                break
            except (PermissionError, NotADirectoryError, OSError):
                scan_complete = False
                break
            if stat.S_ISLNK(entry.st_mode):
                observed.append(Observed(relative, "", is_symlink=True, contained=None))
                break
            if i != len(parts) - 1:
                if not stat.S_ISDIR(entry.st_mode):
                    observed.append(Observed(relative, "", contained=None))
                    break
            elif stat.S_ISREG(entry.st_mode):
                observed.append(Observed(relative, "local-synthetic://" + relative, contained=True))
            else:
                observed.append(Observed(relative, "", contained=None))
    return tuple(observed), scan_complete


def run_local_fixture(scenario: str, request: str | None = None) -> dict:
    """One complete goal→real temporary filesystem check→conservative report."""
    if scenario not in FILES or scenario not in CASES:
        raise ValueError("Unknown synthetic-only local scenario")
    goal = DEFAULT_REQUESTS[scenario] if request is None else request
    if not isinstance(goal, str) or len(goal) > 2048:
        raise ValueError("Request must be bounded text")
    fixture = CASES[scenario]
    requirements = tuple(fixture["required_paths"])
    candidates = fixture.get("version_candidates", {})
    extra = tuple(path for values in candidates.values() for path in values)
    with tempfile.TemporaryDirectory(prefix="ugreen-flowpilot-synthetic-") as scratch:
        base = Path(scratch)
        scope = base / "authorized-synthetic"
        scope.mkdir()
        for relative in FILES[scenario]:
            safe_path(relative)
            target = scope / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"UGREEN FLOWPILOT TEST CONTENT, NOT CUSTOMER DATA\n")
        if scenario == "symlink_unknown_synthetic":
            external = base / "untrusted-synthetic"
            external.write_text("untrusted synthetic", encoding="utf-8")
            linked = scope / "release/final.pdf"
            linked.parent.mkdir(parents=True, exist_ok=True)
            try:
                linked.symlink_to(external)
            except (OSError, NotImplementedError) as exc:
                raise RuntimeError("SYNTHETIC_SYMLINK_FIXTURE_UNAVAILABLE") from exc
        observations, local_complete = inspect_exact_local_fixture(
            scope, tuple(dict.fromkeys(requirements + extra))
        )
        # Incomplete-permission scenario is deliberately simulated; NEVER
        # confuse that test with an OS permission failure on the host.
        force_incomplete = scenario == "truncated_or_denied_synthetic"
        claimed_complete = local_complete and not force_incomplete
        batch = ObservationBatch(
            DEMO_ROOT, observations,
            permission_confirmed=not force_incomplete,
            registered_adapter_confirmed=not force_incomplete,
            scan_complete=claimed_complete,
            pagination_complete=claimed_complete,
            failed=not claimed_complete,
        )
        outcome = evaluate_offline(
            request=goal, root=DEMO_ROOT, required_paths=requirements,
            metadata_approved=True, unknown_processing_accepted=True,
            batch=batch, version_candidates=candidates,
        )
        # No external filesystem names or contents leave the scratch scope.
        return {
            "mode": "EPHEMERAL_LOCAL_FILESYSTEM_SYNTHETIC_MVP",
            "scenario": scenario,
            "status": outcome.status,
            "goal_type": outcome.plan.intent.value if outcome.plan.intent else None,
            "planned_expert_steps_not_executed": [step.id for step in outcome.plan.steps],
            "filesystem_probe": "OS_LSTAT_ONLY_ON_GENERATED_TEST_FILES",
            "actually_inspected_local_metadata": True,
            "simulated_incomplete_or_denied": force_incomplete,
            "items": [
                {"path": item.relative_path, "state": item.state.value,
                 "synthetic_evidence": list(item.evidence)}
                for item in (outcome.report.items if outcome.report else ())
            ],
            "limitations": list(outcome.limitations),
            "scratch_scope": "AUTOMATICALLY_REMOVED",
            "real_nas_verified": False,
            "registered_uliya_expert_invoked": False,
            "official_creator_invoked": False,
            "entrant_approval": "PENDING",
            "devpost_submitted": False,
            "release_gate": "HOLD",
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Real local temp-file read-only metadata smoke; NOT a NAS demo")
    p.add_argument("--scenario", choices=tuple(FILES),
                   default="complete_synthetic_handoff")
    p.add_argument("--request", help="Natural-language bounded test goal")
    args = p.parse_args(argv)
    print(json.dumps(run_local_fixture(args.scenario, args.request),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
