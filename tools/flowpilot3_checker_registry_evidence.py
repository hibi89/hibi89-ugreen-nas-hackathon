"""G193 read-only local Docker Official Node repository-reference evidence.

Never reads owner ZIP/Kit, starts/pulls an image or invokes vendor JavaScript.
A RepoDigests association is NOT proof of publisher signature or provenance.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile

import flowpilot3_official_checker as gate

NODE_REPOSITORY = "docker.io/library/node"
MAX_OUTPUT_BYTES = 4096


def valid_node_repo_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(
        r"docker\.io/library/node@sha256:[0-9a-f]{64}", value
    ) is not None


def _receipt(status: str, *, image_id: str | None = None, platform: str | None = None) -> dict:
    result = {
        "schema": "flowpilot-g193-official-node-digest-evidence.v1",
        "status": status,
        "image_provenance_verified": False,
        "official_checker_executed": False,
        "owner_archive_read": False,
        "docker_container_executed": False,
        "docker_image_pulled": False,
        "nas_or_expert_executed": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }
    if image_id is not None:
        result["local_image_id"] = image_id
    if platform is not None:
        result["platform"] = platform
    return result


def inspect_local_repo_digest(image_id: object, expected_repo_digest: object) -> dict:
    # Fail before touching Docker metadata on missing/ambiguous expected pins.
    if not gate._valid_image_id(image_id):
        return _receipt("EXACT_LOCAL_IMAGE_ID_REQUIRED")
    if not valid_node_repo_digest(expected_repo_digest):
        return _receipt("EXACT_OFFICIAL_NODE_REPO_DIGEST_REQUIRED")
    docker = shutil.which("docker")
    if not docker:
        return _receipt("LOCAL_DOCKER_CLIENT_MISSING")
    if not gate._local_docker_socket_ready():
        return _receipt("LOCAL_UNIX_DOCKER_SOCKET_UNAVAILABLE")
    try:
        with tempfile.TemporaryDirectory(prefix="g193-local-node-image-") as config:
            env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": config,
                "DOCKER_CONFIG": config,
                "DOCKER_HOST": "unix:///var/run/docker.sock",
            }
            command = [
                docker, "--host=unix:///var/run/docker.sock", "--config", config,
                "image", "inspect", "--format",
                "{{.Id}}|{{.Os}}|{{.Architecture}}|{{json .RepoDigests}}",
                image_id,
            ]
            result = subprocess.run(
                command, cwd=config, env=env,
                capture_output=True, timeout=20, check=False,
            )
    except (OSError, subprocess.TimeoutExpired):
        return _receipt("LOCAL_DOCKER_IMAGE_INSPECT_FAILED")
    if (result.returncode != 0 or result.stderr.strip()
            or not 0 < len(result.stdout) <= MAX_OUTPUT_BYTES):
        return _receipt("LOCAL_IMAGE_METADATA_UNAVAILABLE")
    try:
        observed = result.stdout.decode("ascii", "strict").strip()
    except UnicodeDecodeError:
        return _receipt("LOCAL_IMAGE_METADATA_INVALID")
    parts = observed.split("|", 3)
    if len(parts) != 4 or parts[0] != image_id:
        return _receipt("LOCAL_IMAGE_ID_MISMATCH")
    os_name, architecture, digests_json = parts[1:]
    if os_name != "linux" or architecture not in ("amd64", "arm64"):
        return _receipt("LOCAL_IMAGE_PLATFORM_UNSUPPORTED")
    try:
        repo_digests = json.loads(digests_json)
    except (ValueError, RecursionError):
        return _receipt("LOCAL_REPO_DIGEST_METADATA_INVALID")
    if (not isinstance(repo_digests, list) or len(repo_digests) > 128
            or not all(isinstance(item, str) for item in repo_digests)
            or expected_repo_digest not in repo_digests):
        return _receipt("LOCAL_OFFICIAL_NODE_REPO_REFERENCE_NOT_MATCHED")
    # This merely checks local Docker metadata. It does NOT verify upstream
    # signature, publisher identity, build provenance, or user release approval.
    return _receipt(
        "LOCAL_NODE_REPO_REFERENCE_PRESENT_SIGNATURE_UNVERIFIED",
        image_id=image_id, platform=os_name + "/" + architecture,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local Docker metadata only; never execute Checker/NAS/vendor code"
    )
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--expected-repo-digest", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(inspect_local_repo_digest(args.image_id, args.expected_repo_digest),
                     sort_keys=True))
    return 2  # A metadata result can NEVER mean official checker pass/release.


if __name__ == "__main__":
    raise SystemExit(main())
