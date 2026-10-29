"""Opt-in smoke for UGREEN ↔ a trusted local HAE Lightning Azent checkout.

Usage:
  python tools/verify_la_runtime_bridge.py --la-package-root PATH_TO_HAE/packages/lightning-azent
This executes only a synthetic literal workflow in disposable temporary SQLite.
It does NOT access NAS, external APIs, customer files, or a real Uliya Expert.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrations.la_bridge import preflight_la, read_la_audit, inspect_la_capabilities

REQUEST = {
    "intent": "CHECK_REQUIRED", "folder": "synthetic-test-only",
    "required_paths": ["README.md"], "owner_approved_metadata": True,
    "runtime_permissions_verified": True, "processing_location_accepted": True,
}
PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "synthetic", "op": "literal", "value": {"check": "ok"}}
]}
WRITE_PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "source", "op": "literal", "value": {"tag": "ugreen-private-sentinel"}},
    {"id": "store", "op": "sqlite_put", "from": "source"},
]}


def verify(package_root: Path) -> dict[str, object]:
    package_root = package_root.resolve(strict=True)
    if not package_root.is_dir() or not (package_root / "lightning_azent" / "runtime.py").is_file():
        raise ValueError("supply a trusted Lightning Azent package source directory")
    sys.path.insert(0, str(package_root))
    from lightning_azent import LAExecutor, ApprovalRequired

    capabilities = LAExecutor.capabilities()
    if capabilities.get("api_version") != "azent.api.v0":
        raise RuntimeError("LA API version mismatch")
    with tempfile.TemporaryDirectory(prefix="ugreen-la-smoke-") as tmp:
        root = Path(tmp)
        runtime = root / "runtime.sqlite"
        business = root / "business.sqlite"
        la = LAExecutor(runtime, business)
        compatibility = inspect_la_capabilities(REQUEST, LAExecutor)
        if compatibility.get("state") != "LOCAL_PLAN_ONLY" or compatibility.get("can_read_nas") is not False:
            raise RuntimeError("LA falsely claims NAS capability")
        preview = preflight_la(REQUEST, PLAN, LAExecutor)
        if preview.get("state") != "PLAN_PREFLIGHT_ONLY" or preview["preview"]["step_count"] != 1:
            raise RuntimeError("LA plan preflight incompatible")
        if runtime.exists() or business.exists():
            raise RuntimeError("preflight unexpectedly created SQLite files")
        la.execute(PLAN, "ugreen_smoke", approve_writes=False)
        audit = read_la_audit(REQUEST, "ugreen_smoke", la)
        if audit.get("state") != "METADATA_ONLY":
            raise RuntimeError("LA metadata audit incompatible")
        if not runtime.is_file() or not business.is_file():
            raise RuntimeError("synthetic execution did not create local ledgers")
        if la.status("ugreen_smoke").get("status") != "completed":
            raise RuntimeError("synthetic literal run did not complete")

        # Exercise real LA's write-consent barrier against separate empty
        # disposable ledgers; refusal must not create either file.
        denied_state = root / "denied_runtime.sqlite"
        denied_business = root / "denied_business.sqlite"
        denied_executor = LAExecutor(denied_state, denied_business)
        denied_plan = preflight_la(REQUEST, WRITE_PLAN, LAExecutor)
        if denied_plan.get("preview", {}).get("requires_write_approval") is not True:
            raise RuntimeError("LA failed to flag the synthetic write")
        try:
            denied_executor.execute(WRITE_PLAN, "ugreen_denied", approve_writes=False)
        except ApprovalRequired:
            pass
        else:
            raise RuntimeError("LA permitted a synthetic write without approval")
        if denied_state.exists() or denied_business.exists():
            raise RuntimeError("denied synthetic write unexpectedly created ledgers")

        # Run one explicitly approved synthetic write (never owner data).
        # Verify the business ledger independently and ensure replay does not
        # repeat the write or issue a second approval receipt.
        first = la.execute(WRITE_PLAN, "ugreen_approved", approve_writes=True)
        original_audit = la.audit("ugreen_approved")
        if len(original_audit.get("approval_receipts", [])) != 1:
            raise RuntimeError("synthetic write approval receipt missing")
        if "ugreen-private-sentinel" in json.dumps(original_audit):
            raise RuntimeError("LA audit exposed synthetic workflow contents")
        approval_view = read_la_audit(REQUEST, "ugreen_approved", la)
        if approval_view.get("audit", {}).get("approval_count") != 1:
            raise RuntimeError("UGREEN redacted write audit incompatible")
        with closing(sqlite3.connect(business)) as connection:
            before_replay = connection.execute(
                "SELECT COUNT(*) FROM records WHERE run_id=? AND step_id=?",
                ("ugreen_approved", "store")
            ).fetchone()[0]
            if connection.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
                raise RuntimeError("synthetic business ledger integrity check failed")
        if before_replay != 1:
            raise RuntimeError("expected exactly one synthetic business record")
        replayed = la.execute(WRITE_PLAN, "ugreen_approved", approve_writes=True)
        if first != replayed or la.status("ugreen_approved").get("status") != "completed":
            raise RuntimeError("LA synthetic idempotent replay mismatch")
        replay_audit = la.audit("ugreen_approved")
        if (len(replay_audit.get("approval_receipts", [])) != 1
                or not replay_audit.get("events")
                or replay_audit["events"][-1].get("event_type") != "run_replayed"):
            raise RuntimeError("synthetic replay audit mismatch")
        with closing(sqlite3.connect(business)) as connection:
            after_replay = connection.execute(
                "SELECT COUNT(*) FROM records WHERE run_id=? AND step_id=?",
                ("ugreen_approved", "store")
            ).fetchone()[0]
        if after_replay != before_replay:
            raise RuntimeError("synthetic replay duplicated a business write")
        return {
            "result": "PASS", "scope": "disposable-synthetic-local-only",
            "plan_preflight": preview["state"], "audit": audit["state"],
            "events": audit["audit"]["event_count"],
            "approval_receipts": approval_view["audit"]["approval_count"],
            "denied_write_created_db": False,
            "approved_synthetic_write_rows": after_replay,
            "replay_duplicate_writes": 0,
            "nas": "NOT_TESTED", "uliya_experts": "NOT_TESTED",
            "la_capabilities": compatibility["state"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline UGREEN-LA integration verification")
    parser.add_argument("--la-package-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.la_package_root), ensure_ascii=False, sort_keys=True))
    except (Exception) as error:
        print(json.dumps({"result": "FAIL", "reason": type(error).__name__,
                          "nas": "NOT_TESTED"}, sort_keys=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
