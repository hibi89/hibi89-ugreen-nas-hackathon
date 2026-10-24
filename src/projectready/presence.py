"""Provisional G2 read-only evidence-scanning contract. NOT the Uliya SDK schema.

Pure functions only: no filesystem access, IO, network, secrets, or NAS calls.
The trusted adapter is not available; adapter_verified must remain False for
real-world use until official registered-agent/CLI semantics are demonstrated.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .readiness import Requirement, ScanStatus, Verdict, _safe_rel_path


class EvidenceOrigin(str, Enum):
    SYNTHETIC = "SYNTHETIC"
    SDK_VERIFIED = "SDK_VERIFIED"  # An assertion, not automatically proof.


@dataclass(frozen=True)
class FileEvidence:
    relative_path: str
    evidence_ref: str
    is_file: bool = True


@dataclass(frozen=True)
class ScanEnvelope:
    authorized_root_ref: str
    scope_prefix: str
    status: ScanStatus
    evidence_origin: EvidenceOrigin
    adapter_verified: bool
    permission_granted: bool
    pagination_exhausted: bool
    complete_scope: bool
    observations: tuple[FileEvidence, ...]
    scan_reference: str = ""


@dataclass(frozen=True)
class PresenceCheck:
    requirement_id: str
    relative_path: str
    verdict: Verdict
    evidence_refs: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class PresenceReport:
    checks: tuple[PresenceCheck, ...]
    trusted: bool
    limitations: tuple[str, ...]


def _within_scope(path: str, prefix: str) -> bool:
    return not prefix or path.startswith(prefix + "/")


def check_presence(
    requirements: Sequence[Requirement], envelope: ScanEnvelope
) -> PresenceReport:
    """Check exact authorized relative paths with conservative provenance.

    This is a contract test only. Callers cannot establish real Uliya
    authorization merely by passing truthy booleans in a synthetic fixture.
    """
    if not requirements:
        raise ValueError("At least one explicit deliverable required")
    if not isinstance(envelope.authorized_root_ref, str) or not envelope.authorized_root_ref.strip():
        raise ValueError("Missing authorized root reference")
    prefix = _safe_rel_path(envelope.scope_prefix) if envelope.scope_prefix else ""
    status = ScanStatus(envelope.status)
    source = EvidenceOrigin(envelope.evidence_origin)
    seen_ids: set[str] = set()
    for item in requirements:
        if not item.id or item.id in seen_ids:
            raise ValueError("Missing or duplicate requirement ID")
        seen_ids.add(item.id)
        path = _safe_rel_path(item.relative_path)
        if not _within_scope(path, prefix):
            raise ValueError("Requirement would escape authorized scope")
    observed: dict[str, list[FileEvidence]] = {}
    for item in envelope.observations:
        path = _safe_rel_path(item.relative_path)
        if not _within_scope(path, prefix):
            raise ValueError("Scan result contains out-of-scope path")
        observed.setdefault(path, []).append(item)

    # Explicit simulation trust is a hypothesis, never UGREEN production proof.
    trusted = (
        source == EvidenceOrigin.SDK_VERIFIED
        and envelope.adapter_verified
        and envelope.permission_granted
        and bool(envelope.scan_reference.strip())
        and status in (ScanStatus.COMPLETE, ScanStatus.PARTIAL)
    )
    safe_full = (
        trusted and status == ScanStatus.COMPLETE
        and envelope.pagination_exhausted and envelope.complete_scope
    )
    checks: list[PresenceCheck] = []
    limitations: list[str] = []
    for required in requirements:
        path = required.relative_path
        entries = observed.get(path, [])
        files = [e for e in entries if e.is_file]
        file_refs = tuple(e.evidence_ref for e in files)
        if not trusted:
            verdict, reason, refs = (
                Verdict.NOT_CHECKED,
                "No verified, authorized official SDK observation source",
                (),
            )
        elif len(entries) > 1:
            verdict, reason, refs = (
                Verdict.REVIEW,
                "Multiple ambiguous observations of the same path",
                (),
            )
        elif len(files) == 1 and file_refs[0].strip():
            verdict, reason, refs = (
                Verdict.PASS,
                "Exact authorized file seen; reference supplied by adapter",
                file_refs,
            )
        elif entries:  # Directory or file with missing evidence reference
            verdict, reason, refs = (
                Verdict.NOT_CHECKED,
                "Path matched but file/evidence cannot be verified",
                (),
            )
        elif safe_full:
            verdict, reason, refs = (
                Verdict.FAIL,
                "Absent in declared complete, authorized, fully paginated scan",
                (),
            )
        else:
            verdict, reason, refs = (
                Verdict.NOT_CHECKED,
                "Absence unproven: incomplete scan, pagination or permission",
                (),
            )
        checks.append(PresenceCheck(required.id, path, verdict, refs, reason))
        if verdict != Verdict.PASS:
            limitations.append(f"{required.id}: {reason}")
    return PresenceReport(tuple(checks), trusted, tuple(limitations))
