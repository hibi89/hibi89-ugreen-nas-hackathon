"""G104 exactly-pinned synthetic NAS trial fixture checker; never accesses NAS.

The fixture is deliberately NOT the official Uliya Skill submission ZIP.
A success here only proves local archive integrity, not working NAS tools.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile

PIN = "84640976377953e5167f5d901b3951e044e2e7005178e3df7801ec157bda9cb3"
ROOT = "FLOWPILOT_G104_SYNTHETIC_TEST/"
FILES = frozenset(ROOT + suffix for suffix in (
    "README.md",
    "project/requirements.md", "project/design/architecture.md",
    "project/handoff/summary.md", "project/handoff/review-v1.md",
    "project/handoff/review-v2.md", "project/.env",
    "project/deep/level2/level3/beyond_depth.md",
))


class FixtureRefused(ValueError):
    pass


def verify_archive(raw: bytes, *, expected_sha: str = PIN) -> dict:
    if not raw or len(raw) > 1_000_000 or sha256(raw).hexdigest() != expected_sha:
        raise FixtureRefused("Fixture ZIP is missing, oversized or SHA-mismatched")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            records = archive.infolist()
            names = [entry.filename for entry in records]
            if len(names) != len(FILES) or set(names) != FILES or len(set(names)) != len(names):
                raise FixtureRefused("Fixture entries differ from pinned manifest")
            if any(entry.is_dir() or entry.flag_bits & 1 or entry.file_size > 100_000
                   for entry in records) or archive.testzip() is not None:
                raise FixtureRefused("Fixture ZIP has unsafe or damaged members")
    except (BadZipFile, RuntimeError, OSError) as exc:
        raise FixtureRefused("Unreadable fixture archive") from exc
    return {"status": "EXACT_SYNTHETIC_INPUT_VERIFIED_NOT_NAS",
            "fixture_sha256": sha256(raw).hexdigest(), "files": len(FILES),
            "real_nas_test_executed": False, "official_uliya_checker_executed": False,
            "owner_approved_upload": False, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G104 exact synthetic archive preflight")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        path = args.path
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise FixtureRefused("Missing or unsafe fixture path")
        result = verify_archive(path.read_bytes())
        rc = 0
    except (OSError, FixtureRefused) as exc:
        result = {"status": "LOCAL_FIXTURE_REFUSED", "error": str(exc),
                  "real_nas_test_executed": False, "release_gate": "HOLD"}
        rc = 2
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
