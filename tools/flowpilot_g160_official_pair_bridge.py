"""G160: connect exact unapproved G158 owner review pair to authentic Uliya Kit.

Default verifies private pair and documentary parity only. Never downloads,
uploads, executes vendor JS without a distinct explicit user-local switch,
calls NAS, or submits to Devpost. An official static pass never lifts HOLD.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

import flowpilot_g158_review_pair as pair
import flowpilot_g159_claims_rights_gate as claims
import flowpilot3_official_checker as official


class BridgeRefused(ValueError):
    """Sanitized local refusal, no original owner paths/content."""


def _read_local(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise BridgeRefused("LOCAL_INPUT_MISSING_OR_SYMLINK")
    try:
        size = path.stat().st_size
        if not 0 < size <= limit:
            raise BridgeRefused("LOCAL_FILE_SIZE_REFUSED")
        raw = path.read_bytes()
        if not 0 < len(raw) <= limit:
            raise BridgeRefused("LOCAL_FILE_SIZE_REFUSED")
        return raw
    except OSError as exc:
        raise BridgeRefused("LOCAL_INPUT_UNAVAILABLE") from exc


def audit(package_path: Path, kit_path: Path | None = None, *,
          execute_official_native_code: bool = False) -> dict:
    if type(execute_official_native_code) is not bool:
        raise BridgeRefused("INVALID_RISK_FLAG")
    # Never run third-party code or touch an unknown kit without an exact
    # private pair + written PDF/Skill claim parity.
    raw = _read_local(package_path, pair.MAX_BUNDLE)
    verified = pair.verify_package(raw)
    documentary = claims.review_package(raw)
    if (verified.get("release_gate") != "HOLD" or
            documentary.get("release_gate") != "HOLD" or
            documentary.get("documentary_claims_cross_referenced") != 7):
        raise BridgeRefused("G158_DOCUMENTARY_GATE_INCOMPLETE")
    if execute_official_native_code and kit_path is None:
        raise BridgeRefused("OFFICIAL_KIT_REQUIRED_BEFORE_NATIVE_CODE")
    base = {
        "schema": "flowpilot-g160-official-owner-pair-bridge-v1",
        "candidate": "EXACT_G158_G157_PDF_G147_SKILL_UNAPPROVED",
        "candidate_pdf_sha256": pair.PDF_PIN,
        "candidate_skill_zip_sha256": pair.SKILL_PIN,
        "documentary_claims_checked": 7,
        "first_party_vendor_zip_authenticated": False,
        "official_checker_executed": False,
        "registered_expert_verified": False,
        "real_nas_verified": False,
        "owner_rights_approved": False,
        "devpost_submitted": False,
        "private_artifacts_uploaded": False,
        "release_gate": "HOLD",
    }
    if kit_path is None:
        return {**base, "status": "EXACT_OWNER_PAIR_VERIFIED_OFFICIAL_KIT_MISSING"}
    kit = _read_local(kit_path, official.MAX_VENDOR)
    if sha256(kit).hexdigest() != official.VENDOR_ZIP_SHA:
        raise BridgeRefused("AUTHENTIC_ULIYA_KIT_SHA256_MISMATCH")
    # Original Skill file is *exactly* G147 SHA-pinned ZIP; G157 PDF does not
    # change the official Checker input. Stage only the ZIP in disposable temp.
    with ZipFile(BytesIO(raw)) as z:
        skill = z.read(pair.SKILL_ENTRY)
    if sha256(skill).hexdigest() != official.G147_CANDIDATE_ZIP_SHA:
        raise BridgeRefused("OFFICIAL_CANDIDATE_PROFILE_DRIFT")
    with tempfile.TemporaryDirectory(prefix="ugreen-g160-owner-") as d:
        candidate_path = Path(d) / "exact-g147-skill.zip"
        candidate_path.write_bytes(skill)
        # Official upstream helper authenticates both complete ZIP archives,
        # checks all expected Markdown source hashes and inspects vendor catalog.
        result = official.check(
            candidate_path, kit_path,
            mode="native" if execute_official_native_code else "inspect",
            native_risk_approved=execute_official_native_code,
            candidate_profile="g147",
        )
    if not execute_official_native_code:
        if (result.get("status") != "EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN"
                or result.get("official_checker_executed") is not False):
            raise BridgeRefused("VENDOR_INSPECT_STATUS_UNEXPECTED")
        return {**base,
                "status": "G158_AUTHENTIC_ULIYA_KIT_INSPECTED_NO_VENDOR_CODE",
                "first_party_vendor_zip_authenticated": True}
    if (result.get("status") != "OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE"
            or result.get("official_checker_executed") is not True):
        raise BridgeRefused("FIRST_PARTY_RUN_NOT_CONFIRMED")
    allowed = ("result", "checker_exit_code", "checker_status", "checker_summary",
               "diagnostic_codes", "checker_stderr_present", "mode")
    minimal = {key: result[key] for key in allowed if key in result}
    passed = result.get("result") == "OFFICIAL_STATIC_PASS_REVIEW_ONLY"
    return {**base, **minimal,
            "status": "G158_FIRST_PARTY_CHECKER_STATIC_PASS_OWNER_REVIEW_ONLY"
                      if passed else "G158_FIRST_PARTY_CHECKER_WARN_OR_FAIL_HOLD",
            "first_party_vendor_zip_authenticated": True,
            "official_checker_executed": True, "release_gate": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G160 G158 owner-only Uliya bridge; never Devpost approval")
    parser.add_argument("--review-package", type=Path, required=True)
    parser.add_argument("--official-kit-zip", type=Path)
    parser.add_argument("--execute-official-native-code", action="store_true",
                        help="Only after separate entrant authorization: runs real vendor Node JS")
    a = parser.parse_args(argv)
    try:
        report = audit(a.review_package, a.official_kit_zip,
                       execute_official_native_code=a.execute_official_native_code)
        code = 2 if a.execute_official_native_code and report.get("result") != "OFFICIAL_STATIC_PASS_REVIEW_ONLY" else 0
    except (BridgeRefused, pair.PairRefused, claims.ClaimsRefused,
            official.VerificationRefused, OSError, ValueError, RuntimeError) as exc:
        report = {
            "schema": "flowpilot-g160-official-owner-pair-bridge-v1",
            "status": "G160_OWNER_OFFICIAL_BRIDGE_REFUSED",
            "reason": type(exc).__name__,
            "official_checker_executed": False,
            "release_gate": "HOLD",
            "private_artifacts_uploaded": False,
        }
        code = 2
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
