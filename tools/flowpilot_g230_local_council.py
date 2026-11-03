"""G230: deterministic owner-review council and report from real LOCAL evidence.

Four independent *policy perspectives*, NOT independent model agents.
Consumes the previously persisted and checked G227 receipt; performs no
filesystem read, NAS/Expert call, subprocess, external request or database write.
"""
from __future__ import annotations

import re

SCHEMA = "flowpilot-local-council-g230-v1"
REPORT_SCHEMA = "flowpilot-local-operator-report-g230-v1"
SHA = re.compile(r"[0-9a-f]{64}\Z")
WORKFLOW = re.compile(r"wf_[0-9a-f]{32}\Z")
STATES = ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")


class CouncilRefused(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


def evaluate_local_receipt(receipt: object, *, workflow_id: object,
                           plan_sha256: object) -> dict:
    """Output cannot say NAS-ready even when all local checklist items exist."""
    if (type(receipt) is not dict or
            receipt.get("status") != "REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS" or
            receipt.get("release_gate") != "HOLD" or
            receipt.get("verified_actual_nas") is not False or
            receipt.get("source_files_opened") is not False or
            type(workflow_id) is not str or WORKFLOW.fullmatch(workflow_id) is None or
            type(plan_sha256) is not str or SHA.fullmatch(plan_sha256) is None):
        raise CouncilRefused("VERIFIED_LOCAL_RECEIPT_REQUIRED")
    fingerprint = receipt.get("record_sha256")
    record = receipt.get("record")
    if (type(fingerprint) is not str or SHA.fullmatch(fingerprint) is None or
            type(record) is not dict or
            record.get("workflow_id") != workflow_id or
            record.get("local_metadata_only") is not True or
            record.get("file_contents_opened") is not False or
            record.get("registered_expert_invoked") is not False or
            record.get("nas_verified") is not False or
            record.get("release_gate") != "HOLD"):
        raise CouncilRefused("RECEIPT_PROVENANCE_REFUSED")
    # The caller MUST obtain receipt using the G227 SQLite integrity-checked
    # readback method; untrusted JSON cannot authenticate itself with a hash.
    rows = record.get("findings")
    if (type(rows) is not list or type(record.get("item_count")) is not int or
            not 1 <= len(rows) == record["item_count"] <= 20 or
            any(type(row) is not dict or set(row) != {"index", "state"}
                or type(row["index"]) is not int or row["index"] != idx
                or type(row["state"]) is not str or row["state"] not in STATES
                for idx, row in enumerate(rows, 1))):
        raise CouncilRefused("UNTRUSTED_LOCAL_FINDINGS")
    counts = {s: sum(row["state"] == s for row in rows) for s in STATES}
    unknown = counts["NOT_CHECKED"] + counts["VERSION_REVIEW"]
    missing = counts["MISSING"]
    if record.get("inspection_status") != (
            "LOCAL_METADATA_FINDINGS_READY" if missing == 0 and unknown == 0
            else "LOCAL_METADATA_BLOCKED"):
        raise CouncilRefused("LOCAL_STATUS_MISMATCH")
    builder = "BLOCKED" if missing else ("REVIEW" if unknown else "PASS_LOCAL")
    qa = "BLOCKED" if missing else ("REVIEW" if unknown else "PASS_LOCAL")
    verdict = ("LOCAL_BLOCKED_MISSING_FILES" if missing else
               "LOCAL_REVIEW_REQUIRED" if unknown else
               "LOCAL_CHECKLIST_COMPLETE_NOT_NAS")
    roles = [
        {"role": "Architect", "status": "PASS_LOCAL",
         "reason": "TYPED_FILE_TEMPLATE_AND_BOUNDED_INDEXES"},
        {"role": "Security", "status": "PASS_LOCAL",
         "reason": "CONSENTED_LOCAL_METADATA_ONLY_NO_CONTENT"},
        {"role": "Builder", "status": builder,
         "reason": ("MISSING_REQUIRED_ITEMS" if missing else
                    "UNCERTAIN_ITEMS" if unknown else "ALL_INDEXES_PRESENT")},
        {"role": "QA", "status": qa,
         "reason": ("LOCAL_FINDINGS_BLOCKED" if missing else
                    "REVIEW_UNCERTAIN_LOCAL_FINDINGS" if unknown else
                    "LOCAL_RECEIPT_CONSISTENT_NOT_NAS")},
    ]
    # One bounded proposed correction, NEVER a filesystem mutation or retry.
    proposed = {
        "kind": ("OWNER_REVIEW_MISSING_ITEMS" if missing else
                 "OWNER_VERIFY_UNCERTAIN_ITEMS" if unknown else "NONE"),
        "item_indexes": [r["index"] for r in rows
                         if r["state"] in ("MISSING", "NOT_CHECKED", "VERSION_REVIEW")],
        "proposed_only": True, "repair_count": 0, "max_proposed_revisions": 1,
        "filesystem_modified": False, "rerun_started": False,
    }
    return {
        "schema": SCHEMA, "status": verdict, "workflow_id": workflow_id,
        "plan_sha256": plan_sha256, "local_receipt_sha256": fingerprint,
        "item_count": len(rows), "counts": counts, "findings": [
            {"index": row["index"], "state": row["state"]} for row in rows],
        "roles": roles, "proposed_correction": proposed,
        "policy_engine": "FOUR_DETERMINISTIC_LOCAL_PERSPECTIVES_NOT_AI_AGENTS",
        "local_evidence_verified": True, "owner_files_opened_by_council": False,
        "real_nas_verified": False, "registered_expert_invoked": False,
        "docker_executed": False, "independent_ai_council_invoked": False,
        "nas_execution_approved": False, "release_gate": "HOLD",
    }


def owner_report(review: object) -> dict:
    if (type(review) is not dict or review.get("schema") != SCHEMA or
            review.get("release_gate") != "HOLD" or
            review.get("real_nas_verified") is not False or
            review.get("registered_expert_invoked") is not False or
            review.get("independent_ai_council_invoked") is not False or
            review.get("status") not in (
                "LOCAL_BLOCKED_MISSING_FILES",
                "LOCAL_REVIEW_REQUIRED",
                "LOCAL_CHECKLIST_COMPLETE_NOT_NAS") or
            type(review.get("roles")) is not list or
            [r.get("role") for r in review["roles"]] !=
            ["Architect", "Security", "Builder", "QA"]):
        raise CouncilRefused("VERIFIED_COUNCIL_REQUIRED")
    # Only code-defined tokens and indexes: never store or emit raw filenames.
    counts = review["counts"]
    summary = (
        "Required local files are missing; delivery remains blocked."
        if review["status"] == "LOCAL_BLOCKED_MISSING_FILES" else
        "Local inventory includes uncertain states; manual review is required."
        if review["status"] == "LOCAL_REVIEW_REQUIRED" else
        "All required local files were present at inspection time; NAS and "
        "document contents remain unverified."
    )
    lines = [
        "# FlowPilot 3.0 - local delivery evidence",
        "",
        f"Verdict: {review['status']}",
        f"Evidence SHA-256: {review['local_receipt_sha256']}",
        f"Plan SHA-256: {review['plan_sha256']}",
        f"Total: {review['item_count']} | Present: {counts['PRESENT']} | "
        f"Missing: {counts['MISSING']} | Unchecked: {counts['NOT_CHECKED']} | "
        f"Version review: {counts['VERSION_REVIEW']}",
        "",
        "## Four deterministic review perspectives",
        *[f"- {r['role']}: {r['status']} ({r['reason']})"
          for r in review["roles"]],
        "",
        "## Owner follow-up",
        summary,
        f"Suggested action: {review['proposed_correction']['kind']}",
        "Item indexes: " + (
            ", ".join(str(n) for n in review["proposed_correction"]["item_indexes"])
            or "none"),
        "No edits, retries or NAS commands have been executed.",
        "",
        "Scope: one previously approved LOCAL filesystem metadata observation.",
        "No document content was read; a local hash is not independent attestation.",
        "Actual Uliya Expert, NAS permissions, live device and production are NOT VERIFIED.",
        "RELEASE HOLD.",
    ]
    return {
        "schema": REPORT_SCHEMA, "status": "OWNER_LOCAL_REPORT_READY_NOT_NAS",
        "workflow_id": review["workflow_id"],
        "source_receipt_sha256": review["local_receipt_sha256"],
        "verdict": review["status"], "report_markdown": "\n".join(lines) + "\n",
        "owner_actions_required": (
            "REVIEW_INDEXED_LOCAL_ITEMS" if
            review["proposed_correction"]["kind"] != "NONE"
            else "VERIFY_DEVICE_CAPABILITIES_AND_EXPLICIT_APPROVAL"),
        "file_contents_opened": False, "report_data_is_redacted": True,
        "real_nas_verified": False, "external_request_performed": False,
        "release_gate": "HOLD",
    }
