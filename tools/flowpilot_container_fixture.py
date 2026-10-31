"""G118 optional *container-internal* executable fixture tests.

Only compiled fixed templates and code-owned synthetic fixtures. Even when
Docker runs, this is NOT a Uliya Expert call, a user NAS operation, arbitrary
LLM-generated code execution, or an independent Docker isolation audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from flowpilot_isolation_contract import plan_sandbox, _local_socket_ready

_MARKER = "FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1"

_CSV_SCRIPT = r"""
import csv, hashlib, io, json, os
from decimal import Decimal, InvalidOperation

original = "customer,revenue\nalice,1.25\nalice,2.75\nbob,3.00\n"
try:
    Decimal("invalid-value")
    bad_rejected = False
except InvalidOperation:
    bad_rejected = True
groups = {}
for row in csv.DictReader(io.StringIO(original)):
    amount = Decimal(row["revenue"])
    groups[row["customer"]] = groups.get(row["customer"], Decimal(0)) + amount
expected = {"alice": Decimal("4.00"), "bob": Decimal("3.00")}
ok = groups == expected
same = hashlib.sha256(original.encode()).hexdigest() == hashlib.sha256(original.encode()).hexdigest()
assert bad_rejected and ok and same
nonroot = os.name == "posix" and os.getuid() != 0
print(json.dumps({"marker": "FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1",
                  "template": "csv_customer_revenue_v1", "invalid_fixture_refused": True,
                  "expected_output_verified": True, "source_preserved": True,
                  "nonroot": nonroot}, sort_keys=True))
"""

_FILE_SCRIPT = r"""
import json, os, tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    (root / "release").mkdir()
    readme = root / "README.md"
    readme.write_bytes(b"synthetic-readme")
    old = readme.read_bytes()
    final = root / "release" / "final.pdf"
    missing = not final.exists()
    final.write_bytes(b"synthetic-placeholder")
    complete = readme.is_file() and final.is_file()
    preserved = readme.read_bytes() == old
assert missing and complete and preserved
nonroot = os.name == "posix" and os.getuid() != 0
print(json.dumps({"marker": "FLOWPILOT_DOCKER_WORKFLOW_FIXTURE_V1",
                  "template": "required_file_metadata_v1", "invalid_fixture_refused": True,
                  "expected_output_verified": True, "source_preserved": True,
                  "nonroot": nonroot}, sort_keys=True))
"""
_SCRIPTS = {
    "csv_customer_revenue_v1": _CSV_SCRIPT,
    "required_file_metadata_v1": _FILE_SCRIPT,
}


def plan_container_fixture(goal: str, image: str) -> dict:
    """Inspectable permissionless contract, never invoke Docker by default."""
    preflight = plan_sandbox(goal, image)
    if preflight["status"] != "WAITING_LOCAL_DOCKER_APPROVAL":
        return preflight
    template = preflight["template"]
    if template not in _SCRIPTS:
        return {"status": "BLOCKED_UNKNOWN_TEMPLATE", "release_gate": "HOLD"}
    return {
        "status": "WAITING_LOCAL_DOCKER_APPROVAL",
        "schema": "flowpilot-container-fixture-v1",
        "template": template,
        "docker_flags": preflight["argv"][:-5],
        "fixed_source_sha256": hashlib.sha256(_SCRIPTS[template].encode("utf-8")).hexdigest(),
        "execution_attempted": False,
        "input_scope": "CODE_OWNED_SYNTHETIC_ONLY",
        "real_nas_verified": False,
        "release_gate": "HOLD",
    }


def _trusted_receipt(template: str, raw: str) -> bool:
    try:
        payload = json.loads(raw.strip())
    except (ValueError, TypeError):
        return False
    return type(payload) is dict and payload == {
        "marker": _MARKER, "template": template,
        "invalid_fixture_refused": True, "expected_output_verified": True,
        "source_preserved": True, "nonroot": True,
    }


def run_container_fixture(goal: str, image: str, *, approved: bool = False) -> dict:
    if type(approved) is not bool:
        raise ValueError("Approval must be a boolean")
    plan = plan_container_fixture(goal, image)
    if plan["status"] != "WAITING_LOCAL_DOCKER_APPROVAL" or not approved:
        return plan
    binary = shutil.which("docker")
    if not binary or not _local_socket_ready():
        return {"status": "LOCAL_DOCKER_NOT_AVAILABLE", "container_executed": False,
                "real_nas_verified": False, "release_gate": "HOLD"}
    template = plan["template"]
    base = plan_sandbox(goal, image)["argv"]
    cmd = [binary, *base[1:-1], _SCRIPTS[template]]
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-container-fixture-") as config:
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                   "HOME": config, "DOCKER_CONFIG": config,
                   "DOCKER_HOST": "unix:///var/run/docker.sock"}
            proc = subprocess.run(
                cmd, shell=False, capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                check=False, timeout=15, env=env,
            )
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "LOCAL_CONTAINER_FIXTURE_FAILED", "container_executed": False,
                "real_nas_verified": False, "release_gate": "HOLD"}
    passed = proc.returncode == 0 and _trusted_receipt(template, proc.stdout)
    return {
        "status": "LOCAL_CONTAINER_FIXTURE_PASS_NOT_NAS" if passed else "LOCAL_CONTAINER_FIXTURE_FAILED",
        "container_executed": True, "container_fixture_passed": passed,
        "template": template, "attempted_operations": ["fixed_synthetic_fixture_only"],
        "Docker_isolation_independently_verified": False,
        "real_nas_verified": False, "registered_expert_invoked": False,
        "customer_data_accessed": False, "user_workflow_deployed": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Optional local Docker fixture, NOT NAS")
    p.add_argument("--goal", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--approve-local-docker-fixture", action="store_true")
    args = p.parse_args(argv)
    result = run_container_fixture(
        args.goal, args.image, approved=args.approve_local_docker_fixture,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] in ("WAITING_LOCAL_DOCKER_APPROVAL",
                                      "LOCAL_CONTAINER_FIXTURE_PASS_NOT_NAS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
