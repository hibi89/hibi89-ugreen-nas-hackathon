"""G263: read-only, exact-original G226 rights/provenance boundary audit.

Confirms only source byte identity and directly checkable Markdown/disclosure facts.
Does NOT determine copyright originality, issue a license, invoke Creator/NAS,
or grant submission approval. Never embeds or publishes the owner-private ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

SCHEMA = "flowpilot-g263-original-markdown-rights-boundary-v1"
SKILL_SHA = "fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803"
KIT_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
ENTRY_SHA = {
    "flowpilot-3/SKILL.md": "2f8f3c6cefcd5a02eb9c2de19a7bdb6009bf5ffa07dc1c0a7e7e369e14deb0fe",
    "flowpilot-3/references/failure-and-disclosure.md": "27a20ae313e4cf6a37af7d5b6d016acbde2cf1b3581034a8e7372ef2a96892ef",
    "flowpilot-3/references/modes-and-evidence.md": "41fbd0bb65ac26bf9a3feef1951a1104886881cf9ea6d62658032ff2758081c5",
    "flowpilot-3/references/workflow-council-and-repair.md": "33aeff0f5d8531fd23861b34d4798efe988078bd2b2933ab78ce348ea03e6c19",
}
REQUIRED_DISCLOSURE = (
    "Principal new work for the contest:",
    "This Skill was authored in ChatGPT with OpenAI GPT-6",
    "official Uliya Skill Kit 0.7.3",
    "No vendor script, binary, SDK source, runtime component, model weight or dependency is bundled",
    "Data processing and retention of any future selected external provider must be separately confirmed",
)
OFFICIAL_SOURCE_PAGES = (
    "https://ugreenhackathon.devpost.com/rules",
    "https://ai.ugreen.com/pages/hackathon-starter-kit",
    "https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-user-agreement",
    "https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec",
    "https://ai.ugreen.com/pages/uliya-user-agreement",
    "https://openai.com/ko-KR/policies/terms-of-use/",
)


class RightsBoundaryRefused(ValueError):
    """Input could not support narrow reproducible provenance conclusion."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _markdown_zip(data: bytes, *, exact_manifest: bool) -> dict[str, bytes]:
    if type(data) is not bytes or not 0 < len(data) < 120000:
        raise RightsBoundaryRefused("UNBOUNDED_OR_INVALID_SKILL_ARCHIVE")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members = z.infolist()
            if len(members) != 4 or sum(x.file_size for x in members) > 85000:
                raise RightsBoundaryRefused("UNEXPECTED_SKILL_ARCHIVE_CONTENTS")
            names = [x.filename for x in members]
            if len(names) != len(set(names)) or set(names) != set(ENTRY_SHA):
                raise RightsBoundaryRefused("UNEXPECTED_SKILL_ENTRY_NAMES")
            if any(x.is_dir() or x.flag_bits & 1 or x.file_size > 50000 or
                   x.compress_size > 60000 or x.filename.startswith("/") or
                   ".." in x.filename.split("/") or
                   (x.external_attr >> 16) & 0o170000 == 0o120000
                   for x in members):
                raise RightsBoundaryRefused("UNSAFE_SKILL_ARCHIVE_ENTRY")
            docs = {p: z.read(p) for p in names}
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError, UnicodeError) as exc:
        raise RightsBoundaryRefused("BAD_SKILL_ZIP_OR_CRC") from exc
    for name, body in docs.items():
        if b"\x00" in body or not body or len(body) > 50000:
            raise RightsBoundaryRefused("NON_MARKDOWN_OR_UNBOUNDED_ENTRY")
        try:
            text = body.decode("utf-8")
        except UnicodeError as exc:
            raise RightsBoundaryRefused("NON_UTF8_MARKDOWN") from exc
        if re.search(r"(?im)^\s*(?:```|~~~)\s*(?:python|bash|sh|powershell|javascript|node)\b", text):
            raise RightsBoundaryRefused("EXECUTABLE_CODE_BLOCK_DISCLOSURE_RISK")
        if exact_manifest and _sha(body) != ENTRY_SHA[name]:
            raise RightsBoundaryRefused("CHANGED_G226_MARKDOWN_BYTES")
    return docs


