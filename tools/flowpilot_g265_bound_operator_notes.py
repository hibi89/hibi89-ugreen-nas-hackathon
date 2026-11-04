"""G265: attach untrusted operator notes to one exact G257 offline plan.

This is NOT a native Uliya parser, signed report, device readback, or approval.
No NAS/CLI calls, owner path reads, external calls, or file writes. A digest
prevents accidental replay across plans; an attacker can forge unsigned JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "flowpilot-g265-source-bound-operator-notes-v1"
PLAN_SCHEMA = "flowpilot-g257-nas-trial-readiness-v1"
SCOPE_SCHEMA = "flowpilot-g261-redacted-owner-scope-receipt-v1"
G226_SHA = "fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803"
KIT_SHA = "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3"
STAGE_IDS = (
    "REGISTRY_AND_RIGHTS", "REQUIRED_FILES", "VERSION_CONFLICT",
    "DOCUMENT_SEPARATE_CONSENT", "DENIED_AND_TRUNCATED",
    "INDEPENDENT_READBACK", "CLEANUP_AND_BUFFER",
)
OUTCOMES = ("NOT_RUN", "BLOCKED", "OPERATOR_REPORTED", "TIMED_OUT")
REASONS = (
    "NONE", "PERMISSION_DENIED", "UNKNOWN_SIGNATURE", "UNKNOWN_RESULT_SCHEMA",
    "INCOMPLETE_LISTING", "CONFLICT", "CONSENT_DECLINED", "TIMEOUT", "UNKNOWN_PROVENANCE",
)
HASH = re.compile(r"[0-9a-f]{64}\Z")


class OperatorNotesRefused(ValueError):
    pass


def _digest(value: object) -> str:
    # A canonical digest is only equality evidence, NOT authentication.
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def plan_identity(plan: object) -> dict:
    """Require exact current source/Kit identity and current owner scope.

    The input is still user/operator-declared. It cannot prove that the
    actual private bytes or effective NAS permissions were checked here.
    """
    if type(plan) is not dict or plan.get("schema") != PLAN_SCHEMA or \
       plan.get("status") != "CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY" or \
       plan.get("source_candidate_sha256") != G226_SHA or \
       plan.get("public_kit_sha256") != KIT_SHA or \
       plan.get("current_skill_rechecked") is not True or \
       plan.get("nas_verified") is not False or \
       plan.get("release_gate") != "HOLD" or \
       plan.get("starts_trial_or_timer") is not False or \
       plan.get("performs_native_cli_calls") is not False or \
       plan.get("may_activate_nas_trial") is not False or \
       plan.get("exact_registered_expert_signatures_verified") is not False or \
       plan.get("effective_nas_permissions_verified") is not False or \
       plan.get("native_return_envelope_verified") is not False or \
       plan.get("owner_explicit_live_authorization_received") is not False or \
       plan.get("official_creator_provenance_verified") is not False or \
       plan.get("devpost_submitted") is not False:
        raise OperatorNotesRefused("UNTRUSTED_OR_NONCURRENT_TRIAL_PLAN")
    instructions = plan.get("current_skill_instruction_sha256")
    if type(instructions) is not list or len(instructions) != 2 or \
       any(type(x) is not str or not HASH.fullmatch(x) for x in instructions):
        raise OperatorNotesRefused("INCOMPLETE_GUARDED_SOURCE_INSTRUCTIONS")
    stages = plan.get("scenarios")
    if type(stages) is not list or len(stages) != len(STAGE_IDS) or \
       any(type(s) is not dict or s.get("id") != stage_id or
           s.get("status") != "NOT_RUN" or
           s.get("effective_permissions_verified") is not False or
           s.get("required_independent_live_evidence") is not True
           for s, stage_id in zip(stages, STAGE_IDS)):
        raise OperatorNotesRefused("UNTRUSTED_SCENARIO_COVERAGE")
    scope = plan.get("operator_scope")
    if type(scope) is not dict or set(scope) != {
        "schema", "status", "request_sha256", "required_file_count",
        "owner_paths_exposed", "consent_independently_verified",
        "actual_native_instruction_created",
    } or scope["schema"] != SCOPE_SCHEMA or \
       scope["status"] != "LOCAL_SCOPE_REQUEST_BOUND_AWAITING_REAL_EXPERT" or \
       type(scope["request_sha256"]) is not str or \
       not HASH.fullmatch(scope["request_sha256"]) or \
       type(scope["required_file_count"]) is not int or \
       not 1 <= scope["required_file_count"] <= 40 or \
       scope["owner_paths_exposed"] is not False or \
       scope["consent_independently_verified"] is not False or \
       scope["actual_native_instruction_created"] is not False:
        raise OperatorNotesRefused("OWNER_SCOPE_OR_CONSENT_UNBOUND")
    return {"plan_sha256": _digest(plan),
            "source_candidate_sha256": G226_SHA,
            "public_kit_sha256": KIT_SHA,
            "owner_scope_sha256": scope["request_sha256"]}


def bind_operator_notes(plan: object, note_packet: object) -> dict:
    """Normalize only safe enumerations and SHA-256 digests; never raw paths.

    Does not establish ownership of the reported traces, their existence,
    consent validity, vendor provenance, authenticity, or NAS success.
    """
    identity = plan_identity(plan)
    if type(note_packet) is not dict or set(note_packet) != {
        "schema", "plan_sha256", "scope_sha256", "notes",
    } or note_packet["schema"] != SCHEMA or \
       note_packet["plan_sha256"] != identity["plan_sha256"] or \
       note_packet["scope_sha256"] != identity["owner_scope_sha256"]:
        raise OperatorNotesRefused("STALE_OR_MISMATCHED_OPERATOR_NOTES")
    notes = note_packet["notes"]
    if type(notes) is not list or len(notes) > len(STAGE_IDS):
        raise OperatorNotesRefused("UNBOUNDED_OPERATOR_NOTES")
    seen = set()
    counts = {status: 0 for status in OUTCOMES}
    for note in notes:
        if type(note) is not dict or set(note) != {
            "case_id", "outcome", "reason_code", "trace_sha256",
        }:
            raise OperatorNotesRefused("RAW_OR_UNKNOWN_NOTE_FIELDS")
        case, status, reason, trace = (note["case_id"], note["outcome"],
                                       note["reason_code"], note["trace_sha256"])
        if (type(case) is not str or case not in STAGE_IDS or case in seen or
            type(status) is not str or status not in OUTCOMES or
            type(reason) is not str or reason not in REASONS or
            (trace is not None and (type(trace) is not str or
                                    not HASH.fullmatch(trace)))):
            raise OperatorNotesRefused("INVALID_OR_DUPLICATE_OPERATOR_NOTE")
        seen.add(case)
        counts[status] += 1
    return {"schema": "flowpilot-g265-redacted-operator-report-v1",
            "status": "SOURCE_BOUND_OPERATOR_NOTES_NOT_DEVICE_EVIDENCE",
            **identity, "note_count": len(notes), "outcome_counts": counts,
            "operator_notes_sha256": _digest(note_packet),
            "operator_claims_are_signed_vendor_evidence": False,
            "registered_expert_invocation_verified": False,
            "nas_verified": False, "release_gate": "HOLD"}


def _json_file(path: Path, maximum: int) -> object:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise OperatorNotesRefused("MISSING_OR_UNSAFE_LOCAL_JSON")
    def unique(pairs):
        if len(pairs) != len({name for name, _ in pairs}):
            raise OperatorNotesRefused("DUPLICATE_JSON_FIELD")
        return dict(pairs)
    return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          OperatorNotesRefused("INVALID_JSON_CONSTANT")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G265 no-network operator notes source binder")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--notes", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = bind_operator_notes(_json_file(args.plan, 60000),
                                     _json_file(args.notes, 16384))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, OverflowError):
        print(json.dumps({"status": "G265_OPERATOR_NOTES_REFUSED",
                          "nas_verified": False, "release_gate": "HOLD"},
                         sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
