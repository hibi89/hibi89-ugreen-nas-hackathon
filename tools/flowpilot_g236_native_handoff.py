"""G236: safe, REDACTED handoff from verified LOCAL evidence to a future Uliya Expert.

Consumes only G230's deterministic local council, called by Backend after
G227 SQLite integrity readback. Public catalog labels are NOT callable native
signatures. No SDK invocation, credential use, NAS network, reads or writes.
"""
from __future__ import annotations

import hashlib
import json
import re

SCHEMA = "flowpilot-g236-redacted-native-handoff-v1"
COUNCIL = "flowpilot-local-council-g230-v1"
KINDS = {
    "REQUIRED_FILES": "ug-filesystem find",
    "REVIEW_VERSIONS": "ug-filesystem stat",
    "HANDOFF_CHECKLIST": "ug-filesystem find",
}
STATES = ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
PENDING = (
    "PINNED_CATALOG_IS_NOT_RUNTIME_REGISTRATION",
    "VERIFY_REGISTERED_EXPERT_IDENTITY_AND_EXACT_SIGNATURE",
    "VERIFY_EFFECTIVE_OWNER_SCOPED_READ_PERMISSION",
    "VERIFY_NATIVE_RESULT_SCHEMA_AND_COMPLETE_PAGINATION",
    "GET_DISTINCT_OWNER_APPROVAL_BEFORE_REAL_NAS_ACTION",
    "VERIFY_INDEPENDENT_LIVE_READBACK_AND_FAILURE_RECOVERY",
)
WORKFLOW = re.compile(r"wf_[0-9a-f]{32}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class NativeHandoffRefused(ValueError):
    def __init__(self, code="LOCAL_COUNCIL_REQUIRED", status=409):
        self.code, self.status = code, status
        super().__init__(code)


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()


def build_native_handoff(review: object) -> dict:
    """A future registered adapter may consume this checklist, NEVER execute it.

    Only Backend.native_handoff(), which obtains a G227 integrity-checked SQLite
    receipt then G230 council, may treat input as trusted LOCAL evidence. This
    function does not authenticate arbitrary caller-supplied council JSON.
    """
    if type(review) is not dict or review.get("schema") != COUNCIL:
        raise NativeHandoffRefused()
    wf = review.get("workflow_id")
    plan = review.get("plan_sha256")
    receipt = review.get("local_receipt_sha256")
    if (type(wf) is not str or not WORKFLOW.fullmatch(wf)
            or any(type(d) is not str or not DIGEST.fullmatch(d)
                   for d in (plan, receipt))
            or review.get("local_evidence_verified") is not True
            or review.get("release_gate") != "HOLD"
            or review.get("real_nas_verified") is not False
            or review.get("registered_expert_invoked") is not False
            or review.get("docker_executed") is not False
            or review.get("independent_ai_council_invoked") is not False
            or review.get("owner_files_opened_by_council") is not False):
        raise NativeHandoffRefused("LOCAL_PROVENANCE_OR_GATE_REFUSED")
    total = review.get("item_count")
    counts = review.get("counts")
    findings = review.get("findings")
    if (type(total) is not int or not 1 <= total <= 20
            or type(counts) is not dict or set(counts) != set(STATES)
            or any(type(counts[k]) is not int or counts[k] < 0 for k in STATES)
            or sum(counts.values()) != total
            or type(findings) is not list or len(findings) != total
            or any(type(v) is not dict or set(v) != {"index", "state"}
                   or type(v["index"]) is not int or v["index"] != i
                   or v["state"] not in STATES
                   for i, v in enumerate(findings, 1))):
        raise NativeHandoffRefused("LOCAL_FINDINGS_INVALID")
    if any(sum(v["state"] == k for v in findings) != counts[k] for k in STATES):
        raise NativeHandoffRefused("LOCAL_COUNT_CONFLICT")
    expected = ("LOCAL_BLOCKED_MISSING_FILES" if counts["MISSING"] else
                "LOCAL_REVIEW_REQUIRED" if counts["NOT_CHECKED"] or counts["VERSION_REVIEW"]
                else "LOCAL_CHECKLIST_COMPLETE_NOT_NAS")
    if review.get("status") != expected:
        raise NativeHandoffRefused("LOCAL_VERDICT_CONFLICT")
    roles = review.get("roles")
    if (type(roles) is not list or len(roles) != 4
            or [r.get("role") for r in roles if type(r) is dict] !=
            ["Architect", "Security", "Builder", "QA"]):
        raise NativeHandoffRefused("LOCAL_ROLES_INVALID")
    stages = review.get("stage_reviews")
    if type(stages) is not list or len(stages) > 8:
        raise NativeHandoffRefused("LOCAL_STAGES_INVALID")
    if not stages:
        stages = [{"stage_index": 1, "kind": "REQUIRED_FILES",
                   "item_count": total,
                   "verdict": ("BLOCKED" if counts["MISSING"] else
                               "REVIEW" if counts["NOT_CHECKED"] or counts["VERSION_REVIEW"]
                               else "PASS_LOCAL"),
                   "real_nas_verified": False}]
    steps = []
    checked = 0
    for i, stage in enumerate(stages, 1):
        if (type(stage) is not dict or
                set(stage) != {"stage_index", "kind", "item_count", "verdict",
                               "real_nas_verified"} or
                type(stage["stage_index"]) is not int or
                stage["stage_index"] != i or
                stage["kind"] not in KINDS or
                type(stage["item_count"]) is not int or
                not 1 <= stage["item_count"] <= 20 or
                stage["verdict"] not in ("BLOCKED", "REVIEW", "PASS_LOCAL") or
                stage["real_nas_verified"] is not False):
            raise NativeHandoffRefused("LOCAL_STAGE_CONTRACT_INVALID")
        segment = findings[checked:checked + stage["item_count"]]
        if len(segment) != stage["item_count"]:
            raise NativeHandoffRefused("LOCAL_STAGE_PARTITION_INVALID")
        missing = any(x["state"] == "MISSING" for x in segment)
        uncertain = any(x["state"] in ("NOT_CHECKED", "VERSION_REVIEW")
                        for x in segment)
        expected_verdict = "BLOCKED" if missing else "REVIEW" if uncertain else "PASS_LOCAL"
        if stage["verdict"] != expected_verdict:
            raise NativeHandoffRefused("LOCAL_STAGE_VERDICT_CONFLICT")
        steps.append({
            "stage_index": i, "kind": stage["kind"],
            "item_count": stage["item_count"], "local_verdict": expected_verdict,
            "catalog_label_not_executable": KINDS[stage["kind"]],
            "native_argument_binding_verified": False,
            "registered_expert_verified": False,
            "native_result_schema_verified": False,
            "owner_live_approval_granted": False,
            "live_action_allowed": False,
        })
        checked += stage["item_count"]
    if checked != total:
        raise NativeHandoffRefused("LOCAL_STAGE_PARTITION_INVALID")
    result = {
        "schema": SCHEMA, "status": "NATIVE_EXECUTION_BLOCKED_PENDING_RUNTIME_EVIDENCE",
        "workflow_id": wf, "plan_sha256": plan,
        "local_receipt_sha256": receipt,
        "local_review_status": expected,
        "local_item_count": total, "stages": steps,
        "gate_reasons": list(PENDING),
        "source_level": "CONSENTED_LOCAL_METADATA_NOT_NAS",
        "catalog_claim_level": "PUBLIC_IDENTIFIER_ONLY_NOT_RUNTIME_CAPABILITY",
        "external_requests_performed": False, "owner_folder_rechecked": False,
        "actual_registered_expert_invoked": False, "effective_nas_rights_verified": False,
        "live_nas_readback_verified": False, "nas_verified": False,
        "release_gate": "HOLD",
    }
    return {**result, "handoff_sha256": _digest(result)}
