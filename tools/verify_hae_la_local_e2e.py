"""G81 owner-local one-command REAL HAE .pyz -> LA -> SQLite acceptance.

Runs a SHA-pinned owner-selected existing HAE zipapp as imported Python code,
not its installer or launcher. All input and databases are temporary synthetic
fixtures. No NAS, external service, credentials, third-party payment, originals,
customer data or Devpost. Does not copy private code into the public repository.

Requires explicit --execute-synthetic-only because importing a zipapp executes
the package's import-time Python code. Never silently select a binary.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
import importlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from tempfile import TemporaryDirectory
import threading

from flowpilot_hae_bridge import APPROVAL, run_bridge, _request, reconcile_run

SHA = re.compile(r"^[a-f0-9]{64}$")
FIXTURE = b"id,name\n11,SyntheticAlice\n12,SyntheticBob\n"
TASK = "Import this CSV into local SQLite"


class AcceptanceRefused(ValueError):
    """Local acceptance requirements not satisfied."""


def validate_binary(path: Path, expected: str, confirmed: bool) -> tuple[Path, str]:
    if confirmed is not True:
        raise AcceptanceRefused("Explicit synthetic owner-run approval missing")
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise AcceptanceRefused("Expected 64-character SHA256 required")
    if (path.is_symlink() or not path.is_file() or path.suffix.lower() != ".pyz"
            or not 1000 <= path.stat().st_size <= 10_000_000):
        raise AcceptanceRefused("Existing regular bounded .pyz required")
    actual = sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise AcceptanceRefused("Owner-provided zipapp SHA256 does not match")
    if sys.version_info < (3, 11):
        raise AcceptanceRefused("Python 3.11+ required")
    return path.resolve(strict=True), actual


def run_acceptance(hae_zipapp: Path, expected_sha: str, *,
                   execute_synthetic_only: bool = False) -> dict:
    binary, digest = validate_binary(
        hae_zipapp, expected_sha, execute_synthetic_only)
    sys.path.insert(0, str(binary))
    try:
        axflow = importlib.import_module("axflow.web")
        la = importlib.import_module("lightning_azent")
        if not str(getattr(axflow, "__file__", "")).startswith(str(binary)):
            raise AcceptanceRefused("HAE module was not loaded from the pinned archive")
        if not str(getattr(la, "__file__", "")).startswith(str(binary)):
            raise AcceptanceRefused("LA module was not loaded from the pinned archive")
        create_server = axflow.create_server
        with TemporaryDirectory(prefix="ugreen-hae-real-synthetic-") as temp:
            base = Path(temp)
            input_root = base / "input"
            input_root.mkdir()
            source = input_root / "contacts.csv"
            source.write_bytes(FIXTURE)
            state = base / "runtime.sqlite"
            business = base / "business.sqlite"
            server = create_server(
                input_root, state, business, port=0,
                engine_backend="lightning-azent",
            )
            worker = threading.Thread(
                target=server.serve_forever,
                kwargs={"poll_interval": 0.01}, daemon=True)
            worker.start()
            try:
                port = server.server_port
                opts = {"csv_path": "contacts.csv", "port": port,
                        "confirm_synthetic": True}
                first = run_bridge(TASK, **opts)
                if first["status"] != "WAITING_HAE_WRITE_APPROVAL":
                    raise AcceptanceRefused("Real HAE preview did not validate")
                if state.exists() or business.exists():
                    raise AcceptanceRefused("Preview unexpectedly wrote SQLite")
                declined = run_bridge(
                    TASK, approval="DECLINED", preview_id=first["preview_id"], **opts)
                if declined["status"] != "DECLINED" or business.exists():
                    raise AcceptanceRefused("Declined execution changed SQLite")
                executed = run_bridge(
                    TASK, approval=APPROVAL, preview_id=first["preview_id"], **opts)
                if (executed["status"] != "HAE_LA_SQLITE_AUDIT_CONFIRMED"
                        or executed["imported_rows"] != 2):
                    raise AcceptanceRefused("HAE/LA exact runtime audit not confirmed")
                with closing(sqlite3.connect(business)) as connection:
                    count = connection.execute("SELECT COUNT(*) FROM csv_records").fetchone()[0]
                if count != 2:
                    raise AcceptanceRefused("HAE LA business SQLite row count differs")
                run_id = executed["run_id"]
                code, status = _request(port, "GET", f"/api/status?run_id={run_id}")
                if code != 200 or status.get("status") != "completed":
                    raise AcceptanceRefused("HAE persistent run status mismatch")
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()

            # Restart actual server on same *temporary* state and verify
            # persisted LA audit; never rerun a write during recovery.
            server = create_server(
                input_root, state, business, port=0,
                engine_backend="lightning-azent",
            )
            worker = threading.Thread(
                target=server.serve_forever, kwargs={"poll_interval": 0.01},
                daemon=True)
            worker.start()
            try:
                port = server.server_port
                code, status = _request(port, "GET", f"/api/status?run_id={run_id}")
                code2, audit = _request(port, "GET", f"/api/la-audit?run_id={run_id}")
                if (code != 200 or status.get("status") != "completed"
                        or code2 != 200 or audit.get("run_id") != run_id
                        or type(audit.get("total_events")) is not int
                        or audit["total_events"] < 2):
                    raise AcceptanceRefused("Restarted LA run/audit mismatch")
                with closing(sqlite3.connect(business)) as connection:
                    count_after = connection.execute(
                        "SELECT COUNT(*) FROM csv_records").fetchone()[0]
                if count_after != 2:
                    raise AcceptanceRefused("Restart changed business SQLite")
                read_only = reconcile_run(
                    port, run_id, confirm_synthetic=True)
                if (read_only["status"] != "HAE_LA_AUDIT_RECONCILED"
                        or not read_only["do_not_retry_automatically"]
                        or read_only["actual_la_execution_verified"] is not False):
                    raise AcceptanceRefused("Read-only audit recovery did not validate")
                with closing(sqlite3.connect(business)) as connection:
                    after_read_only = connection.execute(
                        "SELECT COUNT(*) FROM csv_records").fetchone()[0]
                if after_read_only != 2:
                    raise AcceptanceRefused("Read-only recovery changed SQLite")
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()
        if sha256(binary.read_bytes()).hexdigest() != digest:
            raise AcceptanceRefused("Zipapp changed during isolated test")
        return {
            "status": "REAL_HAE_LA_LOCAL_SYNTHETIC_E2E_PASS",
            "steps_passed": 5, "steps_failed": 0,
            "hae_binary_sha256": digest, "live_hae_http": True,
            "real_la_engine": True, "sqlite_business_rows": 2,
            "la_audit_persisted_after_restart": True,
            "read_only_recovery_no_duplicate_write": True,
            "source_originals_modified": False,
            "nas_verified": False, "uliya_verified": False,
            "devpost_submitted": False, "release_gate": "HOLD",
        }
    finally:
        sys.path.remove(str(binary))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run pinned genuine HAE+LA synthetic acceptance locally; never NAS")
    parser.add_argument("--hae-zipapp", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--execute-synthetic-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_acceptance(
            args.hae_zipapp, args.sha256,
            execute_synthetic_only=args.execute_synthetic_only,
        )
    except (AcceptanceRefused, OSError, ValueError, ImportError, AttributeError):
        result = {"status": "REAL_HAE_LA_ACCEPTANCE_BLOCKED",
                  "release_gate": "HOLD", "nas_verified": False,
                  "devpost_submitted": False}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "REAL_HAE_LA_LOCAL_SYNTHETIC_E2E_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
