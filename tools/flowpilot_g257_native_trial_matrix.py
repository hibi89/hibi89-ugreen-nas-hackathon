"""G257: executable LOCAL readiness gate for a future short NAS trial.

Checks the pinned public Uliya 0.7.3 catalog and exact G256 private
candidate-admission *receipt*. Emits a fixed 180-minute test matrix and
strict, redacted trial evidence slots. Never invokes a vendor CLI/Expert/NAS,
starts a trial, writes owner files, or claims that reported results are live.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from flowpilot_g260_official_catalog import (
    matrix, EXPECTED_SHA256 as KIT_SHA, OfficialCatalogRefused as UnsafePackage,
)
from flowpilot_g258_skill_dispatch_binding import verify_current_skill, SkillBoundaryRefused
from flowpilot_g261_owner_scope import bind_owner_scope, ScopeRefused

SCHEMA = "flowpilot-g257-nas-trial-readiness-v1"
G256_SCHEMA = "flowpilot-g256-private-exact-source-admission-v1"
G256_STATUS = "EXACT_G226_SOURCE_PDF_AND_HISTORY_BOUND_LOCAL_ONLY"
G226_SHA = "fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803"
G226_PDF = "5f8b4ccde2c88c288d4f12bc3a63e814ced1296e7c255102132baea0d358047e"
ACTIONS = {
    "ug-filesystem": {"ls", "find", "stat"},
    "ug-document": {"metadata", "qa"},
}
AGENTS = {"ug-filesystem": "file-agent", "ug-document": "document-agent"}
# The budget is a proposed 3h owner test sequence, NOT proof that a 3h
# official trial account exists. The official finalist window differs.
STAGES = (
    ("REGISTRY_AND_RIGHTS", 20, (), "Exact registered Expert signature and effective scoped read permission"),
    ("REQUIRED_FILES", 35, ("ug-filesystem find", "ug-filesystem stat"),
     "A complete, attributable scoped listing; missing only with complete enumeration"),
    ("VERSION_CONFLICT", 30, ("ug-filesystem find", "ug-filesystem stat"),
     "Two competing real candidates -> VERSION_REVIEW; no automatic winner"),
    ("DOCUMENT_SEPARATE_CONSENT", 30, ("ug-document metadata", "ug-document qa"),
     "Explicit new exact-document content consent before any QA"),
    ("DENIED_AND_TRUNCATED", 30, ("ug-filesystem ls",),
     "Denied/out-of-scope/truncated results -> NOT_CHECKED; no fallback read"),
    ("INDEPENDENT_READBACK", 25, ("ug-filesystem stat",),
     "Real second scoped read with trace/identity binding; never trust self-claimed success"),
    ("CLEANUP_AND_BUFFER", 10, (), "Originals unchanged; only synthetic files and credential-free evidence"),
)
OUTCOMES = frozenset(("NOT_RUN", "BLOCKED", "OPERATOR_REPORTED", "TIMED_OUT"))
NOTES = frozenset(("NONE", "PERMISSION_DENIED", "UNKNOWN_SIGNATURE",
                   "UNKNOWN_RESULT_SCHEMA", "INCOMPLETE_LISTING",
                   "CONFLICT", "CONSENT_DECLINED", "TIMEOUT", "UNKNOWN_PROVENANCE"))
SHA = re.compile(r"[0-9a-f]{64}\Z")


class TrialReadinessRefused(ValueError):
    pass


def _receipt_ok(proof: object, kit_sha: str) -> None:
    required = {
        "schema": G256_SCHEMA,
        "status": G256_STATUS,
        "candidate_skill_zip_sha256": G226_SHA,
        "candidate_pdf_sha256": G226_PDF,
        "kit_sha256": KIT_SHA,
        "recorded_official_checker_static_pass": True,
        "checker_executed_by_this_verifier": False,
        "official_creator_provenance_verified": False,
        "nas_verified": False,
        "participant_release_approved": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }
    if type(proof) is not dict or proof != required or kit_sha != KIT_SHA:
        raise TrialReadinessRefused("G256_PRIVATE_SOURCE_ATTESTATION_OR_KIT_MISSING")


def _catalog_rows(raw: bytes, kit_sha: str, *, override_for_tests: bool = False):
    # No unsigned user-provided 'official' digest overrides are accepted
    # by the normal CLI. Optional fixture path marks synthetic-only tests.
    if type(raw) is not bytes or not 0 < len(raw) <= 500000:
        raise TrialReadinessRefused("INVALID_KIT_BYTES")
    if hashlib.sha256(raw).hexdigest() != kit_sha:
        raise TrialReadinessRefused("OFFICIAL_KIT_HASH_MISMATCH")
    if kit_sha != KIT_SHA and not override_for_tests:
        raise TrialReadinessRefused("OFFICIAL_KIT_NOT_PINNED")
    result = matrix(raw, kit_sha, synthetic_only=override_for_tests)
    rows = result.get("actions")
    if type(rows) is not list or result.get("action_count") != len(rows):
        raise TrialReadinessRefused("INVALID_OFFICIAL_CAPABILITY_MATRIX")
    indexed = {}
    for row in rows:
        if type(row) is not dict:
            raise TrialReadinessRefused("INVALID_CAPABILITY_ROW")
        key = (row.get("cli"), row.get("action"))
        if key in indexed:
            raise TrialReadinessRefused("DUPLICATE_OFFICIAL_ACTION")
        indexed[key] = row
    for cli, names in ACTIONS.items():
        for action in names:
            row = indexed.get((cli, action))
            if not row or row.get("agent_label") != (
                    AGENTS[cli] if kit_sha == KIT_SHA else "fake-agent"):
                raise TrialReadinessRefused("EXPERT_CATALOG_AGENT_MAPPING_MISSING")
            if row.get("effect") != {"kind": "scalar", "value": "read"}:
                raise TrialReadinessRefused("UNSAFE_ACTION_EFFECT")
            if row.get("permissions", {}).get("knowledge_status") != "unknown":
                raise TrialReadinessRefused("CATALOG_RIGHTS_OVERSTATED")
            params = row.get("parameters")
            if (type(params) is not list or len(params) > 20 or
                    len({p.get("name") for p in params if type(p) is dict}) != len(params)):
                raise TrialReadinessRefused("INVALID_PUBLIC_PARAMETERS")
    return sorted(f"{cli} {action}" for cli,names in ACTIONS.items() for action in names)


def prepare_trial(kit: bytes, proof: dict, *,
                  test_sha: str | None = None,
                  candidate_skill: bytes | None = None,
                  test_candidate_sha: str | None = None) -> dict:
    digest = hashlib.sha256(kit).hexdigest() if type(kit) is bytes else ""
    # A synthetic fixture may exercise the public catalog contract in unit
    # tests, but NEVER use G256 owner-proof or say official registration passed.
    synthetic = test_sha is not None
    if synthetic:
        if digest != test_sha or type(proof) is not dict:
            raise TrialReadinessRefused("SYNTHETIC_FIXTURE_INVALID")
    else:
        _receipt_ok(proof, digest)
    actions = _catalog_rows(kit, test_sha if synthetic else KIT_SHA,
                            override_for_tests=synthetic)
    bound = None
    if candidate_skill is not None:
        if (synthetic and test_candidate_sha is None) or (
                not synthetic and test_candidate_sha is not None):
            raise TrialReadinessRefused("G258_INVALID_CANDIDATE_HASH_OVERRIDE")
        try:
            bound = verify_current_skill(
                candidate_skill, kit, skill_pin=(
                    test_candidate_sha if synthetic else G226_SHA),
                kit_pin=(test_sha if synthetic else KIT_SHA),
                synthetic_only=synthetic)
        except SkillBoundaryRefused as exc:
            raise TrialReadinessRefused("CURRENT_G226_SKILL_RECHECK_REFUSED") from exc
    stages = []
    for name, minutes, dependencies, condition in STAGES:
        if not set(dependencies).issubset(actions):
            raise TrialReadinessRefused("TEST_SCENARIO_WITHOUT_CATALOG_ACTION")
        stages.append({
            "id": name, "maximum_minutes": minutes,
            "catalog_action_labels_not_executable": list(dependencies),
            "success_condition_for_authorized_operator": condition,
            "status": "NOT_RUN",
            "required_independent_live_evidence": True,
            "effective_permissions_verified": False,
        })
    assert sum(s["maximum_minutes"] for s in stages) == 180
    return {
        "schema": SCHEMA,
        "status": "SYNTHETIC_TRIAL_PLAN_ONLY" if synthetic
                  else ("CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY" if bound
                        else "AWAITING_CURRENT_G226_SKILL_BYTES"),
        "budget_minutes": 180,
        "starts_trial_or_timer": False, "performs_native_cli_calls": False,
        "source_candidate_sha256": G226_SHA if not synthetic else None,
        "public_kit_sha256": digest,
        "catalog_actions_checked": actions,
        "current_skill_rechecked": bound is not None,
        "current_skill_instruction_sha256": (
            bound["guarded_instruction_sha256"] if bound else []),
        "current_skill_policy_status": (
            bound["status"] if bound else "SKILL_NOT_SUPPLIED"),
        "may_activate_nas_trial": False,
        "exact_registered_expert_signatures_verified": False,
        "effective_nas_permissions_verified": False,
        "native_return_envelope_verified": False,
        "owner_explicit_live_authorization_received": False,
        "scenarios": stages,
        "nas_verified": False,
        "official_creator_provenance_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
    }


def summarize_operator_notes(packet: object, notes: object) -> dict:
    """Operator-supplied outcomes are NEVER independent device evidence."""
    if (type(packet) is not dict or packet.get("schema") != SCHEMA or
            packet.get("nas_verified") is not False or
            packet.get("release_gate") != "HOLD" or
            type(packet.get("scenarios")) is not list or
            [x.get("id") for x in packet["scenarios"]] !=
            [x[0] for x in STAGES] or
            type(notes) is not list or len(notes) > len(STAGES)):
        raise TrialReadinessRefused("TRIAL_NOTES_OR_SOURCE_INVALID")
    seen = set()
    counts = {k:0 for k in OUTCOMES}
    for item in notes:
        if (type(item) is not dict or set(item) !=
                {"case_id", "outcome", "trace_sha256", "reason_code"} or
                item["case_id"] not in [x[0] for x in STAGES] or
                item["case_id"] in seen or item["outcome"] not in OUTCOMES or
                item["reason_code"] not in NOTES or
                (item["trace_sha256"] is not None and (
                    type(item["trace_sha256"]) is not str or
                    not SHA.fullmatch(item["trace_sha256"])))):
            raise TrialReadinessRefused("UNSUPPORTED_OR_PRIVATE_OPERATOR_NOTE")
        seen.add(item["case_id"])
        counts[item["outcome"]] += 1
    return {
        "schema": "flowpilot-g257-operator-report-no-independent-proof-v1",
        "status": "REQUIRES_INDEPENDENT_REGISTERED_NAS_READBACK",
        "counts": counts,
        "owner_notes_received": len(notes),
        "raw_paths_emitted": False, "no_nas_claims_accepted": True,
        "nas_verified": False, "release_gate": "HOLD",
    }


def _strict_json(data: bytes) -> object:
    def unique(pairs):
        if len(pairs) != len({key for key,_ in pairs}):
            raise TrialReadinessRefused("DUPLICATE_JSON_KEY")
        return dict(pairs)
    if len(data) > 16384:
        raise TrialReadinessRefused("UNBOUNDED_PRIVATE_RECEIPT")
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G257 offline-only NAS trial readiness; no timer")
    parser.add_argument("--official-kit", required=True, type=Path)
    parser.add_argument("--g256-private-receipt", required=True, type=Path)
    parser.add_argument("--candidate-skill", type=Path,
                        help="Exact private G226 ZIP; no vendor/provider invocation")
    parser.add_argument("--owner-scope-request", type=Path,
                        help="Optional private owner-declared metadata scope JSON; only a plan")
    args = parser.parse_args(argv)
    # G259: a human-readable WAITING status is NOT a successful pre-trial
    # command. Reject before reading any owner-controlled private files.
    if args.candidate_skill is None:
        print(json.dumps({
            "status": "G259_CURRENT_G226_SKILL_REQUIRED",
            "current_skill_rechecked": False, "nas_verified": False,
            "release_gate": "HOLD"}, sort_keys=True))
        return 2
    try:
        files = [args.official_kit, args.g256_private_receipt]
        if args.candidate_skill is not None:
            files.append(args.candidate_skill)
        if any(not p.is_file() or p.is_symlink() for p in files):
            raise TrialReadinessRefused("OWNER_PRIVATE_SOURCE_INVALID")
        candidate = (args.candidate_skill.read_bytes() if args.candidate_skill
                     is not None else None)
        if args.owner_scope_request is not None and (
                not args.owner_scope_request.is_file() or
                args.owner_scope_request.is_symlink()):
            raise TrialReadinessRefused("OWNER_SCOPE_INPUT_INVALID")
        scope_receipt = (bind_owner_scope(_strict_json(
            args.owner_scope_request.read_bytes()))
            if args.owner_scope_request is not None else None)
        out = prepare_trial(files[0].read_bytes(), _strict_json(files[1].read_bytes()),
                            candidate_skill=candidate)
    except (OSError, ValueError, TypeError, UnsafePackage, ScopeRefused, KeyError):
        print(json.dumps({"status": "G257_OFFLINE_TRIAL_READINESS_REFUSED",
                          "nas_verified": False, "release_gate": "HOLD"}))
        return 2
    # G259: report success ONLY for a current byte-checked source and pinned
    # Kit. A plan, old receipt or simulator alone cannot start owner testing.
    ready = (out.get("status") == "CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY"
             and out.get("current_skill_rechecked") is True
             and len(out.get("current_skill_instruction_sha256", [])) == 2
             and out.get("nas_verified") is False
             and out.get("may_activate_nas_trial") is False
             and out.get("release_gate") == "HOLD")
    if not ready:
        print(json.dumps({
            "status": "G259_REAL_SOURCE_BOUND_OFFLINE_PREFLIGHT_INCOMPLETE",
            "current_skill_rechecked": out.get("current_skill_rechecked") is True,
            "nas_verified": False, "release_gate": "HOLD"}, sort_keys=True))
        return 2
    if scope_receipt is not None:
        out["operator_scope"] = {
            "schema": scope_receipt["schema"],
            "status": scope_receipt["status"],
            "request_sha256": scope_receipt["request_sha256"],
            "required_file_count": scope_receipt["required_file_count"],
            "owner_paths_exposed": False,
            "consent_independently_verified": False,
            "actual_native_instruction_created": False,
        }
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
