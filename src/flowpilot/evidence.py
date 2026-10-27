"""FlowPilot offline evidence-to-report contract, no filesystem or NAS I/O.

The caller must NOT use this engine as proof of actual registered Uliya Agent
execution, effective permissions, private model processing or NAS safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
import re
import unicodedata


class ItemState(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    NOT_CHECKED = "NOT_CHECKED"
    VERSION_REVIEW = "VERSION_REVIEW"


class Overall(str, Enum):
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True)
class Observed:
    relative_path: str
    reference: str
    is_symlink: bool = False
    contained: bool | None = None


@dataclass(frozen=True)
class ObservationBatch:
    authorized_root: str
    observations: tuple[Observed, ...]
    permission_confirmed: bool = False
    registered_adapter_confirmed: bool = False
    scan_complete: bool = False
    pagination_complete: bool = False
    failed: bool = False


@dataclass(frozen=True)
class EvidenceItem:
    relative_path: str
    state: ItemState
    evidence: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class EvidenceReport:
    items: tuple[EvidenceItem, ...]
    overall: Overall
    scope_complete: bool
    limitations: tuple[str, ...]
    actual_nas_verified: bool = False


_RESTRICTED = re.compile(
    r"(^|[._-])(env|ssh|git|token|tokens|secret|secrets|password|passwords|credential|credentials|private[._-]?key|api[._-]?key|access[._-]?key|service[._-]?account|session|sessions|auth)([._-]|$)"
    r"|(^|[.])(pem|p12|pfx|key|kdbx|asc|gpg)$"
    r"|^(config[.]json|id_rsa|id_ed25519|authorized_keys|known_hosts|[.]npmrc|[.]netrc|[.]aws|[.]kube|[.]gnupg|[.]docker)$", re.IGNORECASE
)


def safe_path(path: str) -> str:
    """Reject traversal, restricted filenames and noncanonical input.

    This is ONLY a string guard, not a substitute for official symlink or
    effective-permission validation in the real registered adapter.
    """
    if not isinstance(path, str) or not path or path != path.strip():
        raise ValueError("Invalid scoped path")
    if unicodedata.normalize("NFKC", path) != path or path.startswith(("/", "~")):
        raise ValueError("Not a canonical relative path")
    if ":" in path or "%" in path or "\\" in path or any(ord(ch) < 32 or ord(ch) == 127 or unicodedata.category(ch) == "Cf" for ch in path):
        raise ValueError("Ambiguous separator or control character")
    pieces = path.split("/")
    if any(not part or part in (".", "..") or part.endswith((".", " ")) for part in pieces):
        raise ValueError("Traversal or noncanonical path")
    if any(_RESTRICTED.search(part) for part in pieces):
        raise ValueError("Restricted file or folder")
    return path


def report(
    required_paths: Sequence[str],
    batch: ObservationBatch,
    *,
    version_candidates: dict[str, Sequence[str]] | None = None,
) -> EvidenceReport:
    """Convert already supplied metadata into conservative item states.

    Missing is never concluded from an incomplete, denied, failed, or
    untrusted scan. Even with all caller flags true, the result is not a NAS
    release certificate, because booleans are assertions not provenance.
    """
    if not required_paths:
        raise ValueError("No mandatory items")
    if not isinstance(batch.authorized_root, str) or not batch.authorized_root.strip():
        raise ValueError("No authorized root reference")
    requested = tuple(safe_path(path) for path in required_paths)
    if len(set(requested)) != len(requested) or len(requested) > 100:
        raise ValueError("Duplicate or excessive checklist")
    for obs in batch.observations:
        safe_path(obs.relative_path)
        if not isinstance(obs.reference, str):
            raise ValueError("Invalid evidence reference")
    versions = version_candidates or {}
    if any(key not in requested for key in versions):
        raise ValueError("Version requirements outside checklist")
    for variants in versions.values():
        for path in variants:
            safe_path(path)
    complete = all((batch.permission_confirmed, batch.registered_adapter_confirmed,
                    batch.scan_complete, batch.pagination_complete, not batch.failed))
    limitations = ["OFFLINE_EVIDENCE_ASSEMBLY_ONLY; live NAS and Agent provenance NOT_VERIFIED"]
    if not complete:
        limitations.append("No complete verified and authorized file enumeration")
    rows = []
    for wanted in requested:
        found = [o for o in batch.observations if o.relative_path == wanted]
        usable = [o for o in found if o.reference.strip() and o.is_symlink is False and o.contained is True]
        untrusted_found = bool(found) and len(usable) != len(found)
        # A single alternative version is not proof that a requirement is missing.
        # Unverified symlink or containment for any candidate invalidates the scan.
        candidate_paths = set(versions.get(wanted, ()))
        candidates = [o for o in batch.observations
                      if o.relative_path in candidate_paths | {wanted}]
        untrusted_candidate = any(
            not o.reference.strip() or o.is_symlink is not False or o.contained is not True
            for o in candidates
        )
        detected = {o.relative_path for o in candidates
                    if o.reference.strip() and o.is_symlink is False and o.contained is True}
        if not complete or untrusted_found or untrusted_candidate:
            state, refs, reason = ItemState.NOT_CHECKED, (), "Scan, permission, symlink target or evidence unverified"
        elif detected - {wanted} or len(usable) > 1:
            state, refs, reason = ItemState.VERSION_REVIEW, (), "Alternative or competing version requires owner review"
        elif usable:
            state, refs, reason = ItemState.PRESENT, (usable[0].reference,), "Exact scoped file has attributable metadata"
        else:
            state, refs, reason = ItemState.MISSING, (), "Absent in claimed complete authorized enumeration"
        rows.append(EvidenceItem(wanted, state, refs, reason))
    overall = Overall.BLOCKED if any(row.state is ItemState.MISSING for row in rows) else Overall.NEEDS_REVIEW
    return EvidenceReport(tuple(rows), overall, complete, tuple(limitations))
