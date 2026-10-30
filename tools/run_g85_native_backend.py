"""UGREEN main-repo entrypoint for owner-authorized genuine HAE+LA+SQLite acceptance.

Only delegates to the private HAE G84/G85 verifier on the owner's PC. Does not
contain/copy private source or call NAS/Uliya/providers. Synthetic fixtures only.
Usage:
  python tools/run_g85_native_backend.py --hae-root PATH --la-package PATH --execute-synthetic-only
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import re

# Reviewed private HAE source blobs.  GitHub branch HEAD may advance for docs;
# these exact executable modules must still match BOTH HEAD and working bytes.
PINNED_PRIVATE_BLOBS = {
    "tools/g84_verify_ugreen_native.py": "04bc2f07b43a430bfa516279e93c7118a2738752",
    "tools/package_hae_integrated.py": "fa3f9b5a14b37fb9cd2c26e2e48c005e2d92eb81",
}
G82_WEB_BLOB = "ef093554750e28c0be7967d3a49e48649878d448"
G83_PUBLIC_VERIFIER = "45e09ae506b5ffed11b143f1e0387a4e7bfc303a"
LA_COMMIT = "9cba6424dadf3fadb0ccd6ed10040e322c4a62fa"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
EXPECTED_RECEIPT_FIELDS = frozenset({
    "status", "verification", "hae_web_git_blob", "la_source_commit",
    "ugreen_verifier_commit", "temporary_zipapp_sha256",
    "independent_sqlite_payload_verified", "pending_run_id_bound_to_approval",
    "sqlite_business_rows", "read_only_recovery_without_duplicate_write",
    "original_binary_replaced", "real_nas_verified", "devpost_submitted",
})


class IntegrityRefused(ValueError):
    """A local private helper is not the reviewed and pinned executable."""


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=10, check=False,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntegrityRefused("Private Git source unavailable") from exc
    if proc.returncode:
        raise IntegrityRefused("Private Git source unavailable")
    return proc.stdout.strip()


def _verify_private_source(hae_root: Path) -> None:
    """Before executing any private helper, match exact reviewed Git blobs."""
    if Path(_git(hae_root, "rev-parse", "--show-toplevel")).resolve() != hae_root:
        raise IntegrityRefused("HAE source root mismatch")
    for rel, expected in PINNED_PRIVATE_BLOBS.items():
        source = hae_root / rel
        if source.is_symlink() or not source.is_file():
            raise IntegrityRefused("Private helper absent or linked")
        if (_git(hae_root, "rev-parse", f"HEAD:{rel}") != expected
                or _git(hae_root, "hash-object", "--path", rel, rel) != expected):
            raise IntegrityRefused("Private helper source integrity mismatch")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("duplicate receipt field")
        data[key] = value
    return data


def _reject_nonfinite(_: str) -> None:
    raise ValueError("nonfinite receipt number")


def _verified_receipt(data: dict) -> bool:
    """A reported PASS alone is not sufficient evidence of native execution."""
    return (
        set(data) == EXPECTED_RECEIPT_FIELDS
        and data["status"] == PASS
        and data["verification"] == "G82_PRIVATE_RUNTIME_G83_PUBLIC_ACCEPTANCE"
        and data["hae_web_git_blob"] == G82_WEB_BLOB
        and data["la_source_commit"] == LA_COMMIT
        and data["ugreen_verifier_commit"] == G83_PUBLIC_VERIFIER
        and isinstance(data["temporary_zipapp_sha256"], str)
        and SHA256_PATTERN.fullmatch(data["temporary_zipapp_sha256"]) is not None
        and data["independent_sqlite_payload_verified"] is True
        and data["pending_run_id_bound_to_approval"] is True
        and type(data["sqlite_business_rows"]) is int
        and data["sqlite_business_rows"] == 2
        and data["read_only_recovery_without_duplicate_write"] is True
        and data["original_binary_replaced"] is False
        and data["real_nas_verified"] is False
        and data["devpost_submitted"] is False
    )


UGREEN_ROOT = Path(__file__).resolve().parents[1]
PASS = "G84_GENUINE_HAE_LA_SQLITE_E2E_PASS"


def run_native(hae_root: Path, la_package: Path, approved: bool) -> dict:
    if not approved:
        return {"status": "G85_CONSENT_REQUIRED", "native_verified": False}
    if sys.version_info < (3, 11):
        return {"status": "G85_PYTHON_311_REQUIRED", "native_verified": False}
    try:
        hae_root = hae_root.expanduser().resolve(strict=True)
        la_package = la_package.expanduser().resolve(strict=True)
        runner = hae_root / "tools" / "g84_verify_ugreen_native.py"
        if not runner.is_file() or not (la_package / "lightning_azent" / "__init__.py").is_file():
            return {"status": "G85_PRIVATE_SOURCE_MISSING", "native_verified": False}
        if hae_root == UGREEN_ROOT or la_package == UGREEN_ROOT:
            return {"status": "G85_PRIVATE_SOURCE_MISSING", "native_verified": False}
        _verify_private_source(hae_root)
        proc = subprocess.run(
            [sys.executable, str(runner),
             "--la-package", str(la_package),
             "--ugreen-root", str(UGREEN_ROOT),
             "--execute-synthetic-only"],
            cwd=str(hae_root), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=120, check=False,
        )
        if len(proc.stdout) > 8192:
            raise ValueError("oversized receipt")
        output = json.loads(
            proc.stdout.strip(), object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite,
        )
        if not isinstance(output, dict):
            raise ValueError("unexpected report type")
        if proc.returncode == 0 and _verified_receipt(output):
            return {
                "status": "G85_UGREEN_NATIVE_BACKEND_E2E_PASS",
                "native_verified": True,
                "private_runner_integrity": "G86_REVIEWED_GIT_BLOBS_MATCH",
                "backend_receipt": output,
                "real_nas_verified": False,
            }
        return {
            "status": "G85_NATIVE_BACKEND_NOT_VERIFIED",
            "native_verified": False,
            "private_gate_status": str(output.get("status", "UNKNOWN"))[:80],
            "private_failure_gate": str(output.get("failure_gate", "unclassified"))[:120],
            "returncode": proc.returncode,
        }
    except IntegrityRefused:
        return {
            "status": "G86_PRIVATE_RUNNER_INTEGRITY_REFUSED",
            "native_verified": False, "real_nas_verified": False,
        }
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "G85_NATIVE_BACKEND_NOT_VERIFIED",
            "native_verified": False,
            "error_type": type(exc).__name__,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hae-root", type=Path, required=True)
    parser.add_argument("--la-package", type=Path, required=True)
    parser.add_argument("--execute-synthetic-only", action="store_true")
    args = parser.parse_args(argv)
    report = run_native(args.hae_root, args.la_package, args.execute_synthetic_only)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["native_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
