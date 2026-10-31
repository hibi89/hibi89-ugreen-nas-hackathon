"""G100: SHA-pinned offline Uliya Checker runner for a retained G99 candidate.

The public repo contains only this code, NOT the private-to-operator candidate,
the vendor kit or any real NAS paths. Never uploads data or authorizes release.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
from zipfile import BadZipFile, ZipFile

CANDIDATE_SHA = "f21c184f4a0bf370d438b3918a345870faf9d69ee88aac239fe13241a8960ca6"
CANDIDATE_ZIP_SHA = "f28acfbeba9d3a6e33b9977d1ea1de15b50ca48dbc505144c0b2cb719efc2cfc"
G103_CANDIDATE_SHA = "f940bcd884b83d80fbecf533caee7d492488c274e1d3eab2b99b034b92428e15"
G103_CANDIDATE_ZIP_SHA = "1496103b5c1b15da113867ed0cab57ad1e2dab0be80c2f06fd049cac359bf11b"
# G141 exact owner-review G139 private candidate; never place ZIP bytes in public GitHub.
G139_CANDIDATE_SHA = "a13e07121e3e72b49300e0e5581ecf9d9edfd09e1fb69d481f3b2a811d6cb063"
G139_CANDIDATE_ZIP_SHA = "fb948d50be12f548ad48dd527cd858f3d5e5e73fd611de2a502f89acff8478e1"
G139_MEMBERS = (
    "flowpilot-3/SKILL.md",
    "flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md",
    "flowpilot-3/references/SAFETY_AND_SCENARIOS.md",
)
VENDOR_ZIP_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
MEMBER = "flowpilot-3/SKILL.md"
MAX_CANDIDATE = 10_000_000
MAX_VENDOR = 20_000_000
MAX_VENDOR_UNCOMPRESSED = 64_000_000
MAX_VENDOR_ENTRY = 8_000_000
MAX_VENDOR_MEMBERS = 1000


class VerificationRefused(ValueError):
    """Safe refusal without disclosing source/paths/secret-bearing content."""


def _read_pinned(path: Path, *, digest: str, size_limit: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= size_limit:
        raise VerificationRefused("Missing, nonregular or oversized pinned archive")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise VerificationRefused("Pinned archive SHA256 mismatch")
    return raw


def _safe_names(z: ZipFile, *, count: int, expanded: int, per_entry: int) -> list:
    members = z.infolist()
    if not members or len(members) > count or sum(x.file_size for x in members) > expanded:
        raise VerificationRefused("ZIP count/expansion budget exceeded")
    seen: set[str] = set()
    for info in members:
        path = info.filename
        parts = path.rstrip("/").split("/")
        key = path.rstrip("/").casefold()
        if (not path or path.startswith("/") or "\\" in path or ":" in path
                or any(part in ("", ".", "..") for part in parts)
                or any(ord(c) < 32 or ord(c) == 127 for c in path)
                or key in seen or info.flag_bits & 1
                or info.file_size > per_entry
                or stat.S_ISLNK(info.external_attr >> 16)):
            raise VerificationRefused("Unsafe ZIP metadata")
        seen.add(key)
    return members


def inspect_pinned_archives(candidate_zip: bytes, vendor_zip: bytes, *,
                            expected_source_sha: str | None = None,
                            expected_members: tuple[str, ...] = (MEMBER,)) -> dict:
    if expected_source_sha is None:
        expected_source_sha = CANDIDATE_SHA  # Legacy G99 regression compatibility.
    try:
        with ZipFile(BytesIO(candidate_zip)) as z:
            names = _safe_names(z, count=100, expanded=10_000_000, per_entry=1_000_000)
            if (not expected_members or len(set(expected_members)) != len(expected_members)
                    or set(x.filename for x in names) != set(expected_members)
                    or any(x.is_dir() for x in names)
                    or not all(x == MEMBER or (x.startswith("flowpilot-3/references/")
                               and x.endswith(".md")) for x in expected_members)):
                raise VerificationRefused("Candidate must contain exact Markdown members (exact approved set)")
            candidate = z.read(MEMBER)
            if sha256(candidate).hexdigest() != expected_source_sha:
                raise VerificationRefused("Candidate Skill bytes differ from exact selected source pin")
        with ZipFile(BytesIO(vendor_zip)) as z:
            members = _safe_names(z, count=MAX_VENDOR_MEMBERS,
                                  expanded=MAX_VENDOR_UNCOMPRESSED, per_entry=MAX_VENDOR_ENTRY)
            checkers = [x.filename for x in members if x.filename.endswith("scripts/check-skill.mjs")]
            if len(checkers) != 1:
                raise VerificationRefused("One official check-skill.mjs required")
            root = checkers[0][:-len("scripts/check-skill.mjs")].rstrip("/")
            prefix = root + "/" if root else ""
            if not any(x.filename == prefix + "SKILL.md" for x in members):
                raise VerificationRefused("Official tool root is incomplete")
            if not any(x.filename == prefix + "data/capability-catalog.json" for x in members):
                raise VerificationRefused("Official capability catalog missing")
            if z.testzip() is not None:
                raise VerificationRefused("Vendor ZIP corruption")
    except (BadZipFile, RuntimeError, OSError) as exc:
        raise VerificationRefused("Invalid pinned ZIP archive") from exc
    return {"source_sha256": expected_source_sha, "vendor_archive_sha256": VENDOR_ZIP_SHA,
            "checker_relative_root": root, "member_count": len(members),
            "candidate_member_count": len(expected_members)}


def _prepare_toolkit(vendor_zip: bytes, extracted: Path, root: str) -> Path:
    """Use the inspected pinned ZIP only, in a disposable folder."""
    with ZipFile(BytesIO(vendor_zip)) as z:
        z.extractall(extracted)
    vendor = extracted / root if root else extracted
    if not (vendor / "scripts/check-skill.mjs").is_file():
        raise VerificationRefused("Checker missing after safe extraction")
    return vendor


def _execute(vendor: Path, candidate: Path, *, mode: str) -> tuple[int, str, str]:
    if mode == "docker":
        if not shutil.which("docker"):
            raise VerificationRefused("Docker not installed; no fallback")
        image = "node:22-alpine"
        inspect = subprocess.run(["docker", "image", "inspect", image], capture_output=True,
                                 timeout=20, check=False)
        if inspect.returncode != 0:
            raise VerificationRefused("Pinned Docker image not present; no automatic download")
        cmd = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--pids-limit", "96", "--memory", "384m", "--cpus", "1",
               "--user", "65534:65534", "-v", str(vendor) + ":/vendor:ro",
               "-v", str(candidate) + ":/candidate/flowpilot-3:ro",
               "--workdir", "/candidate", image, "node",
               "/vendor/scripts/check-skill.mjs", "/candidate/flowpilot-3"]
    elif mode == "native":
        node = shutil.which("node")
        if not node:
            raise VerificationRefused("Node 22+ is not installed; no fallback")
        cmd = [node, str(vendor / "scripts/check-skill.mjs"), str(candidate)]
    else:
        raise VerificationRefused("Unknown checker execution mode")
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(vendor.parent),
           "TEMP": str(vendor.parent), "TMP": str(vendor.parent),
           "NODE_ENV": "production"}
    try:
        result = subprocess.run(cmd, cwd=vendor.parent, env=env, capture_output=True,
                                timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerificationRefused("Official checker failed or timed out") from exc
    if len(result.stdout) > 100_000 or len(result.stderr) > 100_000:
        raise VerificationRefused("Official checker output limit exceeded")
    return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")


def _sanitized_checker_result(code: int, stdout: str, stderr: str, *, mode: str) -> dict:
    def unique_pairs(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("Duplicate Checker JSON key")
            obj[key] = value
        return obj

    def reject_nonfinite(value):
        raise ValueError("Nonfinite Checker JSON number")

    try:
        data = json.loads(stdout, object_pairs_hook=unique_pairs,
                          parse_constant=reject_nonfinite)
    except (ValueError, RecursionError):
        data = None
    if not isinstance(data, dict):
        return {"result": "UNVERIFIED_NON_JSON_CHECKER_OUTPUT", "checker_exit_code": code,
                "checker_stdout_sha256": sha256(stdout.encode()).hexdigest(),
                "checker_stderr_present": bool(stderr.strip()),
                "official_checker_executed": True, "release_gate": "HOLD"}
    summary = data.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    numbers = {k: summary.get(k) for k in ("errors", "warnings", "info")}
    valid_numbers = all(type(value) is int and value >= 0 for value in numbers.values())
    diagnostics = data.get("diagnostics")
    # A zero-count summary can still conceal an error diagnostic. Refuse all
    # inconsistent or missing diagnostic collections instead of claiming PASS.
    diagnostics_complete = isinstance(diagnostics, list)
    diagnostics_empty = diagnostics_complete and len(diagnostics) == 0
    diagnostic_codes = [str(d.get("code"))[:80] for d in diagnostics[:40]
                        if isinstance(d, dict) and isinstance(d.get("code"), str)] if isinstance(diagnostics, list) else []
    # A silent stdout PASS with warnings/errors on stderr is not a clean vendor run.
    # Keep the boundary equivalent to the historical G45 isolated first-party gate.
    clean = (code == 0 and not stderr.strip()
             and data.get("status") == "static-pass" and valid_numbers
             and all(value == 0 for value in numbers.values()) and diagnostics_empty)
    return {"result": "OFFICIAL_STATIC_PASS_REVIEW_ONLY" if clean else "OFFICIAL_WARN_OR_FAIL_HOLD",
            "checker_exit_code": code, "checker_status": str(data.get("status"))[:100],
            "checker_summary": numbers if valid_numbers else "UNVERIFIED_SUMMARY",
            "diagnostic_codes": diagnostic_codes,
            "diagnostics_consistent_with_zero_summary": diagnostics_empty,
            "checker_stderr_present": bool(stderr.strip()), "mode": mode,
            "official_checker_executed": True, "registered_expert_verified": False,
            "real_nas_verified": False, "owner_release_approved": False,
            "devpost_submitted": False, "release_gate": "HOLD"}


def check(candidate: Path, kit: Path, *, mode: str, native_risk_approved: bool = False,
          candidate_profile: str = "g99") -> dict:
    if mode not in ("inspect", "docker", "native"):
        raise VerificationRefused("Invalid execution mode")
    if mode == "native" and not native_risk_approved:
        raise VerificationRefused("Native execution requires explicit risk approval")
    # Profiles are immutable source/ZIP pairs; untrusted CLI users cannot supply arbitrary hashes.
    profiles = {"g99": (CANDIDATE_SHA, CANDIDATE_ZIP_SHA, (MEMBER,)),
                "g103": (G103_CANDIDATE_SHA, G103_CANDIDATE_ZIP_SHA, (MEMBER,)),
                "g139": (G139_CANDIDATE_SHA, G139_CANDIDATE_ZIP_SHA, G139_MEMBERS)}
    if candidate_profile not in profiles:
        raise VerificationRefused("Unsupported exact candidate profile")
    expected_source, expected_zip, expected_members = profiles[candidate_profile]
    candidate_bytes = _read_pinned(candidate, digest=expected_zip, size_limit=MAX_CANDIDATE)
    vendor_bytes = _read_pinned(kit, digest=VENDOR_ZIP_SHA, size_limit=MAX_VENDOR)
    details = inspect_pinned_archives(candidate_bytes, vendor_bytes,
                                      expected_source_sha=expected_source,
                                      expected_members=expected_members)
    details["candidate_profile"] = candidate_profile
    if mode == "inspect":
        return {"status": "EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN",
                **details, "official_checker_executed": False, "release_gate": "HOLD"}
    with tempfile.TemporaryDirectory(prefix="ugreen-g100-check-") as temp:
        base = Path(temp)
        skill = base / "candidate" / "flowpilot-3"
        skill.mkdir(parents=True)
        member_hashes = {}
        with ZipFile(BytesIO(candidate_bytes)) as z:
            # Only exact, already verified relative paths; no extractall for candidate.
            for name in expected_members:
                target = base / "candidate" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                blob = z.read(name)
                target.write_bytes(blob)
                member_hashes[name] = sha256(blob).hexdigest()
        vendor = _prepare_toolkit(vendor_bytes, base / "official", details["checker_relative_root"])
        code, stdout, stderr = _execute(vendor, skill, mode=mode)
        if any(sha256((base / "candidate" / name).read_bytes()).hexdigest() != digest
               for name, digest in member_hashes.items()):
            raise VerificationRefused("Candidate files changed during Checker run")
        return {"status": "OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE", **details,
                **_sanitized_checker_result(code, stdout, stderr, mode=mode)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G100 local official Uliya checker gate (no NAS/Devpost)")
    parser.add_argument("--candidate-zip", type=Path, required=True)
    parser.add_argument("--official-kit-zip", type=Path, required=True)
    parser.add_argument("--mode", choices=("inspect", "docker", "native"), default="inspect")
    parser.add_argument("--candidate-profile", choices=("g99", "g103", "g139"), default="g99",
                        help="Select exact reviewed source/ZIP pins; no arbitrary hash overrides")
    parser.add_argument("--accept-native-code-execution-risk", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = check(args.candidate_zip, args.official_kit_zip, mode=args.mode,
                       native_risk_approved=args.accept_native_code_execution_risk,
                       candidate_profile=args.candidate_profile)
        exit_code = 0 if report.get("result") == "OFFICIAL_STATIC_PASS_REVIEW_ONLY" else 2
    except (VerificationRefused, OSError, ValueError) as exc:
        report = {"status": "CHECKER_NOT_VERIFIED", "reason": type(exc).__name__,
                  "message": str(exc) if isinstance(exc, VerificationRefused) else "Local input not accessible",
                  "release_gate": "HOLD", "official_checker_executed": False}
        exit_code = 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
