"""G192 local-only Docker image readiness probe (NO vendor/owner code execution).

Reads Docker daemon image metadata via the local Unix socket; does not read
candidate/Kit ZIPs, run/pull/build images, request network, or change approval.
Image ID is identity, NOT independent provenance/attestation.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile

import flowpilot3_official_checker as gate

MAX_OUTPUT = 1000


def _report(status: str, *, inspected: bool = False, image_id: str | None = None,
            platform: str | None = None) -> dict:
    report = {
        "schema": "flowpilot-g192-docker-preflight.v1",
        "status": status,
        "docker_image_inspected": inspected,
        "image_provenance_verified": False,
        "official_checker_executed": False,
        "private_candidate_or_kit_read": False,
        "nas_or_expert_executed": False,
        "docker_container_executed": False,
        "external_image_pull": False,
        "release_gate": "HOLD",
    }
    if image_id is not None:
        report["local_image_id"] = image_id
    if platform is not None:
        report["platform"] = platform
    return report


def preflight(image_id: object = None) -> dict:
    """Safe local-only readiness report. All paths and raw Docker errors redacted."""
    # This is intentionally independent of private candidate, kit and owner approval.
    # Never use a remote daemon, Docker Desktop context or inherited credentials.
    if not gate._valid_image_id(image_id):
        return _report("EXACT_IMAGE_ID_REQUIRED")
    docker = shutil.which("docker")
    if not docker:
        return _report("LOCAL_DOCKER_CLIENT_MISSING")
    if not gate._local_docker_socket_ready():
        return _report("LOCAL_UNIX_DOCKER_SOCKET_UNAVAILABLE")
    try:
        with tempfile.TemporaryDirectory(prefix="ugreen-g192-docker-preflight-") as cfg:
            env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": cfg,
                "DOCKER_CONFIG": cfg,
                "DOCKER_HOST": "unix:///var/run/docker.sock",
            }
            command = [
                docker, "--host=unix:///var/run/docker.sock", "--config", cfg,
                "image", "inspect", "--format", "{{.Id}}|{{.Os}}|{{.Architecture}}",
                image_id,
            ]
            result = subprocess.run(
                command, env=env, capture_output=True, timeout=20, check=False,
                cwd=cfg,
            )
    except (OSError, subprocess.TimeoutExpired):
        return _report("LOCAL_DOCKER_INSPECTION_FAILED")
    if (result.returncode != 0 or result.stderr.strip()
            or not 0 < len(result.stdout) <= MAX_OUTPUT):
        return _report("LOCAL_IMAGE_NOT_VERIFIED")
    try:
        output = result.stdout.decode("ascii", "strict").strip()
    except UnicodeDecodeError:
        return _report("LOCAL_IMAGE_METADATA_INVALID")
    parts = output.split("|")
    if len(parts) != 3 or parts[0] != image_id:
        return _report("LOCAL_IMAGE_ID_MISMATCH")
    os_name, arch = parts[1:]
    if os_name != "linux" or arch not in ("amd64", "arm64"):
        return _report("LOCAL_IMAGE_PLATFORM_UNSUPPORTED")
    # The local configuration digest can match a malicious or substituted image.
    # This receipt is not permission to run untrusted vendor JS.
    return _report("LOCAL_IMAGE_INSPECTED_PROVENANCE_UNVERIFIED",
                   inspected=True, image_id=image_id,
                   platform=os_name + "/" + arch)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local Docker image metadata only; never runs vendor Checker or containers")
    parser.add_argument("--image-id",
                        help="Exact locally installed image ID sha256: followed by 64 lowercase hex")
    args = parser.parse_args(argv)
    print(json.dumps(preflight(args.image_id), sort_keys=True))
    # This is *only* a readiness check. Even positive inspection is not vendor PASS.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
