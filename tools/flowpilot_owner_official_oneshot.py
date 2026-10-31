"""G150 single-entry owner-local G147 preflight and optional official Uliya Checker.

No private candidate/owner bytes are uploaded. Network only downloads the
exact public vendor URL after explicit --download-official-kit. Vendor JS runs
only after independent --execute-official-native-code approval. The vendor
archive is authenticated by the pre-established SHA256 and never committed.

This is not a developer-provided Uliya Checker and does not run a NAS.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
import urllib.request

import flowpilot3_official_checker as official
import flowpilot_artifact_manifest_gate as local_gate

VENDOR_URL = (
    "https://cdn.shopify.com/s/files/1/0630/9416/1602/files/"
    "uliya-skill-kit-0.7.3-en.zip?v=1790578898"
)
VENDOR_MAX = official.MAX_VENDOR
PDF_FILE = "FlowPilot3_G147_RULES_ALIGNED_OWNER_REVIEW_NOT_SUBMITTED.pdf"
ZIP_FILE = "FlowPilot3_G147_RULES_ALIGNED_OWNER_REVIEW_NOT_SUBMITTED.zip"
MANIFEST_FILE = "G147_OWNER_REVIEW_MANIFEST_NOT_SUBMITTED.json"


class OwnerCheckRefused(ValueError):
    """Expected sanitized refusal. Never include private text or paths."""


def _read_file(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise OwnerCheckRefused("MISSING_OR_UNSAFE_OWNER_INPUT")
    stat = path.stat()
    if not 0 < stat.st_size <= limit:
        raise OwnerCheckRefused("OWNER_INPUT_SIZE_REFUSED")
    raw = path.read_bytes()
    if not 0 < len(raw) <= limit:
        raise OwnerCheckRefused("OWNER_INPUT_SIZE_REFUSED")
    return raw


class _OfficialHostOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != "cdn.shopify.com":
            raise OwnerCheckRefused("VENDOR_REDIRECT_DOMAIN_REFUSED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_authenticated_kit() -> bytes:
    """Public download only; no candidate/body/secret/query from owner."""
    url = urlsplit(VENDOR_URL)
    if (url.scheme != "https" or url.hostname != "cdn.shopify.com"
            or not url.path.endswith("/uliya-skill-kit-0.7.3-en.zip")):
        raise OwnerCheckRefused("VENDOR_URL_NOT_CANONICAL")
    opener = urllib.request.build_opener(_OfficialHostOnly)
    try:
        with opener.open(VENDOR_URL, timeout=25) as response:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "cdn.shopify.com":
                raise OwnerCheckRefused("VENDOR_REDIRECT_DOMAIN_REFUSED")
            data = bytearray()
            while True:
                chunk = response.read(min(65536, VENDOR_MAX + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > VENDOR_MAX:
                    raise OwnerCheckRefused("VENDOR_SIZE_LIMIT")
    except OwnerCheckRefused:
        raise
    except (OSError, ValueError, TimeoutError) as exc:
        raise OwnerCheckRefused("VENDOR_DOWNLOAD_UNAVAILABLE") from exc
    raw = bytes(data)
    if sha256(raw).hexdigest() != official.VENDOR_ZIP_SHA:
        raise OwnerCheckRefused("VENDOR_SHA256_MISMATCH")
    return raw


def verify_owner_pair(directory: Path, *, pdf_text: bool = False) -> dict:
    pdf = _read_file(directory / PDF_FILE, 1_000_000)
    zip_raw = _read_file(directory / ZIP_FILE, 10_000_000)
    manifest = _read_file(directory / MANIFEST_FILE, 64000)
    result = local_gate.verify_g147_candidate(
        pdf, zip_raw, manifest, require_pdf_text=pdf_text)
    return result


def run(directory: Path, *, download_official_kit: bool = False,
        execute_official_native_code: bool = False,
        require_pdf_text: bool = False,
        official_kit_zip: Path | None = None) -> dict:
    if any(type(x) is not bool for x in (
            download_official_kit, execute_official_native_code,
            require_pdf_text)):
        raise OwnerCheckRefused("INVALID_EXPLICIT_PERMISSION")
    if official_kit_zip is not None and not isinstance(official_kit_zip, Path):
        raise OwnerCheckRefused("INVALID_LOCAL_VENDOR_PATH")
    if official_kit_zip is not None and download_official_kit:
        raise OwnerCheckRefused("CHOOSE_ONE_VENDOR_SOURCE")
    if (execute_official_native_code and not download_official_kit
            and official_kit_zip is None):
        raise OwnerCheckRefused("VENDOR_EXECUTION_NEEDS_VERIFIED_KIT_SOURCE")
    pair = verify_owner_pair(directory, pdf_text=require_pdf_text)
    if pair.get("status") != "G147_EXACT_LOCAL_PAIR_VERIFIED_NOT_OFFICIAL":
        raise OwnerCheckRefused("LOCAL_OWNER_PAIR_NOT_VERIFIED")
    base = {
        "schema": "flowpilot-g150-owner-one-shot-g147-v1",
        "candidate": "G147_EXACT_PINNED_OWNER_PRIVATE",
        "local_pdf_zip_manifest_verified": True,
        "local_pdf_text_verified": pair.get("pdf_text_verified") is True,
        "official_vendor_digest_verified": False,
        "official_checker_executed": False,
        "real_nas_verified": False,
        "registered_expert_verified": False,
        "owner_rights_approved": False,
        "devpost_submitted": False,
        "private_artifacts_uploaded": False,
        "release_gate": "HOLD",
    }
    if not download_official_kit and official_kit_zip is None:
        return {**base, "status": "G147_LOCAL_PRECHECK_ONLY_NO_NETWORK"}
    if official_kit_zip is not None:
        vendor = _read_file(official_kit_zip, VENDOR_MAX)
        if sha256(vendor).hexdigest() != official.VENDOR_ZIP_SHA:
            raise OwnerCheckRefused("LOCAL_VENDOR_SHA256_MISMATCH")
        vendor_origin = "OWNER_PROVIDED_OFFICIAL_KIT"
    else:
        vendor = _download_authenticated_kit()
        vendor_origin = "UGREEN_LINKED_PUBLIC_CDN"
    with tempfile.TemporaryDirectory(prefix="g150-private-verify-") as tmp:
        vendor_path = Path(tmp) / "authenticated-official-kit.zip"
        vendor_path.write_bytes(vendor)
        if not execute_official_native_code:
            check_result = official.check(
                directory / ZIP_FILE, vendor_path,
                mode="inspect", candidate_profile="g147")
            if check_result.get("official_checker_executed") is not False:
                raise OwnerCheckRefused("UNEXPECTED_CHECKER_EXECUTION")
            return {**base,
                    "status": "G147_VENDOR_BYTES_AUTHENTIC_LOCAL_CHECKER_NOT_RUN",
                    "official_vendor_digest_verified": True,
                    "vendor_source": vendor_origin}
        checked = official.check(
            directory / ZIP_FILE, vendor_path, mode="native",
            native_risk_approved=True, candidate_profile="g147")
        if (checked.get("status") != "OFFICIAL_CHECKER_EXECUTED_WITH_PINNED_SOURCE"
                or checked.get("official_checker_executed") is not True):
            raise OwnerCheckRefused("OFFICIAL_CHECKER_NO_EXACT_RESULT")
        return {**base,
                "status": "G147_OFFICIAL_CHECKER_EXECUTED_OWNER_REVIEW_ONLY",
                "official_vendor_digest_verified": True,
                "vendor_source": vendor_origin,
                "official_checker_executed": True,
                "checker_result": checked.get("result"),
                "checker_summary": checked.get("checker_summary"),
                "diagnostic_codes": checked.get("diagnostic_codes"),
                "checker_exit_code": checked.get("checker_exit_code"),
                "checker_stderr_present": checked.get("checker_stderr_present")}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=(
        "G150 owner-local G147 exact pair preflight and optional official checker. "
        "No NAS, no uploads, release always HOLD."))
    p.add_argument("--folder", type=Path, default=Path(__file__).resolve().parent,
                   help="Folder containing exact G147 pdf, zip and corrected manifest")
    p.add_argument("--require-pdf-text", action="store_true",
                   help="Require local PyMuPDF and check actual PDF text")
    p.add_argument("--download-official-kit", action="store_true",
                   help="Authorize public HTTPS GET to UGREEN-linked Shopify CDN")
    p.add_argument("--official-kit-zip", type=Path,
                   help="Use already downloaded SHA256-pinned vendor ZIP locally; "
                        "no CDN request; mutually exclusive with download")
    p.add_argument("--execute-official-native-code", action="store_true",
                   help="Separately authorize executing authenticated UGREEN JS via installed Node")
    args = p.parse_args(argv)
    try:
        result = run(args.folder, download_official_kit=args.download_official_kit,
                     execute_official_native_code=args.execute_official_native_code,
                     require_pdf_text=args.require_pdf_text,
                     official_kit_zip=args.official_kit_zip)
    except (OwnerCheckRefused, local_gate.ArtifactRefused,
            official.VerificationRefused, OSError, ValueError,
            ImportError, RuntimeError) as exc:
        result = {
            "schema": "flowpilot-g150-owner-one-shot-g147-v1",
            "status": "G147_OWNER_LOCAL_CHECK_REFUSED",
            "reason": type(exc).__name__,
            "official_checker_executed": False,
            "private_artifacts_uploaded": False,
            "release_gate": "HOLD",
        }
        exit_code = 2
    else:
        exit_code = 0 if result["status"] in (
            "G147_LOCAL_PRECHECK_ONLY_NO_NETWORK",
            "G147_VENDOR_BYTES_AUTHENTIC_LOCAL_CHECKER_NOT_RUN",
        ) or (result["status"] == "G147_OFFICIAL_CHECKER_EXECUTED_OWNER_REVIEW_ONLY"
              and result.get("checker_result") == "OFFICIAL_STATIC_PASS_REVIEW_ONLY") else 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
