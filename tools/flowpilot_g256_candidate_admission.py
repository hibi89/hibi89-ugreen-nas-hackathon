"""G256: read-only exact G226 private round-1 pair preflight.

Authenticates previously acquired G226 source/audit/proposal against SHA pins.
NEVER executes the official Uliya checker, a model, a CLI, NAS, or a vendor script.
It does not replace first-party Creator provenance or the entrant's release.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

EXPECTED = {
    "skill": "fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803",
    "pdf": "5f8b4ccde2c88c288d4f12bc3a63e814ced1296e7c255102132baea0d358047e",
    "kit": "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3",
    "audit": "9c062cbe15bc553af6ed13a9b3442f9635037c3d0c484b47fd008866b31d2f1f",
}
MEMBERS = frozenset({
    "flowpilot-3/SKILL.md",
    "flowpilot-3/references/failure-and-disclosure.md",
    "flowpilot-3/references/modes-and-evidence.md",
    "flowpilot-3/references/workflow-council-and-repair.md",
})
MODES = ("CHECK_DELIVERY", "REVIEW_VERSIONS", "REVIEW_DOCUMENT",
         "DESIGN_WORKFLOW", "PLAN_ONLY")


class AdmissionRefused(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json(data: bytes) -> dict:
    def unique(items):
        if len(items) != len({k for k, _ in items}):
            raise AdmissionRefused("DUPLICATE_JSON_KEY")
        return dict(items)
    if len(data) > 32768:
        raise AdmissionRefused("AUDIT_TOO_LARGE")
    try:
        result = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    except (ValueError, UnicodeError) as e:
        raise AdmissionRefused("AUDIT_NOT_VALID_JSON") from e
    if type(result) is not dict:
        raise AdmissionRefused("AUDIT_NOT_OBJECT")
    return result


def verify_bytes(skill: bytes, pdf: bytes, kit: bytes, audit: bytes,
                 expected: dict | None = None) -> dict:
    """Validate exact G226 candidate; tests can pass code-owned fixture hashes."""
    pins = EXPECTED if expected is None else expected
    blobs = {"skill": skill, "pdf": pdf, "kit": kit, "audit": audit}
    for name, raw in blobs.items():
        if type(raw) is not bytes or not raw or len(raw) > (1_000_000 if name != "kit" else 500_000):
            raise AdmissionRefused("FILE_MISSING_OR_TOO_LARGE")
        if sha(raw) != pins[name]:
            raise AdmissionRefused("EXACT_FILE_SHA_MISMATCH")
    if not pdf.startswith(b"%PDF-"):
        raise AdmissionRefused("PDF_MAGIC_INVALID")
    try:
        with zipfile.ZipFile(io.BytesIO(kit)) as vendor:
            if vendor.testzip() is not None or "uliya-skill-kit/scripts/check-skill.mjs" not in vendor.namelist():
                raise AdmissionRefused("KIT_NOT_PINNED_STRUCTURE")
        with zipfile.ZipFile(io.BytesIO(skill)) as bundle:
            entries = bundle.infolist()
            names = [entry.filename for entry in entries]
            if (len(entries) != 4 or set(names) != MEMBERS or
                    len(set(names)) != 4 or bundle.testzip() is not None or
                    sum(e.file_size for e in entries) > 10_000_000 or
                    any(e.file_size > 1_000_000 or e.is_dir() or
                        stat.S_ISLNK(e.external_attr >> 16) for e in entries)):
                raise AdmissionRefused("ZIP_MEMBERS_CRC_OR_SAFETY_INVALID")
            skill_text = bundle.read("flowpilot-3/SKILL.md").decode("utf-8")
            refs = bundle.read("flowpilot-3/references/workflow-council-and-repair.md").decode("utf-8")
            if (not skill_text.startswith("---\nname: flowpilot-3\ndescription:") or
                    any(mode not in skill_text for mode in MODES) or
                    any(path.removeprefix("flowpilot-3/") not in skill_text
                        for path in MEMBERS if path != "flowpilot-3/SKILL.md") or
                    "DESIGN_ONLY / NOT_EXECUTED" not in skill_text or
                    any(role not in refs for role in ("Architect", "Security", "Builder", "QA")) or
                    "Maximum one bounded correction" not in refs):
                raise AdmissionRefused("G226_DESIGN_CONTRACT_INVALID")
    except (zipfile.BadZipFile, KeyError, UnicodeError) as e:
        raise AdmissionRefused("BAD_ZIP_OR_MARKDOWN") from e
    history = _strict_json(audit)
    if (history.get("status") != "ALTERNATIVE_VERIFIED_LOCALLY_NOT_ADOPTED_NOT_SUBMITTED" or
            history.get("skill_zip", {}).get("sha256") != pins["skill"] or
            history.get("pdf", {}).get("sha256") != pins["pdf"] or
            history.get("independent_checks", {}).get("passed") != 24 or
            history.get("independent_checks", {}).get("failed") != 0 or
            history.get("first_party_uliya_checker", {}).get("status") != "static-pass" or
            history.get("first_party_uliya_checker", {}).get("exit_code") != 0 or
            history.get("creator_provenance") != "NOT_VERIFIED" or
            history.get("runtime_registered_agents") != "NOT_RUN" or
            history.get("owner_final_release_approved") is not False or
            history.get("official_submission") != "NOT_SUBMITTED" or
            history.get("release_gate") != "HOLD"):
        raise AdmissionRefused("HISTORICAL_AUDIT_UNBOUND_OR_OVERCLAIMS")
    return {
        "schema": "flowpilot-g256-private-exact-source-admission-v1",
        "status": "EXACT_G226_SOURCE_PDF_AND_HISTORY_BOUND_LOCAL_ONLY",
        "candidate_skill_zip_sha256": pins["skill"],
        "candidate_pdf_sha256": pins["pdf"],
        "kit_sha256": pins["kit"],
        "recorded_official_checker_static_pass": True,
        "checker_executed_by_this_verifier": False,
        "official_creator_provenance_verified": False,
        "nas_verified": False, "participant_release_approved": False,
        "devpost_submitted": False, "release_gate": "HOLD",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Owner-private exact G226 proof only; no provider execution")
    for name in ("skill", "pdf", "kit", "audit"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        paths = {name: getattr(args, name) for name in ("skill", "pdf", "kit", "audit")}
        for path in paths.values():
            if not path.is_file() or path.is_symlink():
                raise AdmissionRefused("NOT_REGULAR_PRIVATE_INPUT")
        result = verify_bytes(**{name: path.read_bytes() for name, path in paths.items()})
    except (AdmissionRefused, OSError) as exc:
        print(json.dumps({"status":"G256_LOCAL_CANDIDATE_ADMISSION_REFUSED",
                          "reason":type(exc).__name__,
                          "release_gate":"HOLD"},sort_keys=True))
        return 2
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
