"""G233: real isolated Docker execution of TWO fixed synthetic local fixtures.

Public repository code, no customer files or mounts, no network, no registry
pull, no Uliya/NAS SDK invocation, no arbitrary scripts, no autonomous repair.
A manually/CI-approved local sandbox smoke only, NOT production workflow E2E.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
from pathlib import Path
import shutil
import subprocess
import tempfile

SMOKE_SCHEMA = "flowpilot-g233-real-local-docker-fixture-v1"
APPROVAL = "--approve-disconnected-synthetic-docker"
_LOCAL_DOCKER_HOST = "unix:///var/run/docker.sock"
C_SOURCE = r"""
#include <stdio.h>
#include <string.h>
int main(void) {
    FILE *f=fopen("/fixture/inventory.txt","rb");
    char first[80]={0}, second[80]={0};
    if (!f) return 4;
    if (!fgets(first,sizeof(first),f) || !fgets(second,sizeof(second),f)
        || fgetc(f)!=EOF || ferror(f)) { fclose(f); return 5; }
    fclose(f);
    if (strcmp(first,"README.md=PRESENT\n") != 0) return 6;
    if (strcmp(second,"release/final.pdf=MISSING\n") == 0) {
        puts("{\"schema\":\"flowpilot-g233-real-local-docker-fixture-v1\","
             "\"status\":\"SYNTHETIC_MISSING\","
             "\"present_count\":1,\"missing_count\":1,"
             "\"nas_verified\":false,\"owner_files_accessed\":false,"
             "\"auto_repair_performed\":false}");
        return 0;
    }
    if (strcmp(second,"release/final.pdf=PRESENT\n") == 0) {
        puts("{\"schema\":\"flowpilot-g233-real-local-docker-fixture-v1\","
             "\"status\":\"SYNTHETIC_RETEST_PRESENT\","
             "\"present_count\":2,\"missing_count\":0,"
             "\"nas_verified\":false,\"owner_files_accessed\":false,"
             "\"auto_repair_performed\":false}");
        return 0;
    }
    return 7;
}
"""
DOCKERFILE = """FROM scratch
COPY --chown=65534:65534 check /check
COPY --chown=65534:65534 inventory.txt /fixture/inventory.txt
USER 65534:65534
ENTRYPOINT ["/check"]
"""
EXPECTED = {"before": ("SYNTHETIC_MISSING", 1, 1),
            "after": ("SYNTHETIC_RETEST_PRESENT", 2, 0)}


class SmokeRefused(RuntimeError):
    pass


class SmokeTimedOut(SmokeRefused):
    """Only a real client subprocess timeout, not an arbitrary Docker error."""
    pass


def _local_docker_socket_ready() -> bool:
    """Fail closed: a configured remote Docker context is never sufficient."""
    try:
        path = "/var/run/docker.sock"
        return (os.name == "posix" and not os.path.islink(path)
                and stat.S_ISSOCK(os.stat(path).st_mode))
    except (OSError, ValueError):
        return False


def checked_run(argv: list[str], *, timeout: int = 45) -> str:
    """Run only fixed local tools; strip remote contexts and credential config."""
    if type(argv) is not list or not argv or argv[0] not in ("docker", "cc"):
        raise SmokeRefused("UNSUPPORTED_LOCAL_PROCESS")
    if argv[0] == "docker" and not _local_docker_socket_ready():
        raise SmokeRefused("LOCAL_DOCKER_SOCKET_NOT_VERIFIED")
    with tempfile.TemporaryDirectory(prefix="flowpilot-g233-client-") as config:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": config, "DOCKER_CONFIG": config,
            "DOCKER_HOST": _LOCAL_DOCKER_HOST,
        }
        cmd = ([argv[0], "--host=" + _LOCAL_DOCKER_HOST, *argv[1:]]
               if argv[0] == "docker" else argv)
        try:
            p = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                timeout=timeout, check=False, env=env, shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SmokeTimedOut("LOCAL_PROCESS_TIMEOUT") from exc
        except OSError as exc:
            raise SmokeRefused("LOCAL_PROCESS_UNAVAILABLE") from exc
    if p.returncode != 0:
        raise SmokeRefused("LOCAL_PROCESS_REFUSED_OR_FAILED")
    return p.stdout.strip()

def verify_host_config(payload: dict, *, started: bool,
                       expected_exit_code: int = 0) -> None:
    if (type(expected_exit_code) is not int
            or expected_exit_code not in (0, 11, 17, 137)):
        raise SmokeRefused("UNSUPPORTED_EXPECTED_CONTAINER_EXIT")
    if type(payload) is not dict:
        raise SmokeRefused("INSPECT_NOT_OBJECT")
    host = payload.get("HostConfig")
    config = payload.get("Config")
    state = payload.get("State")
    if (type(host) is not dict or type(config) is not dict or
            type(state) is not dict or payload.get("Mounts") != []):
        raise SmokeRefused("INSPECT_FIELDS_INVALID")
    if (host.get("NetworkMode") != "none" or
            host.get("ReadonlyRootfs") is not True or
            host.get("Privileged") is not False or
            host.get("PidsLimit") != 32 or
            host.get("Memory") != 64 * 1024 * 1024 or
            host.get("NanoCpus") != 250_000_000 or
            host.get("Binds") not in (None, []) or
            host.get("Mounts") not in (None, []) or
            host.get("Devices") not in (None, [])):
        raise SmokeRefused("ISOLATION_FLAGS_MISMATCH")
    caps, sec = host.get("CapDrop"), host.get("SecurityOpt")
    if (type(caps) is not list or [str(v).lower() for v in caps] != ["all"] or
            type(sec) is not list or
            not any("no-new-privileges" in str(s) for s in sec)):
        raise SmokeRefused("CAPABILITY_OR_SECURITY_OPT_MISMATCH")
    if config.get("User") != "65534:65534" or config.get("Entrypoint") != ["/check"]:
        raise SmokeRefused("INVALID_NONROOT_ENTRYPOINT")
    image = payload.get("Image")
    if type(image) is not str or not image.startswith("sha256:") or len(image) != 71:
        raise SmokeRefused("IMAGE_ID_NOT_A_LOCAL_DIGEST")
    if started:
        if (state.get("Running") is not False
                or state.get("Status") != "exited"
                or type(state.get("ExitCode")) is not int
                or state.get("ExitCode") != expected_exit_code):
            raise SmokeRefused("CONTAINER_EXECUTION_DID_NOT_PASS")
    elif state.get("Running") is not False or state.get("Status") != "created":
        raise SmokeRefused("CONTAINER_ALREADY_EXECUTING_BEFORE_VALIDATION")


def inspect(cid: str, *, started: bool, expected_exit_code: int = 0) -> None:
    raw = checked_run(["docker", "inspect", cid], timeout=15)
    try:
        rows = json.loads(raw)
        if type(rows) is not list or len(rows) != 1:
            raise SmokeRefused("INVALID_INSPECT_LIST")
    except (ValueError, TypeError) as exc:
        raise SmokeRefused("INVALID_INSPECT_JSON") from exc
    verify_host_config(rows[0], started=started,
                       expected_exit_code=expected_exit_code)


def verify_fixture_output(raw: str, stage: str) -> None:
    if len(raw) > 1024:
        raise SmokeRefused("OVERSIZE_FIXTURE_OUTPUT")
    try:
        def reject_duplicate_keys(pairs):
            item = {}
            for key, value in pairs:
                if key in item:
                    raise SmokeRefused("DUPLICATE_CONTAINER_RESPONSE_KEY")
                item[key] = value
            return item
        data = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (ValueError, TypeError) as exc:
        raise SmokeRefused("UNEXPECTED_CONTAINER_RESPONSE") from exc
    state, present, missing = EXPECTED[stage]
    if (type(data) is not dict or set(data) != {
            "schema", "status", "present_count", "missing_count",
            "nas_verified", "owner_files_accessed", "auto_repair_performed",
            } or data["schema"] != SMOKE_SCHEMA or data["status"] != state or
            type(data["present_count"]) is not int or data["present_count"] != present or
            type(data["missing_count"]) is not int or data["missing_count"] != missing or
            data["nas_verified"] is not False or
            data["owner_files_accessed"] is not False or
            data["auto_repair_performed"] is not False):
        raise SmokeRefused("INVALID_OR_OVERSTATED_FIXTURE_EVIDENCE")


def test_synthetic_docker() -> dict:
    if shutil.which("cc") is None or shutil.which("docker") is None:
        raise SmokeRefused("APPROVED_LOCAL_CC_OR_DOCKER_UNAVAILABLE")
    checked_run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
    # Per-invocation unique image names: never overwrite or prune an owner's tag.
    run_tag = secrets.token_hex(12)
    images: list[str] = []
    containers: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g233-only-") as temp:
            base = Path(temp)
            src = base / "fixture.c"
            binary = base / "check"
            src.write_text(C_SOURCE, encoding="ascii")
            checked_run(["cc", "-O2", "-static", "-s", "-Wall", "-Wextra",
                         "-Werror", str(src), "-o", str(binary)], timeout=30)
            first_id: str | None = None
            for stage in ("before", "after"):
                directory = base / stage
                directory.mkdir()
                executable = directory / "check"
                executable.write_bytes(binary.read_bytes())
                executable.chmod(0o755)
                inventory = directory / "inventory.txt"
                last = "MISSING" if stage == "before" else "PRESENT"
                inventory.write_text(
                    "README.md=PRESENT\nrelease/final.pdf=" + last + "\n",
                    encoding="ascii")
                (directory / "Dockerfile").write_text(DOCKERFILE, encoding="ascii")
                image = "flowpilot-g233-" + run_tag + "-" + stage + ":local"
                existing_tags = checked_run([
                    "docker", "image", "ls", "--filter", "reference=" + image,
                    "--format", "{{.Repository}}:{{.Tag}}",
                ], timeout=15)
                if image in existing_tags.splitlines():
                    raise SmokeRefused("IMAGE_TAG_ALREADY_PRESENT")
                checked_run(["docker", "build", "--pull=false", "--network=none",
                             "--no-cache", "--tag", image, str(directory)], timeout=75)
                images.append(image)
                sha = checked_run(["docker", "image", "inspect", image,
                                   "--format", "{{.Id}}"], timeout=15)
                if not sha.startswith("sha256:") or len(sha) != 71:
                    raise SmokeRefused("UNPINNED_LOCAL_IMAGE")
                if stage == "before":
                    first_id = sha
                else:
                    existing = checked_run(["docker", "image", "inspect",
                                            images[0], "--format", "{{.Id}}"],
                                           timeout=15)
                    if first_id != existing:
                        raise SmokeRefused("ORIGINAL_SYNTHETIC_IMAGE_CHANGED")
                cid = checked_run([
                    "docker", "create", "--network", "none", "--read-only",
                    "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges:true",
                    "--pids-limit", "32", "--memory", "64m",
                    "--cpus", "0.25", "--user", "65534:65534", sha,
                ], timeout=15)
                containers.append(cid)
                inspect(cid, started=False)  # fail BEFORE starting if unsafe
                output = checked_run(["docker", "start", "--attach", cid],
                                     timeout=12)
                inspect(cid, started=True)
                verify_fixture_output(output, stage)
                checked_run(["docker", "rm", cid], timeout=15)
                containers.remove(cid)
        return {
            "schema": SMOKE_SCHEMA,
            "status": "REAL_LOCAL_DOCKER_FIXED_FIXTURE_RETEST_PASS",
            "real_docker_engine_used": True,
            "before_missing_count": 1, "after_missing_count": 0,
            "before_image_immutable": True, "network_isolated": True,
            "rootfs_readonly": True, "run_as_root": False,
            "image_pull_performed": False, "host_volumes_mounted": False,
            "nas_verified": False, "uliya_expert_invoked": False,
            "general_workflow_executed": False, "auto_repair_performed": False,
            "release_gate": "HOLD",
        }
    finally:
        # Clean ONLY resources created in this invocation; never prune others.
        for cid in containers:
            try:
                checked_run(["docker", "rm", "-f", cid], timeout=12)
            except SmokeRefused:
                pass
        for image in images:
            try:
                checked_run(["docker", "image", "rm", "-f", image], timeout=12)
            except SmokeRefused:
                pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(APPROVAL, action="store_true")
    args = p.parse_args(argv)
    if not getattr(args, "approve_disconnected_synthetic_docker"):
        print(json.dumps({"status": "EXPLICIT_LOCAL_DOCKER_APPROVAL_REQUIRED",
                          "release_gate": "HOLD", "nas_verified": False}))
        return 2
    try:
        result = test_synthetic_docker()
    except SmokeRefused as exc:
        print(json.dumps({"status": "LOCAL_DOCKER_SMOKE_NOT_VERIFIED",
                          "reason": str(exc), "nas_verified": False,
                          "release_gate": "HOLD"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
