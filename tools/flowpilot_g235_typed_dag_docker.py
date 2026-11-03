"""G235: real Docker run of one fixed typed DAG over synthetic bytes.

Local ephemeral scratch-image test only. No imported customer files, no
mounts/network/pulls, no Uliya/NAS capabilities, no autonomous code edits.
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
    SmokeRefused, checked_run, inspect, DOCKERFILE,
)

SCHEMA = "flowpilot-g235-synthetic-typed-dag-v1"
STEPS = ("csv_read", "validate_decimal", "group_sum", "report")
PLAN = "\n".join(STEPS) + "\n"
SOURCE = "customer,amount_cents\nalice,125\nbob,300\nalice,275\n"
APPROVAL = "--approve-synthetic-typed-docker"
C_SOURCE = r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
int main(void) {
    const char *steps[4] = {"csv_read\n","validate_decimal\n","group_sum\n","report\n"};
    FILE *p = fopen("/fixture/typed.plan", "rb");
    char line[96] = {0};
    if (!p) return 10;
    for (int i=0; i<4; i++) {
        if (!fgets(line, sizeof(line), p) || strcmp(line, steps[i]) != 0) {
            fclose(p); return 11;
        }
    }
    if (fgetc(p) != EOF || ferror(p)) { fclose(p); return 12; }
    fclose(p);
    FILE *f = fopen("/fixture/source.csv", "rb");
    if (!f) return 13;
    if (!fgets(line, sizeof(line), f) ||
        strcmp(line, "customer,amount_cents\n") != 0) { fclose(f); return 14; }
    int rows=0, alice=0, bob=0;
    while (fgets(line, sizeof(line), f)) {
        rows++;
        if (rows>8) { fclose(f); return 15; }
        char *comma = strchr(line, ',');
        if (!comma || comma==line || strchr(comma+1, ',') != NULL ||
            !strchr(comma+1, '\n')) { fclose(f); return 16; }
        *comma = '\0';
        char *end = NULL;
        errno = 0;
        long cents = strtol(comma+1, &end, 10);
        if (errno || !end || strcmp(end, "\n") != 0 ||
            cents < 0 || cents > 10000) { fclose(f); return 17; }
        if (!strcmp(line,"alice")) alice += (int)cents;
        else if (!strcmp(line,"bob")) bob += (int)cents;
        else { fclose(f); return 18; }
    }
    if (ferror(f) || rows != 3) { fclose(f); return 19; }
    fclose(f);
    if (alice != 400 || bob != 300) return 20;
    printf("{\"schema\":\"flowpilot-g235-synthetic-typed-dag-v1\","
           "\"status\":\"SYNTHETIC_TYPED_DAG_COMPLETE\","
           "\"node_types\":[\"csv_read\",\"validate_decimal\",\"group_sum\",\"report\"],"
           "\"source_rows\":%d,"
           "\"report_rows\":[{\"customer\":\"alice\",\"total_cents\":%d},"
           "{\"customer\":\"bob\",\"total_cents\":%d}],"
           "\"nas_verified\":false,\"owner_files_opened\":false,"
           "\"automatic_repair\":false}\n",rows,alice,bob);
    return 0;
}
"""
DOCKERFILE_TYPED = DOCKERFILE.replace(
    "COPY --chown=65534:65534 inventory.txt /fixture/inventory.txt",
    "COPY --chown=65534:65534 typed.plan /fixture/typed.plan\n"
    "COPY --chown=65534:65534 source.csv /fixture/source.csv"
)
EXPECTED = {
    "schema": SCHEMA, "status": "SYNTHETIC_TYPED_DAG_COMPLETE",
    "node_types": list(STEPS), "source_rows": 3,
    "report_rows": [
        {"customer": "alice", "total_cents": 400},
        {"customer": "bob", "total_cents": 300},
    ],
    "nas_verified": False, "owner_files_opened": False,
    "automatic_repair": False,
}


