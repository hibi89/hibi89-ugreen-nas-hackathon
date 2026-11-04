"""G253: independently repair ONE code-owned synthetic DAG PLAN defect in Docker.

Unlike G237's invalid CSV decimal, the CSV remains identical while a typed
graph instruction is corrupted. Verify real container exit 11, then repair
only a disposable plan copy after explicit synthetic approval and retest.
No owner sources, volume mounts, registry pulls, network or NAS operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import tempfile

from flowpilot_g233_real_docker_smoke import SmokeRefused, checked_run, inspect
from flowpilot_g235_typed_dag_docker import (
    C_SOURCE, DOCKERFILE_TYPED, PLAN, SOURCE, verify_output,
)

SCHEMA = "flowpilot-g253-code-owned-typed-plan-repair-v1"
APPROVAL = "--approve-synthetic-typed-plan-repair"
VALID_NODE = "validate_decimal\n"
BROKEN_NODE = "validate_decima1\n"
if PLAN.count(VALID_NODE) != 1 or BROKEN_NODE in PLAN:
    raise RuntimeError("G253_CODE_OWNED_PLAN_DRIFT")
BROKEN_PLAN = PLAN.replace(VALID_NODE, BROKEN_NODE, 1)
STAGES = ("bad_plan", "repaired_plan")


def sha(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise SmokeRefused("G253_HASH_INPUT_NOT_BYTES")
    return hashlib.sha256(raw).hexdigest()


def require_exit(raw: object, stage: str) -> int:
    expected = {"bad_plan": 11, "repaired_plan": 0}
    if stage not in expected or type(raw) is not str or raw != str(expected[stage]):
        raise SmokeRefused("G253_CONTAINER_EXIT_NOT_EXPECTED")
    return expected[stage]


def repair_only_fixed_plan(raw: object, *, diagnosed_exit: object,
                           approved: bool) -> bytes:
    if approved is not True or type(diagnosed_exit) is not int or diagnosed_exit != 11:
        raise SmokeRefused("G253_APPROVAL_OR_DIAGNOSIS_MISSING")
    broken = BROKEN_PLAN.encode("ascii")
    if type(raw) is not bytes or raw != broken or raw.count(BROKEN_NODE.encode("ascii")) != 1:
        raise SmokeRefused("G253_UNKNOWN_PLAN_REFUSED")
    fixed = raw.replace(BROKEN_NODE.encode("ascii"), VALID_NODE.encode("ascii"), 1)
    if fixed != PLAN.encode("ascii") or fixed == raw:
        raise SmokeRefused("G253_REPAIR_CONTRACT_REFUSED")
    return fixed


def run_synthetic_plan_repair() -> dict:
    if shutil.which("docker") is None or shutil.which("cc") is None:
        raise SmokeRefused("G253_LOCAL_DOCKER_OR_COMPILER_MISSING")
    checked_run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
    tag = secrets.token_hex(12)
    images: list[str] = []
    containers: list[str] = []
    original_plan = BROKEN_PLAN.encode("ascii")
    repaired_plan: bytes | None = None
    immutable_image: str | None = None
    final_receipt: str | None = None
    image_ids = []
    repairs = 0
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g253-synthetic-only-") as tmp:
            base = Path(tmp)
            cfile, executable = base / "check.c", base / "check"
            cfile.write_text(C_SOURCE, encoding="ascii")
            checked_run(["cc", "-O2", "-static", "-s", "-Wall", "-Wextra",
                         "-Werror", str(cfile), "-o", str(executable)], timeout=30)
            executable_bytes = executable.read_bytes()
            executable_sha = sha(executable_bytes)
            csv_bytes = SOURCE.encode("ascii")
            csv_sha = sha(csv_bytes)
            for stage in STAGES:
                folder = base / stage
                folder.mkdir()
                plan_bytes = original_plan if stage == "bad_plan" else repaired_plan
                if type(plan_bytes) is not bytes:
                    raise SmokeRefused("G253_MISSING_EXPLICIT_REPAIR")
                (folder / "check").write_bytes(executable_bytes)
                (folder / "check").chmod(0o755)
                (folder / "source.csv").write_bytes(csv_bytes)
                (folder / "typed.plan").write_bytes(plan_bytes)
                (folder / "Dockerfile").write_text(DOCKERFILE_TYPED, encoding="ascii")
                image = f"flowpilot-g253-{tag}-{stage}:local"
                if image in checked_run([
                    "docker", "image", "ls", "--filter", "reference=" + image,
                    "--format", "{{.Repository}}:{{.Tag}}"], timeout=15).splitlines():
                    raise SmokeRefused("G253_IMAGE_COLLISION")
                checked_run(["docker", "build", "--pull=false", "--network=none",
                             "--no-cache", "--tag", image, str(folder)], timeout=75)
                images.append(image)
                image_id = checked_run(["docker", "image", "inspect", image,
                                        "--format", "{{.Id}}"], timeout=15)
                if not (image_id.startswith("sha256:") and len(image_id) == 71):
                    raise SmokeRefused("G253_IMAGE_NOT_IMMUTABLE")
                image_ids.append(image_id)
                if stage == "bad_plan":
                    immutable_image = image_id
                elif checked_run(["docker", "image", "inspect", images[0],
                                  "--format", "{{.Id}}"], timeout=15) != immutable_image:
                    raise SmokeRefused("G253_FAILED_IMAGE_CHANGED")
                cid = checked_run([
                    "docker", "create", "--network", "none", "--read-only",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                    "--pids-limit", "32", "--memory", "64m", "--cpus", "0.25",
                    "--user", "65534:65534", image_id], timeout=15)
                containers.append(cid)
                inspect(cid, started=False)
                if checked_run(["docker", "start", cid], timeout=15) != cid:
                    raise SmokeRefused("G253_CONTAINER_START_MISMATCH")
                exit_code = require_exit(
                    checked_run(["docker", "wait", cid], timeout=15), stage)
                inspect(cid, started=True, expected_exit_code=exit_code)
                stdout = checked_run(["docker", "logs", cid], timeout=15)
                if stage == "bad_plan":
                    if stdout:
                        raise SmokeRefused("G253_FAILED_CONTAINER_EMITTED_SUCCESS")
                    repaired_plan = repair_only_fixed_plan(
                        original_plan, diagnosed_exit=exit_code, approved=True)
                    repairs += 1
                else:
                    final_receipt = verify_output(stdout)
                if (sha((folder / "source.csv").read_bytes()) != csv_sha
                        or sha((folder / "typed.plan").read_bytes()) != sha(plan_bytes)
                        or sha((folder / "check").read_bytes()) != executable_sha):
                    raise SmokeRefused("G253_STAGE_INPUT_MODIFIED")
                checked_run(["docker", "rm", cid], timeout=15)
                containers.remove(cid)
            if (repairs != 1 or repaired_plan != PLAN.encode("ascii")
                    or not final_receipt or image_ids[0] == image_ids[1]
                    or checked_run(["docker", "image", "inspect", images[0],
                                    "--format", "{{.Id}}"], timeout=15) != immutable_image):
                raise SmokeRefused("G253_RETEST_ORIGINAL_INTEGRITY_MISSING")
            return {
                "schema": SCHEMA,
                "status": "REAL_DOCKER_SYNTHETIC_TYPED_PLAN_REPAIR_PASS",
                "failed_container_exit": 11, "retested_container_exit": 0,
                "bounded_plan_copy_repairs": repairs,
                "original_bad_plan_sha256": sha(original_plan),
                "fixed_plan_copy_sha256": sha(repaired_plan),
                "unchanged_csv_sha256": csv_sha,
                "unchanged_binary_sha256": executable_sha,
                "original_image_sha256": image_ids[0][7:],
                "retested_image_sha256": image_ids[1][7:],
                "final_typed_dag_receipt_sha256": final_receipt,
                "real_docker_used": True, "network_isolated": True,
                "host_volumes_mounted": False, "image_pulled": False,
                "customer_data_read": False, "owner_files_modified": False,
                "generic_auto_repair": False, "uliya_expert_invoked": False,
                "nas_verified": False, "release_gate": "HOLD",
            }
    finally:
        for cid in containers:
            try:
                checked_run(["docker", "rm", "-f", cid], timeout=12)
            except SmokeRefused:
                pass
        for image in images:
            try:
                checked_run(["docker", "image", "rm", image], timeout=12)
            except SmokeRefused:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic typed-plan failure recovery; NOT NAS")
    parser.add_argument(APPROVAL, action="store_true")
    args = parser.parse_args(argv)
    if not args.approve_synthetic_typed_plan_repair:
        print(json.dumps({"status": "G253_EXPLICIT_SYNTHETIC_APPROVAL_REQUIRED",
                          "nas_verified": False, "release_gate": "HOLD"}))
        return 2
    try:
        result = run_synthetic_plan_repair()
    except SmokeRefused as exc:
        print(json.dumps({"status": "G253_DOCKER_REPAIR_NOT_VERIFIED",
                          "reason": str(exc), "nas_verified": False,
                          "release_gate": "HOLD"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
