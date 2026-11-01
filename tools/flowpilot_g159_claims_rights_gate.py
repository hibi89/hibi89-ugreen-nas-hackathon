"""G159: cross-reference EXACT G158 review pair claims against packaged Skill text.

This is a static internal evidence ledger, not a legal license clearance,
originality proof, official Uliya Checker, NAS run, or Devpost release.
No private candidate bytes, user paths, or excerpts are emitted or committed.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import flowpilot_g158_review_pair as pair


class ClaimsRefused(ValueError):
    """Fail closed with redacted operational results."""


# All phrases are case-insensitive; these checks establish documentary parity
# for a SHA-pinned exact file pair, not that an external service actually works.
CLAIMS = {
    "scope_and_consent": (
        ("one folder", "confirm scope", "explicit"),
        ("limit a run to one folder", "never infer consent"),
    ),
    "four_internal_review_perspectives": (
        ("architect", "security", "builder", "qa", "not separate"),
        ("architect:", "security:", "builder:", "qa:", "not four separately registered agents"),
    ),
    "conditional_registered_experts": (
        ("subject to registration", "file-agent", "document-agent"),
        ("registered", "file-agent", "document-agent", "if"),
    ),
    "plan_only_for_unsupported_work": (
        ("design_only", "no shell", "not simulated nas execution"),
        ("design_only", "not_execUTABLE_on_current_capabilities".lower()),
    ),
    "honest_unverified_runtime_status": (
        ("first-party checker", "remain unverified", "not uliya runtime results"),
        ("not passed an independently executed first-party", "no native expert permissions"),
    ),
    "ai_and_third_party_disclosure": (
        ("openai chatgpt", "no third-party code or models"),
        ("ai tools and principal uses", "third-party components/open-source libraries included"),
    ),
    "rights_pending_not_cleared": (
        ("owner must confirm", "rights", "licenses"),
        ("rights check still required", "before submission"),
    ),
}
ATTESTATIONS = (
    "entrant_original_authorship_and_rights",
    "ai_assistance_declaration_and_editorial_accuracy",
    "ugreen_license_privacy_and_skill_publishing_terms",
    "exact_final_pdf_and_skill_approval",
)
EXTERNAL_GATES = (
    "authentic_ugreen_creation_tool_and_first_party_checker",
    "actual_registered_expert_availability_and_processing_location",
    "explicit_devpost_release",
)


def compare_text(pdf_text: str, skill_text: str, member_names: tuple[str, ...]) -> dict:
    if not isinstance(pdf_text, str) or not isinstance(skill_text, str):
        raise ClaimsRefused("TEXT_TYPE")
    if not pdf_text.strip() or not skill_text.strip():
        raise ClaimsRefused("EMPTY_TEXT")
    if (len(member_names) != 3 or len(set(member_names)) != 3
            or any(not n.endswith(".md") for n in member_names)):
        raise ClaimsRefused("MARKDOWN_ONLY_PACKAGE_REQUIRED")
    p, s = pdf_text.casefold(), skill_text.casefold()
    missing = [
        key for key, (pdf_terms, skill_terms) in CLAIMS.items()
        if any(term not in p for term in pdf_terms)
        or any(term not in s for term in skill_terms)
    ]
    if missing:
        # Identifiers only; never return raw PDF or Skill text.
        raise ClaimsRefused("DOCUMENTARY_CLAIM_PARITY_FAILED:" + ",".join(missing))
    return {
        "schema": "flowpilot-g159-claims-rights-ledger-v1",
        "status": "EXACT_PAIR_DOCUMENTARY_CLAIMS_MATCH_OWNER_ATTESTATION_PENDING",
        "documentary_claims_cross_referenced": len(CLAIMS),
        "documentary_claim_ids": sorted(CLAIMS),
        "owner_attestations_required": list(ATTESTATIONS),
        "external_verification_pending": list(EXTERNAL_GATES),
        "originality_independently_verified": False,
        "platform_license_approved": False,
        "official_checker_executed": False,
        "registered_expert_verified": False,
        "nas_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
        "private_content_returned": False,
    }


def review_package(blob: bytes) -> dict:
    if type(blob) is not bytes or not 0 < len(blob) <= pair.MAX_BUNDLE:
        raise ClaimsRefused("PACKAGE_INPUT_INVALID")
    # Mandatory earlier verifier checks exact G157/G147 bytes, PDF question text,
    # member content hashes, G158 status=HOLD and no replacement files.
    previous = pair.verify_package(blob)
    if previous.get("release_gate") != "HOLD":
        raise ClaimsRefused("PAIR_RELEASE_STATUS_UNTRUSTED")
    try:
        import fitz
        with ZipFile(BytesIO(blob)) as outer:
            pdf = outer.read(pair.PDF_ENTRY)
            skill_zip = outer.read(pair.SKILL_ENTRY)
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            if doc.needs_pass or doc.page_count != 1:
                raise ClaimsRefused("PDF_UNREVIEWABLE")
            pdf_text = doc[0].get_text(sort=True)
        with ZipFile(BytesIO(skill_zip)) as inner:
            members = tuple(inner.namelist())
            skill_text = inner.read("flowpilot-3/SKILL.md").decode("utf-8")
        result = compare_text(pdf_text, skill_text, members)
    except (OSError, ValueError, UnicodeError, RuntimeError, KeyError) as exc:
        if isinstance(exc, ClaimsRefused):
            raise
        raise ClaimsRefused("DOCUMENTARY_REVIEW_UNAVAILABLE") from exc
    result["pdf_sha256"] = pair.PDF_PIN
    result["skill_zip_sha256"] = pair.SKILL_PIN
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G159 owner-only exact review package; no official clearance")
    parser.add_argument("--review-package", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = args.review_package
        if (path.is_symlink() or not path.is_file() or not
                0 < path.stat().st_size <= pair.MAX_BUNDLE):
            raise ClaimsRefused("LOCAL_PAIR_UNAVAILABLE")
        result = review_package(path.read_bytes())
        code = 0
    except (ClaimsRefused, pair.PairRefused, OSError, ValueError, RuntimeError):
        result = {
            "schema": "flowpilot-g159-claims-rights-ledger-v1",
            "status": "OWNER_FACT_RIGHTS_DOCUMENTARY_REVIEW_REFUSED",
            "official_checker_executed": False,
            "release_gate": "HOLD",
            "private_content_returned": False,
        }
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
