"""G146: real isolated Docker execution for one hardcoded synthetic CSV workflow.

No caller-controlled code, files, image pulls, owner mounts, NAS or Uliya APIs.
A single missing canonical DAG edge can be repaired exactly once in a temporary
fixture. Successful fixture work does NOT imply a general LLM self-healing agent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from flowpilot_isolation_contract import _local_socket_ready, plan_sandbox

_MARKER = "FLOWPILOT_SYNTHETIC_CONTAINER_WORKFLOW_V1"
_SOURCE_SHA = "c3b7ea52e4530b303879608b302e38ff23b989b91e349815f734e7915d518bb9"
_OUTPUT_SHA = "085540323a3b8895631b2f8de0531e94e78bbc15bf9ed44a0e3d2a6329676123"
_EXPECTED = {
    "marker": _MARKER, "initial_plan": "REJECTED_MISSING_EDGE",
    "repair_count": 1, "retest": "PASS",
    "fixture_rows": 3, "output_rows": 2, "sqlite_rows": 2,
    "source_sha256": _SOURCE_SHA, "output_sha256": _OUTPUT_SHA,
    "source_unchanged": True, "raw_user_data_used": False,
}
# Executed literally by the fixed interpreter in a no-network, no-mount Docker.
# This script contains every fixture byte; no host code or user files enter it.
_WORKFLOW_SCRIPT = r'''
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile

MARKER = "FLOWPILOT_SYNTHETIC_CONTAINER_WORKFLOW_V1"
SOURCE = b"customer,amount\nalice,1.25\nbob,3.00\nalice,2.75\n"
SOURCE_SHA = "c3b7ea52e4530b303879608b302e38ff23b989b91e349815f734e7915d518bb9"
OUTPUT_SHA = "085540323a3b8895631b2f8de0531e94e78bbc15bf9ed44a0e3d2a6329676123"
STEPS = ("read", "aggregate", "output", "audit")
EDGES = (("read", "aggregate"), ("aggregate", "output"), ("output", "audit"))

def valid(plan):
    return (type(plan) is dict and plan.get("steps") == STEPS
            and plan.get("edges") == EDGES
            and plan.get("runtime") == "synthetic_container_only")

def repair_missing_last_edge(plan):
    # Exactly one allowlisted in-memory graph repair. Never edit generated code.
    if (type(plan) is not dict or plan.get("steps") != STEPS
            or plan.get("runtime") != "synthetic_container_only"
            or plan.get("edges") != EDGES[:-1]):
        return None
    return {"steps": STEPS, "edges": EDGES, "runtime": "synthetic_container_only"}

proposal = {"steps": STEPS, "edges": EDGES[:-1],
            "runtime": "synthetic_container_only"}
assert not valid(proposal), "Deliberate missing edge was not refused"
repaired = repair_missing_last_edge(proposal)
assert repaired is not None and valid(repaired), "Exact one-edge repair failed"

with tempfile.TemporaryDirectory(dir="/tmp", prefix="fp146-") as tmp:
    base = Path(tmp)
    source = base / "synthetic-source.csv"
    source.write_bytes(SOURCE)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    with source.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ["customer", "amount"]
        rows = list(reader)
    assert len(rows) == 3
    sums = {}
    for row in rows:
        assert set(row) == {"customer", "amount"}
        assert row["customer"] in ("alice", "bob")
        value = Decimal(row["amount"])
        assert value.is_finite() and value >= 0
        sums[row["customer"]] = sums.get(row["customer"], Decimal("0")) + value
    assert sorted(sums) == ["alice", "bob"]
    output = base / "totals.csv"
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["customer", "total"])
        for customer in sorted(sums):
            writer.writerow([customer, format(sums[customer].quantize(Decimal("0.01")), ".2f")])
    output_bytes = output.read_bytes()
    assert hashlib.sha256(output_bytes).hexdigest() == OUTPUT_SHA
    assert output_bytes == b"customer,total\nalice,4.00\nbob,3.00\n"
    dbfile = base / "audit.sqlite3"
    with sqlite3.connect(dbfile) as db:
        db.execute("CREATE TABLE audit (customer TEXT PRIMARY KEY, total TEXT NOT NULL)")
        for customer in sorted(sums):
            db.execute("INSERT INTO audit VALUES (?,?)",
                       (customer, format(sums[customer], ".2f")))
        db.commit()
        saved = db.execute("SELECT customer,total FROM audit ORDER BY customer").fetchall()
    assert saved == [("alice", "4.00"), ("bob", "3.00")]
    untouched = hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    assert untouched
    result = {
        "marker": MARKER, "initial_plan": "REJECTED_MISSING_EDGE",
        "repair_count": 1, "retest": "PASS",
        "fixture_rows": len(rows), "output_rows": len(sums), "sqlite_rows": len(saved),
        "source_sha256": SOURCE_SHA, "output_sha256": OUTPUT_SHA,
        "source_unchanged": untouched, "raw_user_data_used": False,
    }
    print(json.dumps(result, sort_keys=True))
'''


def _report(status: str, *, executed: bool = False, passed: bool = False) -> dict:
    return {
        "schema": "flowpilot-real-docker-fixture-v1",
        "status": status, "docker_launched": executed,
        "actual_synthetic_workflow_executed_in_docker": passed,
        "bounded_synthetic_edge_repair_verified": passed,
        "actual_customer_workflow_executed": False,
        "arbitrary_llm_code_repair_verified": False,
        "owner_files_opened": False, "customer_files_mounted": False,
        "external_api_called_by_fixture": False,
        "registered_uliya_expert_verified": False,
        "nas_verified": False, "production_applied": False,
        "release_gate": "HOLD",
    }


def plan_workflow(goal: str, image: str) -> dict:
    p = plan_sandbox(goal, image)
    if p.get("status") != "WAITING_LOCAL_DOCKER_APPROVAL":
        return _report("INVALID_OR_UNSUPPORTED_PLAN")
    if p.get("template") != "csv_customer_revenue_v1":
        return _report("UNSUPPORTED_WORKFLOW_TEMPLATE")
    argv = p["argv"].copy()
    assert argv[-3:-1] == ["-c", argv[-1]] or argv[-2] == "-c"
    argv[-1] = _WORKFLOW_SCRIPT
    return {**_report("WAITING_LOCAL_DOCKER_APPROVAL"),
            "argv": argv, "template": "csv_customer_revenue_v1"}


def run_workflow(goal: str, image: str, *, approved: bool = False) -> dict:
    if type(approved) is not bool:
        raise ValueError("Approval must be explicit boolean")
    p = plan_workflow(goal, image)
    if p["status"] != "WAITING_LOCAL_DOCKER_APPROVAL" or not approved:
        return {k: v for k, v in p.items() if k != "argv"}
    binary = shutil.which("docker")
    if not binary or not _local_socket_ready():
        return _report("LOCAL_DOCKER_NOT_AVAILABLE")
    cmd = [binary, *p["argv"][1:]]
    try:
        with tempfile.TemporaryDirectory(prefix="fp146-docker-config-") as config:
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                   "HOME": config, "DOCKER_CONFIG": config,
                   "DOCKER_HOST": "unix:///var/run/docker.sock"}
            res = subprocess.run(cmd, shell=False, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 timeout=25, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return _report("LOCAL_DOCKER_WORKFLOW_FAILED")
    if res.returncode != 0 or res.stderr.strip() or len(res.stdout) > 4096:
        return _report("LOCAL_DOCKER_WORKFLOW_FAILED", executed=True)
    try:
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj:
                    raise ValueError("Duplicate receipt key")
                obj[k] = v
            return obj
        receipt = json.loads(res.stdout, object_pairs_hook=unique)
    except (ValueError, RecursionError):
        receipt = None
    if (type(receipt) is dict and
            set(receipt) == set(_EXPECTED) and
            all(type(receipt[k]) is type(v) and receipt[k] == v
                for k, v in _EXPECTED.items())):
        return _report("LOCAL_DOCKER_SYNTHETIC_REPAIR_WORKFLOW_PASS",
                       executed=True, passed=True)
    return _report("LOCAL_DOCKER_WORKFLOW_FAILED", executed=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="REAL synthetic workflow in isolated Docker; NOT NAS")
    p.add_argument("--goal", required=True)
    p.add_argument("--image", required=True, help="Already locally fetched immutable Docker digest")
    p.add_argument("--approve-local-docker-workflow", action="store_true")
    a = p.parse_args(argv)
    result = run_workflow(a.goal, a.image, approved=a.approve_local_docker_workflow)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in (
        "WAITING_LOCAL_DOCKER_APPROVAL",
        "LOCAL_DOCKER_SYNTHETIC_REPAIR_WORKFLOW_PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
