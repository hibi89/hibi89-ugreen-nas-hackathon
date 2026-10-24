"""Offline deterministic delivery-readiness contract. NOT a Uliya API implementation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_CHECKED = "NOT_CHECKED"

class ScanStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    DENIED = "DENIED"
    NOT_RUN = "NOT_RUN"

class Overall(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

REQUIRED_GATES = ("version", "access", "privacy")

@dataclass(frozen=True)
class Requirement:
    id: str
    relative_path: str
    mandatory: bool = True

@dataclass(frozen=True)
class Check:
    id: str
    verdict: Verdict
    evidence: tuple[str, ...]
    note: str

@dataclass(frozen=True)
class Audit:
    overall: Overall
    checks: tuple[Check, ...]
    scan_status: ScanStatus
    limitations: tuple[str, ...]

def _safe_rel_path(value: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise ValueError("expected nonempty POSIX relative path")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("noncanonical or traversal path")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError("control character in path")
    return value

def evaluate(
    requirements: Sequence[Requirement],
    observed_paths: Sequence[str],
    scan_status: ScanStatus,
    gate_results: Mapping[str, Verdict] | None = None,
) -> Audit:
    """Assess provided synthetic/verified metadata; never query or mutate a NAS.

    Only a separately validated, authorized adapter may supply real observations.
    Gate assertions passed to this function are NOT proof of real Uliya checks.
    """
    scan_status = ScanStatus(scan_status)
    if not requirements:
        raise ValueError("at least one explicit deliverable required")
    ids: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement.id, str) or not requirement.id.strip():
            raise ValueError("requirement id missing")
        if requirement.id in ids:
            raise ValueError("duplicate requirement id")
        ids.add(requirement.id)
        _safe_rel_path(requirement.relative_path)
    observed = {_safe_rel_path(path) for path in observed_paths}
    supplied_gates = dict(gate_results or {})
    if set(supplied_gates) - set(REQUIRED_GATES):
        raise ValueError("unknown gate, cannot silently bypass it")

    checks: list[Check] = []
    limitations: list[str] = []
    for requirement in requirements:
        path = requirement.relative_path
        if path in observed and scan_status in (ScanStatus.COMPLETE, ScanStatus.PARTIAL):
            status = Verdict.PASS
            note = "Exact path reported present; adapter not verified"
        elif scan_status == ScanStatus.COMPLETE:
            status = Verdict.FAIL
            note = "Path missing in declared complete authorized scan"
        else:
            status = Verdict.NOT_CHECKED
            note = "Absence unproven: scan partial, denied or not run"
        if status != Verdict.PASS:
            limitations.append(f"{requirement.id}: {note}")
        checks.append(Check(requirement.id, status, (path,) if status == Verdict.PASS else (), note))

    for gate in REQUIRED_GATES:
        gate_verdict = Verdict(supplied_gates.get(gate, Verdict.NOT_CHECKED))
        reason = (
            "Caller-provided gate result: independent evidence required"
            if gate_verdict != Verdict.NOT_CHECKED
            else "Required gate not checked: READY prohibited"
        )
        checks.append(Check(f"gate:{gate}", gate_verdict, (), reason))
        if gate_verdict != Verdict.PASS:
            limitations.append(f"{gate}: {reason}")

    mandatory_ids = {item.id for item in requirements if item.mandatory}
    relevant = [item for item in checks if item.id in mandatory_ids or item.id.startswith("gate:")]
    if any(item.verdict == Verdict.FAIL for item in relevant):
        overall = Overall.BLOCKED
    elif any(item.verdict != Verdict.PASS for item in relevant):
        overall = Overall.NEEDS_REVIEW
    else:
        overall = Overall.READY
    return Audit(overall, tuple(checks), scan_status, tuple(limitations))
