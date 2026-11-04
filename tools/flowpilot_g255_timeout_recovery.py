"""G255 real *stalled* Docker process recovery, unlike G237/G253 error exits.

A code-owned, sleep-only C fixture stalls inside a disconnected scratch image.
The Docker wait CLI must truly time out (distinct exception), then only the
invocation-owned container is killed, verified EXIT 137, removed. A fresh
immutable code-owned healthy image runs the exact G235 typed DAG and receipt.
No general process repair, owner data, NAS, external commands or auto retries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import tempfile

from flowpilot_g233_real_docker_smoke import (
    SmokeRefused, SmokeTimedOut, checked_run, inspect
)
from flowpilot_g235_typed_dag_docker import (
    C_SOURCE, DOCKERFILE_TYPED, PLAN, SOURCE, verify_output
)

SCHEMA = "flowpilot-g255-disconnected-docker-timeout-recovery-v1"
APPROVAL = "--approve-synthetic-timeout-recovery"
STALL_SOURCE = "#include <unistd.h>\nint main(void) { for (;;) { pause(); } }\n"
STAGES = ("stalled", "healthy")
WAIT_TIMEOUT_SECONDS = 3


def sha(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise SmokeRefused("G255_NON_BYTES_DIGEST_INPUT")
    return hashlib.sha256(raw).hexdigest()


def authorize_recovery(*, timeout_seen: object, terminated_exit: object,
                       approved: bool) -> bool:
    """Neither ordinary Docker failure nor a simulated timeout can authorize."""
    if (approved is not True or timeout_seen is not True or
            type(terminated_exit) is not int or terminated_exit != 137):
        raise SmokeRefused("G255_REQUIRED_TIMEOUT_AND_VERIFIED_KILL_MISSING")
    return True


def require_wait_terminated(raw: object) -> int:
    if type(raw) is not str or raw != "137":
        raise SmokeRefused("G255_TERMINATED_CONTAINER_EXIT_INVALID")
    return 137


def run_real_timeout_recovery() -> dict:
    if shutil.which("docker") is None or shutil.which("cc") is None:
        raise SmokeRefused("G255_LOCAL_DOCKER_OR_COMPILER_MISSING")
    checked_run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
    run_tag = secrets.token_hex(12)
    images: list[str] = []
    containers: list[str] = []
    image_ids: list[str] = []
    stalled_timeout_verified = False
    terminated_exit: int | None = None
    recovery_count = 0
    receipt: str | None = None
    binary_shas: dict[str, str] = {}
    source_sha = sha(SOURCE.encode("ascii"))
    plan_sha = sha(PLAN.encode("ascii"))
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g255-synthetic-only-") as temp:
            root = Path(temp)
            for stage in STAGES:
                if stage == "healthy" and not authorize_recovery(
                        approved=True, timeout_seen=stalled_timeout_verified,
                        terminated_exit=terminated_exit):
                    raise SmokeRefused("G255_IMPOSSIBLE_UNAPPROVED_RETEST")
                folder = root / stage
                folder.mkdir()
                program = folder / "check"
                c_source = folder / "check.c"
                c_source.write_text(
                    STALL_SOURCE if stage == "stalled" else C_SOURCE,
                    encoding="ascii")
                checked_run(["cc", "-O2", "-static", "-s", "-Wall", "-Wextra",
                             "-Werror", str(c_source), "-o", str(program)],
                            timeout=40)
                binary_shas[stage] = sha(program.read_bytes())
                program.chmod(0o755)
                (folder / "source.csv").write_bytes(SOURCE.encode("ascii"))
                (folder / "typed.plan").write_bytes(PLAN.encode("ascii"))
                (folder / "Dockerfile").write_text(
                    DOCKERFILE_TYPED, encoding="ascii")
                image = f"flowpilot-g255-{run_tag}-{stage}:local"
                if image in checked_run([
                        "docker", "image", "ls", "--filter",
                        "reference=" + image, "--format",
                        "{{.Repository}}:{{.Tag}}"], timeout=15).splitlines():
                    raise SmokeRefused("G255_IMAGE_TAG_COLLISION")
                checked_run(["docker", "build", "--pull=false", "--network=none",
                             "--no-cache", "--tag", image, str(folder)],
                            timeout=75)
                images.append(image)
                image_id = checked_run([
                    "docker", "image", "inspect", image,
                    "--format", "{{.Id}}"], timeout=15)
                if not (image_id.startswith("sha256:") and len(image_id) == 71):
                    raise SmokeRefused("G255_INVALID_LOCAL_IMAGE_DIGEST")
                image_ids.append(image_id)
                cid = checked_run([
                    "docker", "create", "--network", "none", "--read-only",
                    "--cap-drop", "ALL", "--security-opt",
                    "no-new-privileges:true", "--pids-limit", "32",
                    "--memory", "64m", "--cpus", "0.25",
                    "--user", "65534:65534", image_id], timeout=15)
                containers.append(cid)
                inspect(cid, started=False)
                if checked_run(["docker", "start", cid], timeout=15) != cid:
                    raise SmokeRefused("G255_CONTAINER_START_MISMATCH")
                if stage == "stalled":
                    # The CLI must really wait and time out: an ordinary failed
                    # Docker command or preexisting exit 137 is not evidence.
                    try:
                        checked_run(["docker", "wait", cid],
                                    timeout=WAIT_TIMEOUT_SECONDS)
                    except SmokeTimedOut:
                        stalled_timeout_verified = True
                    else:
                        raise SmokeRefused("G255_STALL_DID_NOT_TIMEOUT")
                    if checked_run([
                            "docker", "kill", "--signal=KILL", cid],
                            timeout=15) != cid:
                        raise SmokeRefused("G255_KILL_ID_MISMATCH")
                    terminated_exit = require_wait_terminated(
                        checked_run(["docker", "wait", cid], timeout=15))
                    inspect(cid, started=True,
                            expected_exit_code=terminated_exit)
                    if checked_run(["docker", "logs", cid], timeout=15):
                        raise SmokeRefused("G255_HUNG_PROGRAM_PRINTED_RESULT")
                    authorize_recovery(
                        approved=True, timeout_seen=stalled_timeout_verified,
                        terminated_exit=terminated_exit)
                    recovery_count += 1
                else:
                    observed = checked_run([
                        "docker", "wait", cid], timeout=15)
                    if observed != "0":
                        raise SmokeRefused("G255_HEALTHY_RETEST_EXIT_NOT_ZERO")
                    inspect(cid, started=True, expected_exit_code=0)
                    receipt = verify_output(
                        checked_run(["docker", "logs", cid], timeout=15))
                if (sha((folder / "source.csv").read_bytes()) != source_sha or
                        sha((folder / "typed.plan").read_bytes()) != plan_sha or
                        sha(program.read_bytes()) != binary_shas[stage]):
                    raise SmokeRefused("G255_DISPOSABLE_STAGE_INPUT_CHANGED")
                checked_run(["docker", "rm", cid], timeout=15)
                containers.remove(cid)
            if (not stalled_timeout_verified or terminated_exit != 137 or
                    recovery_count != 1 or receipt is None or
                    len(set(image_ids)) != 2 or
                    len(set(binary_shas.values())) != 2 or
                    checked_run(["docker", "image", "inspect", images[0],
                                 "--format", "{{.Id}}"], timeout=15)
                    != image_ids[0]):
                raise SmokeRefused("G255_FINAL_RECOVERY_INTEGRITY_MISSING")
            return {
                "schema": SCHEMA,
                "status": "REAL_DOCKER_STALL_TERMINATED_HEALTHY_RETEST_PASS",
                "real_docker_used": True,
                "actual_docker_wait_timeout_observed": True,
                "blocked_container_verified_exit": 137,
                "healthy_container_verified_exit": 0,
                "bounded_recovery_attempts": recovery_count,
                "wait_timeout_seconds": WAIT_TIMEOUT_SECONDS,
                "source_sha256": source_sha,
                "typed_plan_sha256": plan_sha,
                "failed_binary_sha256": binary_shas["stalled"],
                "healthy_binary_sha256": binary_shas["healthy"],
                "failed_image_sha256": image_ids[0][7:],
                "healthy_image_sha256": image_ids[1][7:],
                "healthy_receipt_sha256": receipt,
                "network_isolated": True, "owner_files_accessed": False,
                "host_volumes_mounted": False, "image_pull_performed": False,
                "customer_files_changed": False,
                "general_autonomous_healing": False,
                "uliya_expert_invoked": False, "nas_verified": False,
                "release_gate": "HOLD"
            }
    finally:
        # Only resources whose IDs/tags were created by THIS invocation.
        # On any failure fail closed; do not prune/force delete owner's images.
        for cid in containers:
            try:
                checked_run(["docker", "rm", "-f", cid], timeout=15)
            except SmokeRefused:
                pass
        for image in images:
            try:
                checked_run(["docker", "image", "rm", image], timeout=15)
            except SmokeRefused:
                pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bounded synthetic Docker hang recovery; NOT NAS")
    ap.add_argument(APPROVAL, action="store_true")
    args = ap.parse_args(argv)
    if not args.approve_synthetic_timeout_recovery:
        print(json.dumps({"status":"G255_SYNTHETIC_APPROVAL_REQUIRED",
                          "nas_verified":False, "release_gate":"HOLD"}))
        return 2
    try:
        report = run_real_timeout_recovery()
    except SmokeRefused as exc:
        print(json.dumps({"status":"G255_REAL_DOCKER_TIMEOUT_RECOVERY_NOT_VERIFIED",
                          "reason":str(exc), "nas_verified":False,
                          "release_gate":"HOLD"},sort_keys=True))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
