"""Optional, fail-closed Lightning Azent runtime preflight for FlowPilot 3.0.

Calls only the owner's installed local package capabilities() and preflight()
on one fixed synthetic literal. Never executes an engine, opens user data,
writes SQLite, contacts NAS, or bundles private HAE source into the public
UGREEN repository. A contract handshake is not E2E integration proof.
"""
from __future__ import annotations

import argparse
from importlib import import_module
import json

from flowpilot_la_capabilities import FLOWPILOT_LOCAL_TYPES

PROBE_PLAN = {
    "version": "azent.ir.v0",
    "steps": [{"id": "probe", "op": "literal", "value": "synthetic-only"}],
}


def _result(status: str, *, imported: bool = False, capabilities_called: bool = False,
            preflight_called: bool = False, supported: set[str] | None = None) -> dict:
    supported = supported or set()
    return {
        "schema": "flowpilot-la-installed-runtime-probe-v1",
        "status": status,
        "scope": "LOCAL_INSTALLED_PACKAGE_ONLY_NOT_NAS",
        "required_operations": sorted(FLOWPILOT_LOCAL_TYPES),
        "supported_operations": sorted(supported),
        "missing_operations": sorted(FLOWPILOT_LOCAL_TYPES - supported),
        "installed_la_module_imported": imported,
        "installed_la_capabilities_called": capabilities_called,
        "installed_la_preflight_called": preflight_called,
        "actual_la_workflow_executed": False,
        "hae_application_called": False,
        "sovia_called": False,
        "dbvora_called": False,
        "uliya_or_nas_called": False,
        "execution_allowed": False,
        "release_gate": "HOLD",
    }


def probe_installed_la(*, loader=import_module) -> dict:
    """Inspect exact installed v0 metadata only; never call execute or open files.

    A synthetic test loader proves this adapter's branch logic, not that the
    private Lightning Azent runtime is installed or executing successfully.
    """
    try:
        package = loader("lightning_azent")
    except ImportError:
        return _result("BLOCKED_RUNTIME_UNAVAILABLE")
    except Exception:
        return _result("BLOCKED_RUNTIME_CONTRACT")

    executor = getattr(package, "LAExecutor", None)
    if executor is None or not callable(getattr(executor, "capabilities", None)):
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True)

    try:
        capabilities = executor.capabilities()
    except Exception:
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True, capabilities_called=True)
    if not isinstance(capabilities, dict):
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True, capabilities_called=True)
    operations = capabilities.get("implemented_operations")
    valid_ops = (isinstance(operations, list)
                 and all(isinstance(item, str) for item in operations)
                 and len(operations) == len(set(operations)))
    if (capabilities.get("api_version") != "azent.api.v0"
            or capabilities.get("native_ir_version") != "azent.ir.v0"
            or capabilities.get("legacy_ir_version") != "axflow.ir.v0"
            or capabilities.get("scope") != "synthetic-local-only"
            or capabilities.get("external_connectors") != []
            or not valid_ops):
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True, capabilities_called=True)
    supported = set(operations)
    if not callable(getattr(executor, "preflight", None)):
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True, capabilities_called=True,
                       supported=supported)
    try:
        preview = executor.preflight(PROBE_PLAN)
    except Exception:
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True,
                       capabilities_called=True, preflight_called=True, supported=supported)
    if (not isinstance(preview, dict)
            or preview.get("source_version") != "azent.ir.v0"
            or preview.get("runtime_version") != "axflow.ir.v0"
            or preview.get("step_count") != 1
            or preview.get("requires_write_approval") is not False
            or preview.get("requires_input_root") is not False
            or preview.get("executes_workflow") is not False
            or preview.get("scope") != "synthetic-local-only"):
        return _result("BLOCKED_RUNTIME_CONTRACT", imported=True,
                       capabilities_called=True, preflight_called=True, supported=supported)
    return _result(
        "BLOCKED_MISSING_OPERATIONS" if FLOWPILOT_LOCAL_TYPES - supported
        else "PREFLIGHT_COMPATIBLE_NOT_EXECUTED",
        imported=True, capabilities_called=True,
        preflight_called=True, supported=supported,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local Lightning Azent capability probe; no workflows or NAS execution"
    )
    parser.parse_args(argv)
    result = probe_installed_la()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PREFLIGHT_COMPATIBLE_NOT_EXECUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
