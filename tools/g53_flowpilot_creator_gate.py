"""G53 fail-closed review of OFFICIAL CREATOR operator-provided output.

No installed Codex/Claude/WorkBuddy, vendor kit or NAS execution happens here.
The operator's JSON is an untrusted attestation, NOT cryptographic proof that
the official UGREEN Skill Creation Tool ran. Public submission must remain HOLD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Any

EXPECTED_SKILL_SHA = "47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"
EXPECTED_KIT_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
NAME = "flowpilot-nas"
MAX_BYTES = 1_000_000
SHA = re.compile(r"^[0-9a-f]{64}$")


def review_creator_evidence(source: bytes | None, declaration: Mapping[str, Any] | None) -> dict:
    """Return a pure, non-releasing machine gate (no raw source/path disclosure)."""
    result = {
        "candidate": NAME,
        "current_reviewed_skill_sha256": EXPECTED_SKILL_SHA,
        "official_creator_execution_independently_verified": False,
        "live_nas_verified": False,
        "owner_release_approved": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }
    if source is None or declaration is None:
        return {**result, "status": "CREATOR_NOT_EVIDENCED"}
    if not isinstance(source, bytes) or not source or len(source) > MAX_BYTES:
        return {**result, "status": "INVALID_SOURCE"}
    try:
        decoded = source.decode("utf-8")
    except UnicodeDecodeError:
        return {**result, "status": "INVALID_SOURCE"}
    if re.match(r"\A---\r?\nname: flowpilot-nas\r?\n", decoded) is None:
        return {**result, "status": "WRONG_SKILL_ID"}
    actual_hash = hashlib.sha256(source).hexdigest()
    result["actual_generated_sha256"] = actual_hash
    if not isinstance(declaration, Mapping):
        return {**result, "status": "INVALID_DECLARATION"}
    required = ("kit_sha256", "generated_skill_sha256", "checker_skill_sha256",
                "generation_performed", "official_tool_loaded", "checker_status",
                "checker_errors", "checker_warnings", "checker_info")
    if any(key not in declaration for key in required):
        return {**result, "status": "INCOMPLETE_CREATOR_REPORT"}
    digests = [declaration.get(k) for k in ("kit_sha256", "generated_skill_sha256", "checker_skill_sha256")]
    if not all(isinstance(v, str) and SHA.fullmatch(v) for v in digests):
        return {**result, "status": "INVALID_SHA_FORMAT"}
    if declaration["kit_sha256"] != EXPECTED_KIT_SHA:
        return {**result, "status": "KIT_VERSION_REVIEW_REQUIRED"}
    if declaration["official_tool_loaded"] is not True or declaration["generation_performed"] is not True:
        return {**result, "status": "CREATOR_NOT_EVIDENCED"}
    if declaration["generated_skill_sha256"] != actual_hash:
        return {**result, "status": "GENERATED_SOURCE_SHA_MISMATCH"}
    if declaration["checker_skill_sha256"] != actual_hash:
        return {**result, "status": "CHECKER_SOURCE_SHA_MISMATCH"}
    if (declaration["checker_status"] != "static-pass"
        or any(type(declaration[k]) is not int or declaration[k] != 0
               for k in ("checker_errors", "checker_warnings", "checker_info"))):
        return {**result, "status": "CHECKER_RESULT_NOT_CLEAN"}
    if actual_hash != EXPECTED_SKILL_SHA:
        return {**result, "status": "GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED"}
    # A source-matched self-attested local report cannot prove which tool
    # generated it, establish ownership, or authorize a Devpost submission.
    return {**result, "status": "SOURCE_MATCHED_OPERATOR_ATTESTATION_ONLY"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline FlowPilot Creator evidence boundary")
    parser.add_argument("--generated-skill", type=Path)
    parser.add_argument("--operator-receipt", type=Path)
    args = parser.parse_args()
    if (args.generated_skill is None) != (args.operator_receipt is None):
        parser.error("Both --generated-skill and --operator-receipt must be provided")
    if args.generated_skill is None:
        report = review_creator_evidence(None, None)
    else:
        p, receipt = args.generated_skill, args.operator_receipt
        if p.is_symlink() or p.name != "SKILL.md" or not p.is_file() or p.stat().st_size > MAX_BYTES:
            parser.error("Select a regular bounded SKILL.md only")
        if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 10_000:
            parser.error("Select a regular bounded operator JSON receipt")
        try:
            data = json.loads(receipt.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            parser.error("Invalid receipt JSON")
        report = review_creator_evidence(p.read_bytes(), data)
    print(json.dumps(report, indent=2))
    # This command never emits a release PASS. Status 0 means report rendered,
    # not creator authorization.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
