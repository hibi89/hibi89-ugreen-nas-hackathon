"""G28 editorial PREVIEW, derived from a pinned official-Creator candidate.

Never reuse the official static checker pass for a changed SHA. Does not run
vendor binaries, use the NAS, submit to Devpost or alter the original input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from check_round1_proposal import errors, render_markdown, word_count
from render_round1_proposal_pdf import render
from round1_candidate_bundle import validate_pdf
from round1_official_creator_preview import creator_proposal, zip_only_skill

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/submission/checker_inputs/G22_20261024/projectready-nas/SKILL.md"
RECEIPT = ROOT / "docs/submission/evidence/G27_PARTICIPANT_OFFICIAL_CHECKER_RESULT_20261025.json"
G22_SHA = "770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169"
BEGIN = "The following one-line delegates are fully populated **synthetic examples only**."
END = "If the first expert returns no results, say that no results were returned and stop;"
STALE = (
    "An original official-Creator source and an edited candidate were statically checked "
    "in participant Codex reports; this disclosure-augmented preview has **not** been "
    "rerun through the official checker."
)
CORRECTED = (
    "The previous disclosure-augmented G22 Skill (SHA-256 " + G22_SHA +
    ") passed the official static checker in a participant-reported Codex run with "
    "zero errors, warnings and information messages. This additional editorial "
    "revision has **not** been officially rechecked and must not inherit that pass."
)
PROCEDURE = """## Real-input delegation procedure (no sample commands)

For each real request, build a complete self-contained expert instruction using
only owner-supplied, currently validated and authorized data. No expert is assumed
to see the parent conversation.

1. The file-agent instruction must inject the exact approved folder and each
   required relative path, every approved version-candidate pattern and the
   requirement it represents. Restrict work to read-only ls/find/stat within
   that folder; prohibit symlinks, content reads, mutations and other folders.
   Require attributable file references, scan completeness/truncation, errors,
   permission status and stop conditions. Incomplete or denied scans yield
   NOT_CHECKED, never MISSING; absent approval or required input yields
   waiting_user rather than a delegation.
2. The document-agent instruction must inject only the exact in-scope references
   actually returned by file-agent and separately approved for document reading,
   plus the owner's actual question verbatim. Bind an approved file to file and
   the actual question to query only when supported by the catalog action.
   Restrict to declared metadata/qa/extract/reconcile read operations; prohibit
   independent discovery, mutations and guesses about authoritative versions.
   Require attributable evidence for each referenced document or version
   candidate, coverage, permission state and errors. Missing reference,
   separate approval, actual question or supported argument mapping yields
   waiting_user, not a broadened fallback.

The catalog alone does not establish the actual delegation CLI syntax, live
agent registration, effective permissions or processing location. If any are
required but unverified, stop and report NOT_CHECKED.

