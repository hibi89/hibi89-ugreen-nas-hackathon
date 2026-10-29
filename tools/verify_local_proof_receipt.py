"""Inspect the owner-provided synthetic E2E proof from a bounded JSON file.

This validates contract consistency, not authenticity of an external command.
It prints only the allowlisted, redacted classification or a stable error code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from integrations.local_proof_receipt import (
    ReceiptRejected, validate_owner_reported_local_proof
)

DEFAULT = (PROJECT / "integrations" / "evidence" /
           "owner_reported_local_e2e_20261030.json")
MAX_JSON_BYTES = 8192


def inspect_report(path: Path) -> dict:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise ReceiptRejected("EVIDENCE_UNREADABLE") from exc
    if not 0 < len(data) <= MAX_JSON_BYTES:
        raise ReceiptRejected("EVIDENCE_SIZE_INVALID")
    try:
        report = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ReceiptRejected("EVIDENCE_JSON_INVALID") from exc
    return validate_owner_reported_local_proof(report)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate owner-reported synthetic LA/SOVIA proof, never NAS"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT)
    args = parser.parse_args(argv)
    try:
        classified = inspect_report(args.input)
    except ReceiptRejected as exc:
        print(json.dumps({
            "result": "REJECTED",
            "error_code": str(exc),
            "release_gate": "HOLD",
            "actual_nas_verified": False,
        }, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(classified, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
