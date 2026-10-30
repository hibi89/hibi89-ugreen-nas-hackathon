"""Runnable local OS-lstat FlowPilot demo, independent of private HAE/DBVORA.

Generates five disposable synthetic test folders; uses the actual bounded
FlowPilot planner and OS metadata observer. No user paths, NAS, LLM, Uliya,
SQLite or private imports. Exposes only redacted counts/flags.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
for folder in (PROJECT, TOOLS):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from flowpilot_goal_preview import process_goal

SCENARIOS = (
    ("required_file", "파일 누락 확인", ["README.md"], None, ("README.md",),
     "NEEDS_REVIEW", 1),
    ("handoff_check", "파일 누락 확인 그리고 인계 확인", ["README.md"], None,
     ("README.md",), "NEEDS_REVIEW", 2),
    ("three_intents", "파일 누락 확인 그리고 인계 확인 그리고 버전 비교",
     ["README.md"], {"README.md": ["README_final.md"]},
     ("README.md", "README_final.md"), "NEEDS_REVIEW", 3),
    ("missing_file", "파일 누락 확인", ["missing.md"], None,
     (), "BLOCKED", 1),
    ("missing_version_candidate", "버전 비교", ["README.md"],
     {"README.md": ["README_final.md"]}, ("README.md",), "NEEDS_REVIEW", 1),
)


class RealLocalDemoRefused(ValueError):
    """Only a fixed opaque failure code may be returned to the HTTP caller."""


def run_real_local_demo() -> dict:
    results = []
    for key, goal, required, candidates, names, expected, steps in SCENARIOS:
        with tempfile.TemporaryDirectory(prefix="ugreen-real-os-metadata-") as tmp:
            root = Path(tmp) / "generated"
            root.mkdir(mode=0o700)
            for name in names:
                (root / name).write_bytes(b"disposable test fixture, NOT CUSTOMER DATA\n")
            try:
                preview = process_goal(
                    goal, root=root, required=required, candidates=candidates,
                    metadata_consent=False,
                )
                if (preview.get("status") != "WAITING_APPROVAL"
                        or preview.get("executed_steps") != 0
                        or preview.get("owner_folder_metadata_accessed") is not False
                        or preview.get("file_contents_opened") is not False):
                    raise RealLocalDemoRefused("UNSAFE_SYNTHETIC_PREVIEW")
                actual = process_goal(
                    goal, root=root, required=required, candidates=candidates,
                    metadata_consent=True,
                )
                counts = actual.get("finding_counts")
                if (actual.get("status") != expected
                        or actual.get("executed_steps") != steps
                        or actual.get("planned_steps") != steps
                        or actual.get("owner_folder_metadata_accessed") is not True
                        or actual.get("file_contents_opened") is not False
                        or actual.get("raw_paths_returned") is not False
                        or actual.get("nas_verified") is not False
                        or actual.get("registered_uliya_expert_invoked") is not False
                        or actual.get("release_gate") != "HOLD"
                        or type(counts) is not dict
                        or any(type(v) is not int or v < 0 for v in counts.values())):
                    raise RealLocalDemoRefused("UNVERIFIED_OS_OBSERVATION")
                if key == "three_intents" and counts.get("VERSION_REVIEW") != 1:
                    raise RealLocalDemoRefused("VERSION_REVIEW_NOT_OBSERVED")
                if key == "missing_file" and counts.get("MISSING") != 1:
                    raise RealLocalDemoRefused("MISSING_FILE_NOT_BLOCKED")
                if key == "missing_version_candidate" and (
                    counts.get("VERSION_REVIEW") != 0
                    or counts.get("NOT_CHECKED") != 0
                ):
                    raise RealLocalDemoRefused("INVALID_VERSION_OBSERVATION")
                results.append({
                    "scenario": key,
                    "status": actual["status"],
                    "planned_intents": steps,
                    "os_metadata_steps_executed": actual["executed_steps"],
                    "finding_counts": {
                        code: counts.get(code, 0)
                        for code in ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
                    },
                    "file_contents_opened": False,
                })
            except RealLocalDemoRefused:
                raise
            except (OSError, ValueError, TypeError, KeyError):
                raise RealLocalDemoRefused("REAL_LOCAL_DEMO_REFUSED") from None
    return {
        "status": "PASS_REAL_OS_LSTAT_SYNTHETIC_DEMO",
        "scenario_count": len(results),
        "observations_from_real_os": True,
        "all_test_fixtures_disposed": True,
        "private_hae_executed": False,
        "private_dbvora_executed": False,
        "real_sovia_executed": False,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
        "scenarios": results,
    }


def main() -> int:
    try:
        result = run_real_local_demo()
    except RealLocalDemoRefused:
        print(json.dumps({"status": "REAL_LOCAL_DEMO_REFUSED",
                          "actual_nas_verified": False, "release_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
