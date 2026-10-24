"""Synthetic read-only handling-policy gate; does not access NAS or inspect content."""
from dataclasses import dataclass
from enum import Enum

class Action(str, Enum):
    LIST = "LIST"
    READ = "READ"
    CHANGE = "CHANGE"
    TRANSFER = "TRANSFER"

class Result(str, Enum):
    ELIGIBLE_FOR_ADAPTER_CHECK = "ELIGIBLE_FOR_ADAPTER_CHECK"
    BLOCKED = "BLOCKED"
    NOT_CHECKED = "NOT_CHECKED"

@dataclass(frozen=True)
class Policy:
    folder_selected: bool = False
    authorized_metadata_read: bool = False
    authorized_document_read: bool = False
    official_adapter_validated: bool = False

@dataclass(frozen=True)
class PolicyAssessment:
    decision: Result
    reason: str
    sensitive_content_check: str = "NOT_CHECKED"
    actual_tool_call_performed: bool = False

def assess(action: Action, policy: Policy) -> PolicyAssessment:
    """Eligibility is not permission to execute an SDK command or proof of safety."""
    action = Action(action)
    if action in (Action.CHANGE, Action.TRANSFER):
        return PolicyAssessment(Result.BLOCKED, "Read-only design; not a permitted operation")
    if not policy.folder_selected or not policy.authorized_metadata_read:
        return PolicyAssessment(Result.BLOCKED, "Explicit folder and read authorization required")
    if action == Action.READ and not policy.authorized_document_read:
        return PolicyAssessment(Result.BLOCKED, "Document content requires separate authorization")
    if not policy.official_adapter_validated:
        return PolicyAssessment(Result.NOT_CHECKED, "Official implementation still unverified")
    return PolicyAssessment(Result.ELIGIBLE_FOR_ADAPTER_CHECK,
                            "Policy conditions met only; SDK and content safety not proven")