"""
Q8 = (
    "The official UGOS Skill Creation Tool generated the initial Skill. A "
    "disclosure-augmented revision passed the official static checker in Codex "
    "(zero diagnostics and exact source SHA verified). This further editorial "
    "revision needs its own official recheck. Registered Agent calls, effective "
    "permissions, data-processing location, and live NAS execution are unverified."
)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def verified_input() -> bytes:
    if SOURCE.is_symlink() or RECEIPT.is_symlink() or not SOURCE.is_file() or not RECEIPT.is_file():
        raise ValueError("Pinned Skill or report missing or a symlink")
    raw = SOURCE.read_bytes()
    if digest(raw) != G22_SHA:
        raise ValueError("G22 source SHA mismatch")
    j = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if (j.get("checkFormatVersion") != "2.0.0" or
        j.get("status") != "static-pass" or
        j.get("target", {}).get("skillName") != "projectready-nas" or
        j.get("catalog", {}).get("checkedVersion") != "2.0.0" or
        j.get("files") != [{"path": "SKILL.md", "sha256": G22_SHA}] or
        j.get("summary") != {"errors": 0, "warnings": 0, "info": 0} or
        j.get("diagnostics") != []):
        raise ValueError("G27 official checker receipt not matching pinned G22")
    return raw

def editorial_bytes(raw: bytes) -> bytes:
    if digest(raw) != G22_SHA:
        raise ValueError("Wrong G22 base")
    text = raw.decode("utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1 or text.count(STALE) != 1:
        raise ValueError("Review source block boundaries changed")
    start, stop = text.index(BEGIN), text.index(END)
    if stop <= start:
        raise ValueError("Bad example span")
    old_block = text[start:stop]
    if old_block.count("SYNTHETIC EXAMPLE ONLY") != 2 or old_block.count("delegate --target") != 2:
        raise ValueError("Unexpected example count, manual review required")
    edited = (text[:start] + PROCEDURE + text[stop:]).replace(STALE, CORRECTED)
    if ("SYNTHETIC EXAMPLE ONLY" in edited or "delegate --target" in edited or
        STALE in edited or not re.match(r"\A---\s*\nname: projectready-nas\n", edited)):
        raise ValueError("Unsafe editorial transformation")
    result = edited.encode("utf-8")
    if len(result) > 1_000_000 or digest(result) == G22_SHA:
        raise ValueError("New candidate not distinct or too big")
    return result

def editorial_proposal() -> dict:
    p = creator_proposal()
    p["questions"][7]["answer"] = Q8
    p["proof_status"]["creator_static_checker"] = "G22_REPORTED_STATIC_PASS_NEW_SHA_NOT_RUN"
    p["substantive_words"] = sum(word_count(q["answer"]) for q in p["questions"])
    issues = errors(p, render_markdown(p))
    if issues:
        raise ValueError("Proposal errors: " + "; ".join(issues))
    return p

def build(output: Path) -> dict:
    base = verified_input()
    skill = editorial_bytes(base)
    proposal = editorial_proposal()
    dest = output.resolve()
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError("Output must be outside repository")
    dest.mkdir(parents=True, exist_ok=True)
    archive = zip_only_skill(skill)
    zp = dest / "ProjectReady_Editorial_Skill_NOT_SUBMITTED.zip"
    pp = dest / "ProjectReady_Editorial_Proposal_NOT_SUBMITTED.pdf"
    zp.write_bytes(archive)
    render(pp, proposal=proposal)
    pdf = validate_pdf(pp, proposal["questions"], proposal["disclosures"])
    (dest / "ProjectReady_Editorial_Proposal_NOT_SUBMITTED.md").write_text(
        render_markdown(proposal), encoding="utf-8"
    )
    manifest = {
        "state": "G28_EDITORIAL_PREVIEW_ONLY",
        "official_creator_source": "review/ugreen-official-creator",
        "g22_checked_sha256": G22_SHA,
        "g22_official_checker": "PARTICIPANT_REPORTED_STATIC_PASS_EXACT_SHA_0_0_0",
        "candidate_skill_sha256": digest(skill),
        "candidate_skill_bytes": len(skill),
        "candidate_official_checker": "NOT_RUN_NEW_SHA",
        "removed_synthetic_examples": 2,
        "stale_validation_statement_corrected": True,
        "zip_sha256": digest(archive),
        "zip_bytes": len(archive),
        "zip_members": ["projectready-nas/SKILL.md"],
        "pdf": pdf,
        "proposal_answer_words": proposal["substantive_words"],
        "permissions": "UNVERIFIED",
        "real_nas": "NOT_RUN",
        "ip_license": "PENDING",
        "human_approval": "PENDING",
        "devpost": "NOT_SUBMITTED",
    }
    (dest / "ProjectReady_Editorial_Manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest

def main() -> int:
    arg = argparse.ArgumentParser()
    arg.add_argument("--output-dir", required=True, type=Path)
    a = arg.parse_args()
    try:
        m = build(a.output_dir)
        print("G28 EDITORIAL PREVIEW PASS", m["candidate_skill_sha256"],
              m["proposal_answer_words"], "words; OFFICIAL CHECKER NOT_RUN; NOT_SUBMITTED")
        return 0
    except (ValueError, OSError, UnicodeError, RuntimeError) as e:
        print("G28 EDITORIAL PREVIEW FAIL", str(e)[:400])
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