def verify_output(raw: str) -> str:
    """Require exact types, fields, order and totals; no false live claims."""
    if type(raw) is not str or len(raw) > 1024:
        raise SmokeRefused("G235_OUTPUT_SIZE_REFUSED")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SmokeRefused("G235_DUPLICATE_RECEIPT_KEY")
            result[key] = value
        return result
    try:
        record = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, TypeError) as exc:
        raise SmokeRefused("G235_INVALID_OUTPUT_JSON") from exc
    if (type(record) is not dict or set(record) != set(EXPECTED)
            or any(type(record[k]) is not type(v) or record[k] != v
                   for k, v in EXPECTED.items())
            or type(record["source_rows"]) is not int
            or type(record["report_rows"]) is not list
            or any(type(v.get("total_cents")) is not int
                   for v in record["report_rows"])):
        raise SmokeRefused("G235_OUTPUT_CONTRACT_MISMATCH")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_fixed_dag() -> dict:
    if shutil.which("cc") is None or shutil.which("docker") is None:
        raise SmokeRefused("G235_LOCAL_DOCKER_OR_COMPILER_UNAVAILABLE")
    # G234 checked_run pins every Docker command to a non-symlink local Unix
    # socket and excludes all inherited context, auth, and remote endpoint.
    checked_run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
    image = "flowpilot-g235-" + secrets.token_hex(12) + ":local"
    cid = None
    created_image = False
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-g235-only-") as temp:
            base = Path(temp)
            source = base / "source.csv"
            plan = base / "typed.plan"
            source.write_text(SOURCE, encoding="ascii")
            plan.write_text(PLAN, encoding="ascii")
            source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            plan_sha = hashlib.sha256(plan.read_bytes()).hexdigest()
            cfile = base / "check.c"
            binary = base / "check"
            cfile.write_text(C_SOURCE, encoding="ascii")
            checked_run(["cc", "-O2", "-static", "-s", "-Wall", "-Wextra",
                         "-Werror", str(cfile), "-o", str(binary)], timeout=30)
            (base / "Dockerfile").write_text(DOCKERFILE_TYPED, encoding="ascii")
            tag_list = checked_run(["docker", "image", "ls",
                                    "--filter", "reference=" + image,
                                    "--format", "{{.Repository}}:{{.Tag}}"], timeout=15)
            if image in tag_list.splitlines():
                raise SmokeRefused("G235_IMAGE_TAG_COLLISION")
            checked_run(["docker", "build", "--pull=false", "--network=none",
                         "--no-cache", "--tag", image, str(base)], timeout=75)
            created_image = True
            image_sha = checked_run(["docker", "image", "inspect",
                                     image, "--format", "{{.Id}}"], timeout=15)
            if not (image_sha.startswith("sha256:") and len(image_sha) == 71):
                raise SmokeRefused("G235_IMAGE_DIGEST_REFUSED")
            cid = checked_run(["docker", "create", "--network", "none",
                               "--read-only", "--cap-drop", "ALL",
                               "--security-opt", "no-new-privileges:true",
                               "--pids-limit", "32", "--memory", "64m",
                               "--cpus", "0.25", "--user", "65534:65534",
                               image_sha], timeout=15)
            inspect(cid, started=False)
            output = checked_run(["docker", "start", "--attach", cid], timeout=12)
            inspect(cid, started=True)
            output_sha = verify_output(output)
            # No image mutation, no unverified Docker result promoted to NAS.
            if checked_run(["docker", "image", "inspect", image, "--format",
                            "{{.Id}}"], timeout=15) != image_sha:
                raise SmokeRefused("G235_IMAGE_CHANGED")
            if (hashlib.sha256(source.read_bytes()).hexdigest() != source_sha
                    or hashlib.sha256(plan.read_bytes()).hexdigest() != plan_sha):
                raise SmokeRefused("G235_SOURCE_MUTATED")
            checked_run(["docker", "rm", cid], timeout=15)
            cid = None
            return {
                "schema": SCHEMA, "status": "REAL_DOCKER_FIXED_TYPED_DAG_PASS",
                "typed_nodes_executed": list(STEPS),
                "source_sha256": source_sha, "plan_sha256": plan_sha,
                "receipt_sha256": output_sha, "image_sha256": image_sha[7:],
                "source_rows": 3, "output_rows": 2,
                "local_docker_executed": True,
                "safety": "NO_NETWORK_NO_MOUNTS_NO_PULL_NONROOT_READONLY",
                "general_automation_verified": False,
                "independent_ai_agents_used": False,
                "owner_files_opened": False,
                "uliya_expert_invoked": False, "nas_verified": False,
                "release_gate": "HOLD",
            }
    finally:
        if cid is not None:
            try:
                checked_run(["docker", "rm", "-f", cid], timeout=12)
            except SmokeRefused:
                pass
        if created_image:
            try:
                checked_run(["docker", "image", "rm", image], timeout=12)
            except SmokeRefused:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixed synthetic Docker DAG only; NOT NAS")
    parser.add_argument(APPROVAL, action="store_true")
    args = parser.parse_args(argv)
    if not getattr(args, "approve_synthetic_typed_docker"):
        print(json.dumps({"status": "G235_EXPLICIT_SYNTHETIC_APPROVAL_REQUIRED",
                          "nas_verified": False, "release_gate": "HOLD"}))
        return 2
    try:
        result = run_fixed_dag()
    except SmokeRefused as exc:
        print(json.dumps({"status": "G235_DOCKER_NOT_VERIFIED",
                          "reason": str(exc), "nas_verified": False,
                          "release_gate": "HOLD"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
