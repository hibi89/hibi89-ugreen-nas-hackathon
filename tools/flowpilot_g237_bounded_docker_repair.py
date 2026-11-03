"""G237: bounded, actually executed synthetic Docker failure/repair/retest.

The source, repair rule and C executable are code-owned constants. A real
container must produce exact exit 17 for a synthetic CSV non-digit defect.
Only then may ONE new ephemeral synthetic copy be corrected and independently
retested using the same compiled fixed typed DAG. Never mount customer data.
No NAS/Uliya API, arbitrary code, general healing or user-file mutation.
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

SCHEMA = "flowpilot-g237-bounded-synthetic-docker-repair-v1"
APPROVAL = "--approve-synthetic-only-auto-repair"
DEFECT = "bob,3O0\n"
GOOD = "bob,300\n"
if SOURCE.count(GOOD) != 1 or SOURCE.count(DEFECT) != 0:
    raise RuntimeError("G237_CODE_OWNED_CSV_CONTRACT_DRIFT")
BROKEN_SOURCE = SOURCE.replace(GOOD, DEFECT)
STAGES = ("broken", "repaired")
EXPECTED_EXITS = {"broken": 17, "repaired": 0}


def digest(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise SmokeRefused("G237_NON_BYTES_SOURCE")
    return hashlib.sha256(raw).hexdigest()


def require_exit(observed: object, stage: str) -> int:
    """A successful docker wait COMMAND is not a successful CONTAINER."""
    if stage not in EXPECTED_EXITS or type(observed) is not str:
        raise SmokeRefused("G237_EXIT_RECEIPT_INVALID")
    expected = EXPECTED_EXITS[stage]
    if observed != str(expected):
        raise SmokeRefused("G237_UNEXPECTED_CONTAINER_EXIT")
    return expected


def repair_one_synthetic_decimal(source: object, *, diagnosed_exit: object,
                                 approved: bool) -> bytes:
    """Fail closed before touching any data. Only a disposable fixed fixture."""
    if (approved is not True or type(diagnosed_exit) is not int
            or diagnosed_exit != 17):
        raise SmokeRefused("G237_EXACT_SYNTHETIC_REPAIR_APPROVAL_REQUIRED")
    broken = BROKEN_SOURCE.encode("ascii")
    if type(source) is not bytes or source != broken or source.count(
            DEFECT.encode("ascii")) != 1:
        raise SmokeRefused("G237_UNKNOWN_DEFECT_REFUSED")
    repaired = source.replace(DEFECT.encode("ascii"), GOOD.encode("ascii"), 1)
    if repaired != SOURCE.encode("ascii") or repaired == source:
        raise SmokeRefused("G237_REPAIR_CONTRACT_REFUSED")
    return repaired


def run_bounded_repair() -> dict:
    """Real Docker test: fail with code 17, repair a COPY, rerun once, verify."""
    if shutil.which("cc") is None or shutil.which("docker") is None:
        raise SmokeRefused("G237_LOCAL_COMPILER_OR_DOCKER_UNAVAILABLE")
    checked_run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
    tag_nonce = secrets.token_hex(12)
    images: list[str] = []
    containers: list[str] = []
    original_digest: str | None = None
    successful_receipt: str | None = None
    before = BROKEN_SOURCE.encode("ascii")
    after = None
    repair_attempts = 0
    image_digests = {}
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g237-only-") as temp:
            root = Path(temp)
            source_code = root / "trusted-check.c"
            binary = root / "check"
            source_code.write_text(C_SOURCE, encoding="ascii")
            checked_run(["cc", "-O2", "-static", "-s", "-Wall", "-Wextra",
                         "-Werror", str(source_code), "-o", str(binary)],
                        timeout=30)
            binary_sha = digest(binary.read_bytes())
            for stage in STAGES:
                case = root / stage
                case.mkdir()
                stage_binary = case / "check"
                stage_binary.write_bytes(binary.read_bytes())
                stage_binary.chmod(0o755)
                data = before if stage == "broken" else after
                if type(data) is not bytes:
                    raise SmokeRefused("G237_REPAIR_DID_NOT_PRODUCE_BYTES")
                (case / "source.csv").write_bytes(data)
                (case / "typed.plan").write_text(PLAN, encoding="ascii")
                (case / "Dockerfile").write_text(DOCKERFILE_TYPED, encoding="ascii")
                if (digest(stage_binary.read_bytes()) != binary_sha or
                        digest((case / "typed.plan").read_bytes()) !=
                        digest(PLAN.encode("ascii"))):
                    raise SmokeRefused("G237_BINARY_OR_DAG_DRIFT")
                image = f"flowpilot-g237-{tag_nonce}-{stage}:local"
                existing = checked_run(["docker", "image", "ls",
                                        "--filter", "reference=" + image,
                                        "--format", "{{.Repository}}:{{.Tag}}"],
                                       timeout=15)
                if image in existing.splitlines():
                    raise SmokeRefused("G237_IMAGE_COLLISION")
                checked_run(["docker", "build", "--pull=false", "--network=none",
                             "--no-cache", "--tag", image, str(case)], timeout=75)
                images.append(image)
                immutable_id = checked_run(["docker", "image", "inspect",
                                            image, "--format", "{{.Id}}"], timeout=15)
                if (not immutable_id.startswith("sha256:")
                        or len(immutable_id) != 71):
                    raise SmokeRefused("G237_LOCAL_IMAGE_DIGEST_REFUSED")
                image_digests[stage] = immutable_id
                if stage == "broken":
                    original_digest = immutable_id
                elif checked_run(["docker", "image", "inspect", images[0],
                                  "--format", "{{.Id}}"], timeout=15) != original_digest:
                    raise SmokeRefused("G237_ORIGINAL_IMAGE_CHANGED")
                cid = checked_run(["docker", "create", "--network", "none",
                                   "--read-only", "--cap-drop", "ALL",
                                   "--security-opt", "no-new-privileges:true",
                                   "--pids-limit", "32", "--memory", "64m",
                                   "--cpus", "0.25", "--user", "65534:65534",
                                   immutable_id], timeout=15)
                containers.append(cid)
                inspect(cid, started=False)
                started = checked_run(["docker", "start", cid], timeout=15)
                if started != cid:
                    raise SmokeRefused("G237_CONTAINER_START_ID_MISMATCH")
                observed = checked_run(["docker", "wait", cid], timeout=15)
                exit_code = require_exit(observed, stage)
                inspect(cid, started=True, expected_exit_code=exit_code)
                stdout = checked_run(["docker", "logs", cid], timeout=15)
                if stage == "broken":
                    if stdout:
                        raise SmokeRefused("G237_BROKEN_CONTAINER_EMITTED_SUCCESS")
                    # Only an actual verified failure authorizes a code-owned fix.
                    after = repair_one_synthetic_decimal(
                        before, diagnosed_exit=exit_code, approved=True)
                    repair_attempts += 1
                    if (repair_attempts != 1 or digest(before) !=
                            digest(BROKEN_SOURCE.encode("ascii"))):
                        raise SmokeRefused("G237_UNBOUNDED_OR_MUTATED_ORIGINAL")
                else:
                    successful_receipt = verify_output(stdout)
                if digest((case / "source.csv").read_bytes()) != digest(data):
                    raise SmokeRefused("G237_DISPOSABLE_SOURCE_MUTATED")
                if digest((case / "check").read_bytes()) != binary_sha:
                    raise SmokeRefused("G237_DISPOSABLE_BINARY_MUTATED")
                checked_run(["docker", "rm", cid], timeout=15)
                containers.remove(cid)
            if (repair_attempts != 1 or successful_receipt is None
                    or after != SOURCE.encode("ascii")
                    or image_digests["broken"] == image_digests["repaired"]
                    or checked_run(["docker", "image", "inspect", images[0],
                                    "--format", "{{.Id}}"], timeout=15)
                    != original_digest):
                raise SmokeRefused("G237_FINAL_RETEST_INTEGRITY_REFUSED")
            return {
                "schema": SCHEMA,
                "status": "REAL_DOCKER_BOUNDED_SYNTHETIC_REPAIR_PASS",
                "real_docker_used": True,
                "verified_broken_container_exit_code": 17,
                "verified_retest_container_exit_code": 0,
                "bounded_repair_attempts": repair_attempts,
                "original_source_sha256": digest(before),
                "repaired_copy_sha256": digest(after),
                "typed_dag_sha256": digest(PLAN.encode("ascii")),
                "same_compiled_executable_sha256": binary_sha,
                "original_image_sha256": original_digest[7:],
                "repaired_image_sha256": image_digests["repaired"][7:],
                "final_receipt_sha256": successful_receipt,
                "synthetic_original_immutable": True,
                "network_isolated": True, "host_volumes_mounted": False,
                "container_rootfs_readonly": True, "image_pull_performed": False,
                "customer_files_accessed": False, "customer_files_modified": False,
                "ai_autonomous_repair": False, "arbitrary_workflows_supported": False,
                "uliya_expert_invoked": False, "nas_verified": False,
                "release_gate": "HOLD",
            }
    finally:
        # Only the random tags and container IDs owned by this invocation.
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
    p = argparse.ArgumentParser(description="G237 fixed synthetic-only actual Docker repair; NOT NAS")
    p.add_argument(APPROVAL, action="store_true")
    args = p.parse_args(argv)
    if not getattr(args, "approve_synthetic_only_auto_repair"):
        print(json.dumps({"status": "G237_EXPLICIT_SYNTHETIC_APPROVAL_REQUIRED",
                          "release_gate": "HOLD", "nas_verified": False}))
        return 2
    try:
        data = run_bounded_repair()
    except SmokeRefused as exc:
        print(json.dumps({"status": "G237_LOCAL_DOCKER_REPAIR_NOT_VERIFIED",
                          "reason": str(exc), "release_gate": "HOLD",
                          "nas_verified": False}, sort_keys=True))
        return 2
    print(json.dumps(data, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
