"""Ensure consent applies to precisely the FlowPilot preview being reviewed.

Compares only already-supplied, in-memory strings and bounded goal labels.
No file access, path resolving, execution or NAS integration occurs.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

INTENT_LABELS = {
    "check handoff deliverables": "HANDOFF_AUDIT",
    "check required files": "CHECK_REQUIRED",
    "compare versions": "REVIEW_VERSIONS",
}


class ApprovalScopeMismatch(ValueError):
    """Consent does not cover the exact proposed preview and inputs."""


def require_exact_approval_scope(request, *, root, required, candidates, preview):
    """Fail closed before LA receives a plan; do not touch owner files.

    An explicit list of authorized_intents is required for multi-action plans.
    Version alternatives need their own exact owner-provided scope mapping.
    """
    if not isinstance(request, Mapping) or not isinstance(preview, dict):
        raise ApprovalScopeMismatch("invalid approval envelope")
    if preview.get("status") != "WAITING_APPROVAL":
        raise ApprovalScopeMismatch("proposal is not awaiting approval")
    if (not isinstance(root, (str, Path)) or str(root) != request.get("folder")
            or type(required) is not list or required != request.get("required_paths")):
        raise ApprovalScopeMismatch("approved folder/checklist differs from proposed scope")
    rows = preview.get("plan")
    if type(rows) is not list or not 1 <= len(rows) <= 3:
        raise ApprovalScopeMismatch("missing or oversized preview plan")
    expected = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or set(row) != {"index", "read_only_action"}:
            raise ApprovalScopeMismatch("unexpected preview step")
        if type(row["index"]) is not int or row["index"] != index:
            raise ApprovalScopeMismatch("invalid step order")
        intent = INTENT_LABELS.get(row["read_only_action"])
        if intent is None:
            raise ApprovalScopeMismatch("unsupported preview action")
        expected.append(intent)
    if request.get("intent") != expected[0]:
        raise ApprovalScopeMismatch("approved primary intent differs from preview")
    if len(expected) > 1 and request.get("authorized_intents") != expected:
        raise ApprovalScopeMismatch("all actions require explicit matching approval")
    if len(expected) == 1 and request.get("authorized_intents") not in (None, expected):
        raise ApprovalScopeMismatch("unexpected extra authorized actions")
    versions_needed = "REVIEW_VERSIONS" in expected
    if versions_needed:
        if (not isinstance(candidates, dict) or not candidates
                or candidates != request.get("version_candidates")):
            raise ApprovalScopeMismatch("version candidates not explicitly approved")
    elif candidates not in (None, {}):
        raise ApprovalScopeMismatch("unexpected version candidates")
    return True
