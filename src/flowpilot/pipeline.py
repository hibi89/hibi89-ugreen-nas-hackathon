"""G50 owner-authorized intent -> evidence result offline reference implementation.

Consumes in-memory, already-returned *synthetic* metadata only. No NAS or Uliya
client, filesystem access, network I/O, automation or external transfers.
A caller's claimed permission flags cannot certify any real platform action.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from .planner import Intent, Plan, State, draft_plan
from .evidence import EvidenceReport, ObservationBatch, Overall, ItemState, report


@dataclass(frozen=True)
class FlowResult:
    status: str
    plan: Plan
    report: EvidenceReport | None
    limitations: tuple[str, ...]
    actual_nas_verified: bool = False


def evaluate_offline(
    request: str,
    root: str = "",
    required_paths: Sequence[str] = (),
    *,
    metadata_approved: bool = False,
    unknown_processing_accepted: bool = False,
    batch: ObservationBatch | None = None,
    document_approved: bool = False,
    returned_document_refs: Sequence[str] = (),
    version_candidates: dict[str, Sequence[str]] | None = None,
) -> FlowResult:
    """Compose pure plan and evidence stages; never execute registered agents."""
    # Offline flags are untrusted caller claims. Never plan a document stage
    # from a partial, failed, permission-denied or unregistered file inventory.
    inventory_claimed_complete = batch is not None and all((
        batch.permission_confirmed is True, batch.registered_adapter_confirmed is True,
        batch.scan_complete is True, batch.pagination_complete is True,
        batch.failed is False,
    ))
    eligible_refs = returned_document_refs if inventory_claimed_complete else ()
    plan = draft_plan(
        request, root, required_paths,
        metadata_approved=metadata_approved,
        unknown_processing_accepted=unknown_processing_accepted,
        document_approved=document_approved,
        returned_document_refs=eligible_refs,
    )
    base = ("OFFLINE_ONLY", "LIVE_REGISTERED_AGENT_NOT_INVOKED",
            "PERMISSION_FLAGS_ARE_UNVERIFIED_CALLER_ASSERTIONS")
    if plan.state is not State.READY_FOR_ADAPTER_CHECK:
        return FlowResult(plan.state.value, plan, None, base + plan.limitations)
    if batch is None:
        return FlowResult("NEEDS_REVIEW", plan, None, base + ("NO_OBSERVED_METADATA",))
    if batch.authorized_root != plan.authorized_root:
        no_document = replace(plan, steps=tuple(step for step in plan.steps if step.id != "document"))
        return FlowResult("BLOCKED", no_document, None, base + ("ROOT_MISMATCH",))
    if plan.intent is Intent.SUMMARIZE_SELECTED and document_approved and returned_document_refs:
        if not inventory_claimed_complete:
            return FlowResult("NEEDS_REVIEW", plan, None,
                              base + ("DOCUMENT_STAGE_BLOCKED_UNVERIFIED_INVENTORY",))
        # A file merely found in the root is not an authorized checklist item.
        observed_refs = {
            item.reference for item in batch.observations
            if item.relative_path in plan.required_paths
            and item.contained is True and item.is_symlink is False
            and isinstance(item.reference, str) and item.reference.strip()
        }
        if not set(returned_document_refs).issubset(observed_refs):
            no_document = replace(plan, steps=tuple(s for s in plan.steps if s.id != "document"))
            return FlowResult("BLOCKED", no_document, None,
                              base + ("UNATTRIBUTABLE_DOCUMENT_REFERENCE",))
    findings = report(plan.required_paths, batch, version_candidates=version_candidates)
    if plan.intent is Intent.SUMMARIZE_SELECTED and document_approved and returned_document_refs:
        # Only unambiguous PRESENT evidence uniquely attributable to a
        # checklist item may appear in a selected-document plan. A claimed
        # complete listing alone cannot override symlink/version uncertainty.
        verified_refs = [
            ref for item in findings.items if item.state is ItemState.PRESENT
            for ref in item.evidence
        ]
        if (len(set(returned_document_refs)) != len(returned_document_refs)
                or any(verified_refs.count(ref) != 1 for ref in returned_document_refs)):
            no_document = replace(plan, steps=tuple(step for step in plan.steps if step.id != "document"))
            return FlowResult("NEEDS_REVIEW", no_document, findings,
                              base + findings.limitations +
                              ("DOCUMENT_STAGE_BLOCKED_UNVERIFIED_SELECTED_REFERENCE",))
    # An offline fixture cannot establish a real NAS READY state.
    status = Overall.BLOCKED.value if findings.overall is Overall.BLOCKED else Overall.NEEDS_REVIEW.value
    return FlowResult(status, plan, findings, base + findings.limitations)
