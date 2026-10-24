"""Offline G4 composition: all checks into one conservative customer-facing report.

No source of actual UGREEN CLI truth is available. Never describe synthetic fixtures
as customer verification or imply PII safety on the basis of a filename.
"""
from dataclasses import dataclass

from .policy_guard import Action, Policy, Result, assess
from .presence import PresenceReport, ScanEnvelope, check_presence
from .readiness import Overall, Requirement, Verdict
from .version_candidates import VersionFinding, VersionSignal, detect_version_candidates

@dataclass(frozen=True)
class CombinedReport:
    overall: Overall
    presence: PresenceReport
    versions: tuple[VersionFinding, ...]
    policy_decision: Result
    privacy_check: Verdict
    version_verification: Verdict
    limitations: tuple[str, ...]
    is_real_nas_validation: bool = False

def assemble(requirements: tuple[Requirement, ...],
             scan: ScanEnvelope,
             policy: Policy) -> CombinedReport:
    """Pure deterministic assembly for engineering simulation only."""
    presence = check_presence(requirements, scan)
    versions = tuple(detect_version_candidates(r,scan) for r in requirements)
    permission = assess(Action.LIST,policy)
    problems = list(presence.limitations)
    if permission.decision != Result.ELIGIBLE_FOR_ADAPTER_CHECK:
        problems.append("No validated read-only policy/adapter eligibility")
    if any(item.signal==VersionSignal.CANDIDATES_REVIEW for item in versions):
        problems.append("Competing named file versions require review")
    if any(item.signal==VersionSignal.NOT_CHECKED for item in versions):
        problems.append("Version candidate scan unverified")
    # Without an actual documented first-party verifier, these MUST remain
    # NOT_CHECKED; no fabricated privacy or authoritative version PASS.
    problems.append("Authoritative version validation NOT_CHECKED")
    problems.append("Sensitive-content disclosure validation NOT_CHECKED")
    blocked = any(r.verdict==Verdict.FAIL for r in presence.checks)
    overall = Overall.BLOCKED if blocked else Overall.NEEDS_REVIEW
    return CombinedReport(
        overall=overall,
        presence=presence,
        versions=versions,
        policy_decision=permission.decision,
        privacy_check=Verdict.NOT_CHECKED,
        version_verification=Verdict.NOT_CHECKED,
        limitations=tuple(problems),
    )
