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
        proc = subprocess.run(
            [sys.executable, str(runner),
             "--la-package", str(la_package),
             "--ugreen-root", str(UGREEN_ROOT),
             "--execute-synthetic-only"],
            cwd=str(hae_root), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=120, check=False,
        )
        output = json.loads(proc.stdout.strip())
        if not isinstance(output, dict):
            raise ValueError("unexpected report type")
        if proc.returncode == 0 and output.get("status") == PASS:
            return {
                "status": "G85_UGREEN_NATIVE_BACKEND_E2E_PASS",
                "native_verified": True,
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
