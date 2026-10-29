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
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrations.la_bridge import preflight_la, read_la_audit

REQUEST = {
    "intent": "CHECK_REQUIRED", "folder": "synthetic-test-only",
    "required_paths": ["README.md"], "owner_approved_metadata": True,
    "runtime_permissions_verified": True, "processing_location_accepted": True,
}
PLAN = {"version": "azent.ir.v0", "steps": [
    {"id": "synthetic", "op": "literal", "value": {"check": "ok"}}
]}


def verify(package_root: Path) -> dict[str, object]:
    package_root = package_root.resolve(strict=True)
    if not package_root.is_dir() or not (package_root / "lightning_azent" / "runtime.py").is_file():
        raise ValueError("supply a trusted Lightning Azent package source directory")
    sys.path.insert(0, str(package_root))
    from lightning_azent import LAExecutor

    capabilities = LAExecutor.capabilities()
    if capabilities.get("api_version") != "azent.api.v0":
        raise RuntimeError("LA API version mismatch")
    with tempfile.TemporaryDirectory(prefix="ugreen-la-smoke-") as tmp:
        root = Path(tmp)
        runtime = root / "runtime.sqlite"
        business = root / "business.sqlite"
        la = LAExecutor(runtime, business)
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
        return {
            "result": "PASS", "scope": "disposable-synthetic-local-only",
            "plan_preflight": preview["state"], "audit": audit["state"],
            "events": audit["audit"]["event_count"],
            "approval_receipts": audit["audit"]["approval_count"],
            "nas": "NOT_TESTED", "uliya_experts": "NOT_TESTED",
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