def audit_original(skill: bytes, kit: bytes) -> dict:
    """Read only authentic byte-pinned inputs and return no owner content."""
    if type(skill) is not bytes or _sha(skill) != SKILL_SHA:
        raise RightsBoundaryRefused("CURRENT_G226_ORIGINAL_NOT_PRESENT")
    if type(kit) is not bytes or _sha(kit) != KIT_SHA:
        raise RightsBoundaryRefused("ORIGINAL_FIRST_PARTY_KIT_NOT_PRESENT")
    docs = _markdown_zip(skill, exact_manifest=True)
    disclosure = docs["flowpilot-3/references/failure-and-disclosure.md"].decode("utf-8")
    if not all(phrase in disclosure for phrase in REQUIRED_DISCLOSURE):
        raise RightsBoundaryRefused("ORIGINAL_RIGHTS_DISCLOSURE_INCOMPLETE")
    # Inspect the authentic Kit's archived entries without copying it to output.
    try:
        with zipfile.ZipFile(io.BytesIO(kit)) as z:
            kit_names = z.namelist()
            if (len(kit_names) > 40 or len(kit_names) != len(set(kit_names)) or
                    "uliya-skill-kit/SKILL.md" not in kit_names or
                    "uliya-skill-kit/scripts/check-skill.mjs" not in kit_names):
                raise RightsBoundaryRefused("UNEXPECTED_VENDOR_KIT_ENTRIES")
            vendor_markdown = [z.read(n) for n in kit_names
                               if n.endswith(".md") and z.getinfo(n).file_size <= 25000]
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise RightsBoundaryRefused("UNREADABLE_OFFICIAL_KIT") from exc
    if any(body == vendor for body in docs.values() for vendor in vendor_markdown):
        raise RightsBoundaryRefused("VENDOR_DOCUMENT_WHOLE_FILE_REUSED")
    return {
        "schema": SCHEMA,
        "status": "EXACT_ORIGINAL_MARKDOWN_AND_DISCLOSURE_BOUND_NOT_LICENSE_CLEARANCE",
        "original_g226_sha256": SKILL_SHA,
        "official_kit_sha256": KIT_SHA,
        "g226_markdown_files_checked": len(docs),
        "g226_byte_identical_entries": True,
        "vendor_files_bundled": False,
        "vendor_whole_markdown_reused": False,
        "entrant_work_and_ai_assistance_disclosed_in_skill": True,
        "external_rights_references_for_human_review": list(OFFICIAL_SOURCE_PAGES),
        "references_automatically_verified_live": False,
        "openai_output_ownership_is_subject_to_applicable_terms_and_law": True,
        "third_party_ip_non_infringement_proven": False,
        "vendor_kit_redistribution_license_proven": False,
        "skillhub_publisher_rights_attestation_verified": False,
        "skillhub_compatible_license_choice_verified": False,
        "platform_static_checker_is_license_clearance": False,
        "supported_creator_invocation_verified": False,
        "entrant_rights_attestation_received": False,
        "owner_submission_approved": False,
        "nas_verified": False,
        "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G263 no-network owner-private original provenance audit")
    parser.add_argument("--candidate-skill", required=True, type=Path)
    parser.add_argument("--official-kit", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if any(not p.is_file() or p.is_symlink() for p in
               (args.candidate_skill, args.official_kit)):
            raise RightsBoundaryRefused("UNSAFE_SOURCE_FILE")
        result = audit_original(args.candidate_skill.read_bytes(), args.official_kit.read_bytes())
    except (OSError, ValueError, TypeError, zipfile.BadZipFile):
        print(json.dumps({"status": "G263_PRIVATE_ORIGINAL_PROVENANCE_REFUSED",
                          "nas_verified": False, "release_gate": "HOLD"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
