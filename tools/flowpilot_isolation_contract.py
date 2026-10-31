"""G117 Docker smoke-test contract for an *optional* owner-approved LOCAL runner.

Never executes a workflow, NAS API or arbitrary AI-generated code. Without
explicit approval only emits/validates an argv plan. A successful container
smoke check is NOT proof of safe NAS access or a Uliya Skill capability.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile

from flowpilot_task_compiler import compile_goal

_IMAGE = re.compile(r"(?:docker\.io/library/)?python@sha256:[0-9a-f]{64}\Z")
_MARKER = "FLOWPILOT_DISPOSABLE_CONTAINER_SMOKE_V1"
_SCRIPT = (
    "import json,os;"
    "print(json.dumps({'marker':'FLOWPILOT_DISPOSABLE_CONTAINER_SMOKE_V1',"
    "'nonroot':os.getuid()!=0,'python':True},sort_keys=True))"
)


def _local_socket_ready() -> bool:
    """Do not inherit Docker contexts/remote endpoints from the caller."""
    path = "/var/run/docker.sock"
    try:
        return (os.name == "posix" and not os.path.islink(path)
                and stat.S_ISSOCK(os.stat(path).st_mode))
    except (OSError, ValueError):
        return False


def plan_sandbox(goal: str, image: str) -> dict:
    """Build fixed CLI arguments for a pinned, already-local Python image.

    Image content trust, Docker daemon trust and actual host policy still need
    separate real-system verification. This function launches nothing.
    """
    compiled = compile_goal(goal)
    if compiled.get("status") != "READY_FOR_SYNTHETIC_TEST":
        return {"status": "BLOCKED_UNSUPPORTED_GOAL", "docker_launched": False,
                "nas_verified": False, "release_gate": "HOLD"}
    if type(image) is not str or _IMAGE.fullmatch(image) is None:
        return {"status": "BLOCKED_UNPINNED_IMAGE", "docker_launched": False,
                "nas_verified": False, "release_gate": "HOLD"}
    argv = [
        "docker", "--host=unix:///var/run/docker.sock", "run", "--rm", "--pull=never",
        "--network=none", "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=32",
        "--memory=128m", "--cpus=0.5", "--user=65534:65534",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=16m", "--workdir=/tmp",
        "--entrypoint=/usr/local/bin/python3",
        image, "-I", "-B", "-c", _SCRIPT,
    ]
    return {
        "schema": "flowpilot-docker-smoke-contract-v1",
        "status": "WAITING_LOCAL_DOCKER_APPROVAL",
        "template": compiled["template"],
        "argv": argv,
        "preconditions": [
            "APPROVED_LOCAL_DOCKER_DAEMON_ONLY",
            "PINNED_TRUSTED_PYTHON_IMAGE_ALREADY_PRESENT",
            "NO_NAS_MOUNTS_OR_CUSTOMER_DATA",
            "NO_NETWORK_OR_IMAGE_PULL",
            "NO_HOST_DOCKER_SOCKET_MOUNT",
            "NO_ARBITRARY_CODE_OR_WORKFLOW_EXECUTION",
        ],
        "docker_launched": False, "nas_verified": False,
        "registered_expert_verified": False, "release_gate": "HOLD",
    }


def run_local_smoke(goal: str, image: str, *, approved: bool = False) -> dict:
    """Execute only the fixed smoke check, never a generated workflow.

    No execution without explicit per-call approval. The argv is fixed by us
    and cannot accept arbitrary extra switches, mounts, shell or env vars.
    """
    if type(approved) is not bool:
        raise ValueError("Approval type invalid")
    plan = plan_sandbox(goal, image)
    if plan["status"] != "WAITING_LOCAL_DOCKER_APPROVAL":
        return plan
    if not approved:
        return plan
    binary = shutil.which("docker")
    if not binary or not _local_socket_ready():
        return {
            "status": "LOCAL_DOCKER_NOT_AVAILABLE", "docker_launched": False,
            "nas_verified": False, "release_gate": "HOLD",
        }
    cmd = [binary, *plan["argv"][1:]]
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-docker-cli-") as config:
            # A fresh Docker config prevents use of the owner\'s auth, plugins or
            # named remote context; --host pins the local Unix daemon socket.
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                   "HOME": config, "DOCKER_CONFIG": config,
                   "DOCKER_HOST": "unix:///var/run/docker.sock"}
            run = subprocess.run(cmd, shell=False, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 timeout=15, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "LOCAL_DOCKER_SMOKE_FAILED",
                "docker_launched": False, "nas_verified": False,
                "release_gate": "HOLD"}
    try:
        receipt = json.loads(run.stdout.strip()) if run.returncode == 0 else {}
    except (ValueError, TypeError):
        receipt = {}
    if (type(receipt) is dict and
            receipt == {"marker": _MARKER, "nonroot": True, "python": True}):
        status = "LOCAL_DOCKER_SMOKE_PASS_NOT_NAS"
    else:
        status = "LOCAL_DOCKER_SMOKE_FAILED"
    return {
        "status": status, "docker_launched": True,
        "container_sandbox_executed": status == "LOCAL_DOCKER_SMOKE_PASS_NOT_NAS",
        "actual_workflow_executed_in_docker": False,
        "docker_host_isolation_independently_verified": False,
        "nas_verified": False, "registered_expert_verified": False,
        "image_provenance_independently_verified": False,
        "production_applied": False, "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pinned local Docker smoke plan, NOT NAS")
    p.add_argument("--goal", required=True)
    p.add_argument("--image", required=True,
                   help="Already-local trusted python@sha256:<64 hex> image")
    p.add_argument("--approve-local-docker-smoke", action="store_true",
                   help="Explicitly launch one fixed local smoke check")
    args = p.parse_args(argv)
    result = run_local_smoke(args.goal, args.image,
                             approved=args.approve_local_docker_smoke)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] in ("WAITING_LOCAL_DOCKER_APPROVAL",
                                     "LOCAL_DOCKER_SMOKE_PASS_NOT_NAS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
