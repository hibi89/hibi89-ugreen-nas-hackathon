"""Read-only version candidate signals. Not Uliya version metadata or latest-version proof.

Only flags *filename patterns*; no content, modification time or hash evidence.
Never automatically promotes a version gate to PASS.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
import re

from .presence import ScanEnvelope, check_presence
from .readiness import Requirement, ScanStatus, _safe_rel_path


_TRAILING = re.compile(
    r"(?:[_\-.](?:v[0-9]+|rev[0-9]+|version[0-9]+|final|draft|copy[0-9]*))+$",
    re.IGNORECASE,
)

class VersionSignal(str, Enum):
    NOT_CHECKED = "NOT_CHECKED"
    NONE_DETECTED = "NONE_DETECTED"
    CANDIDATES_REVIEW = "CANDIDATES_REVIEW"


@dataclass(frozen=True)
class VersionCandidate:
    relative_path: str
    evidence_ref: str


@dataclass(frozen=True)
class VersionFinding:
    requirement_id: str
    signal: VersionSignal
    candidates: tuple[VersionCandidate, ...]
    reason: str
    authoritatively_verified_current_version: bool = False


def _base(path: str) -> tuple[str, str, str]:
    clean = _safe_rel_path(path)
    p = PurePosixPath(clean)
    extension = p.suffix.lower()
    base = p.name[:-len(extension)] if extension else p.name
    normalized = _TRAILING.sub("", base)
    return str(p.parent), normalized.lower(), extension


def detect_version_candidates(
    requirement: Requirement, envelope: ScanEnvelope
) -> VersionFinding:
    """Identify ambiguous filename variants only within authorized scope.

    Even NONE_DETECTED cannot prove 'latest', content identity, or absence of
    revisions not following naming conventions. It must not set gate:version PASS.
    """
    # Reuse the authorization/scope/provenance validation. A synthetic caller
    # may assert SDK_VERIFIED in tests; production adapter must prove it.
    presence = check_presence((requirement,), envelope)
    if not presence.trusted or ScanStatus(envelope.status) != ScanStatus.COMPLETE:
        return VersionFinding(
            requirement.id, VersionSignal.NOT_CHECKED, (),
            "Authorized complete official source not validated"
        )
    if not (envelope.pagination_exhausted and envelope.complete_scope):
        return VersionFinding(
            requirement.id, VersionSignal.NOT_CHECKED, (),
            "Search may omit additional versions"
        )
    target = _base(requirement.relative_path)
    candidates = [
        VersionCandidate(e.relative_path, e.evidence_ref)
        for e in envelope.observations
        if e.is_file and _base(e.relative_path) == target
    ]
    # Source refs must identify real observations; unknown IDs cannot prove
    # that two different files exist.
    if any(not x.evidence_ref.strip() for x in candidates):
        return VersionFinding(
            requirement.id, VersionSignal.NOT_CHECKED, (),
            "Candidate lacking evidence reference"
        )
    unique = {(x.relative_path, x.evidence_ref): x for x in candidates}
    found = tuple(sorted(unique.values(), key=lambda x: (x.relative_path, x.evidence_ref)))
    if len(found) > 1:
        return VersionFinding(
            requirement.id, VersionSignal.CANDIDATES_REVIEW, found,
            "Filename variants require human/official supported verification; do not choose newest"
        )
    return VersionFinding(
        requirement.id, VersionSignal.NONE_DETECTED, found,
        "No competing filename variant detected; real version gate remains NOT_CHECKED"
    )
