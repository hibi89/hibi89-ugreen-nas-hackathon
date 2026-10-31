"""G106: real local OS lstat on exact G104 synthetic ZIP; never Uliya/NAS.

No user-selected directory, no customer content, no network and no document read.
The registered-adapter flags in this rehearsal are synthetic claims only.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import stat
import sys
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from verify_g104_nas_trial_fixture import ROOT, verify_archive
from flowpilot_local_file_mvp import inspect_exact_local_fixture
from flowpilot.evidence import ObservationBatch, ItemState, safe_path
from flowpilot.pipeline import evaluate_offline

SCOPE = "/volume1/FLOWPILOT_G104_SYNTHETIC_TEST/project"
REQUIRED = ("handoff/summary.md", "design/architecture.md", "handoff/signoff.md")
VERSIONS = ("handoff/review-v1.md", "handoff/review-v2.md")
EXTRACTABLE = frozenset(("requirements.md", "design/architecture.md",
                         "handoff/summary.md", "handoff/review-v1.md",
                         "handoff/review-v2.md"))


class LocalVerticalRefused(ValueError):
    pass


def _extract_safely(raw: bytes, root: Path) -> int:
    """Extract only allowlisted nonrestricted files inside disposable scratch."""
    count = 0
    prefix = ROOT + "project/"
    with ZipFile(BytesIO(raw)) as z:
        for info in z.infolist():
            if not info.filename.startswith(prefix):
                continue
            name = info.filename[len(prefix):]
            if name not in EXTRACTABLE:  # excludes .env and over-depth files
                continue
            safe_path(name)
            mode = info.external_attr >> 16
            if info.is_dir() or not stat.S_ISREG(mode) or info.file_size > 100_000:
                raise LocalVerticalRefused("Unsafe expected synthetic entry metadata")
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(info))
            count += 1
    if count != len(EXTRACTABLE):
        raise LocalVerticalRefused("Missing expected synthetic project items")
    return count


def run_exact_fixture(raw: bytes) -> dict:
    fixture = verify_archive(raw)  # checks fixed G104 SHA, names, size, CRC
    if fixture["real_nas_test_executed"] is not False:
        raise LocalVerticalRefused("Unexpected real-NAS claim")
    with tempfile.TemporaryDirectory(prefix="ugreen-g106-") as temp:
        root = Path(temp) / "FLOWPILOT_G104_SYNTHETIC_TEST" / "project"
        root.mkdir(parents=True)
        n = _extract_safely(raw, root)
        checklist = tuple(dict.fromkeys(REQUIRED + VERSIONS))
        observed, complete = inspect_exact_local_fixture(root, checklist)
        if not complete:
            raise LocalVerticalRefused("Actual local lstat incomplete")
        batch = ObservationBatch(SCOPE, observed, True, True, True, True, False)
        intents = (
            ("CHECK_REQUIRED", "check required project handoff files", REQUIRED, {}),
            ("HANDOFF_AUDIT", "handoff audit", REQUIRED, {}),
            ("REVIEW_VERSIONS", "compare versions of handoff review drafts",
             (VERSIONS[0],), {VERSIONS[0]: (VERSIONS[1],)}),
            ("SUMMARIZE_SELECTED", "summarize handoff/summary.md", (REQUIRED[0],), {}),
        )
        modes = {}
        for target, phrase, required, versions in intents:
            result = evaluate_offline(
                request=phrase, root=SCOPE, required_paths=required,
                metadata_approved=True, unknown_processing_accepted=True,
                batch=batch, version_candidates=versions, document_approved=False,
            )
            if (result.report is None or result.plan.intent is None
                    or result.plan.intent.value != target or result.actual_nas_verified):
                raise LocalVerticalRefused("Incorrect offline intent/evidence provenance")
            modes[target] = {
                "status": result.status,
                "items": {x.relative_path: x.state.value for x in result.report.items},
                "planned_steps_not_executed": [x.id for x in result.plan.steps],
                "document_content_read": False,
            }
        partial = ObservationBatch(SCOPE, observed, True, True, False, False, False)
        uncertain = evaluate_offline(
            request="check required project handoff files", root=SCOPE,
            required_paths=REQUIRED, metadata_approved=True,
            unknown_processing_accepted=True, batch=partial,
        )
        if uncertain.report is None or any(x.state is not ItemState.NOT_CHECKED
                                            for x in uncertain.report.items):
            raise LocalVerticalRefused("Unverified partial listing incorrectly trusted")
        modes["PARTIAL_SCAN_NEGATIVE"] = {
            "status": uncertain.status,
            "items": {x.relative_path: x.state.value for x in uncertain.report.items},
        }
        if not (
            modes["CHECK_REQUIRED"]["status"] == "BLOCKED"
            and modes["CHECK_REQUIRED"]["items"] ==
                dict(zip(REQUIRED, ("PRESENT", "PRESENT", "MISSING")))
            and modes["HANDOFF_AUDIT"]["status"] == "BLOCKED"
            and modes["REVIEW_VERSIONS"]["items"][VERSIONS[0]] == "VERSION_REVIEW"
            and modes["SUMMARIZE_SELECTED"]["items"][REQUIRED[0]] == "PRESENT"
            and "document" not in modes["SUMMARIZE_SELECTED"]["planned_steps_not_executed"]
        ):
            raise LocalVerticalRefused("Observed local file results violate G104 contract")
        return {
            "status": "G106_REAL_LOCAL_OS_METADATA_VERTICAL_PASS_NOT_NAS",
            "fixture_sha256": fixture["fixture_sha256"],
            "extracted_nonrestricted_files_only": n,
            "physically_probed_relative_paths": checklist,
            "modes": modes,
            "metadata_origin": "REAL_LOCAL_LSTAT_OF_EPHEMERAL_SYNTHETIC_FILES",
            "registered_agent_flag": "SIMULATED_FOR_OFFLINE_EVALUATION_ONLY",
            "document_content_read_by_agent": False,
            "original_input_modified": False,
            "scratch_retained": False,
            "official_uliya_checker_executed": False,
            "real_nas_test_executed": False,
            "devpost_submitted": False,
            "release_gate": "HOLD",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pinned G104 ZIP -> local lstat -> report; NOT NAS")
    parser.add_argument("--fixture-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        p = args.fixture_zip
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1_000_000:
            raise LocalVerticalRefused("Missing or unsafe G104 input")
        output, code = run_exact_fixture(p.read_bytes()), 0
    except (OSError, ValueError, RuntimeError):
        output, code = {"status": "G106_LOCAL_VERTICAL_FAIL",
                        "real_nas_test_executed": False,
                        "release_gate": "HOLD"}, 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
