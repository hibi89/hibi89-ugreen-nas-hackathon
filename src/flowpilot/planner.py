"""NAS FlowPilot offline natural-language-to-plan MVP.

No Uliya/NAS SDK, filesystem, network, model, or expert is called.
A READY_FOR_ADAPTER_CHECK result is a proposed plan, never a NAS result.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
import re
import unicodedata


class State(str, Enum):
    WAITING_USER = "WAITING_USER"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    READY_FOR_ADAPTER_CHECK = "READY_FOR_ADAPTER_CHECK"


class Intent(str, Enum):
    HANDOFF_AUDIT = "HANDOFF_AUDIT"
    CHECK_REQUIRED = "CHECK_REQUIRED"
    REVIEW_VERSIONS = "REVIEW_VERSIONS"
    SUMMARIZE_SELECTED = "SUMMARIZE_SELECTED"


@dataclass(frozen=True)
class Step:
    id: str
    expert: str
    purpose: str
    requires_runtime_verification: bool = True


@dataclass(frozen=True)
class Plan:
    state: State
    intent: Intent | None
    authorized_root: str
    required_paths: tuple[str, ...]
    steps: tuple[Step, ...]
    questions: tuple[str, ...]
    limitations: tuple[str, ...]
    did_access_nas: bool = False


_RESTRICTED = re.compile(
    r"(^|[._-])(env|ssh|git|token|tokens|secret|secrets|password|passwords|credential|credentials|private[._-]?key|api[._-]?key|access[._-]?key|service[._-]?account|session|sessions|auth)([._-]|$)"
    r"|(^|[.])(pem|p12|pfx|key|kdbx|asc|gpg)$"
    r"|^(config[.]json|id_rsa|id_ed25519|authorized_keys|known_hosts|[.]npmrc|[.]netrc|[.]aws|[.]kube|[.]gnupg|[.]docker)$", re.IGNORECASE
)
_WRITES = re.compile(
    # Inflected mutating/transfer verbs must fail closed, not just bare
    # imperatives. The word boundaries avoid matching unrelated substrings.
    r"\b(?:delet(?:e|es|ed|ing)|remov(?:e|es|ed|ing|al)|renam(?:e|es|ed|ing)|"
    r"mov(?:e|es|ed|ing)|upload(?:s|ed|ing)?|transfer(?:s|red|ring)?|"
    r"send(?:s|ing)?|sent|overwrit(?:e|es|ing|ten)|wip(?:e|es|ed|ing)|"
    r"modif(?:y|ies|ied|ying)|cop(?:y|ies|ied|ying)|shar(?:e|es|ed|ing)|"
    r"publish(?:es|ed|ing)?|export(?:s|ed|ing)?|edit(?:s|ed|ing)?|"
    r"eras(?:e|es|ed|ing)|download(?:s|ed|ing)?|"
    r"synchroniz(?:e|es|ed|ing)|synchronis(?:e|es|ed|ing)|"
    r"sync(?:s|ed|ing)?|email(?:s|ed|ing)?|forward(?:s|ed|ing)?|"
    r"attach(?:es|ed|ing)?)\b"
    r"|(?:삭제|이동|업로드|전송|수정|덮어쓰기|복사|공유|지워|지우|지웠|지웁|"
    r"옮기|옮겨|옮겼|지우기|보내|내보내기|게시|발행|다운로드|내려받|동기화|첨부해|"
    r"저장해|이름\s*바꿔)", re.IGNORECASE
)


def _safe(value: str, *, root: bool) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Missing or noncanonical path")
    if unicodedata.normalize("NFKC", value) != value:
        raise ValueError("Noncanonical Unicode path")
    if ":" in value or "%" in value or "\\" in value or any(ord(x) < 32 or ord(x) == 127 or unicodedata.category(x) == "Cf" for x in value):
        raise ValueError("Control or alternate path separator")
    if root:
        if not value.startswith("/") or value == "/" or value.startswith("//"):
            raise ValueError("An explicit scoped POSIX root is required")
        parts = value[1:].split("/")
    else:
        if value.startswith("/") or value.startswith("~"):
            raise ValueError("Checklist paths must be relative")
        parts = value.split("/")
    if any(p in ("", ".", "..") or p.endswith(" ") or p.endswith(".") for p in parts):
        raise ValueError("Ambiguous or escaping path")
    if any(_RESTRICTED.search(p) for p in parts):
        raise ValueError("Restricted target; do not enumerate or disclose")
    return value


def _intent(request: str) -> Intent | None:
    r = request.casefold()
    # Explicit task verbs take precedence over nouns in selected filenames.
    # E.g. "summarize handoff/summary.md" is a content-read request, NOT
    # a handoff audit; planning it as an audit could bypass document consent.
    # Keep the established general "check project handoff deliverables" audit
    # interpretation, unless a more specific action was requested.
    # A file name such as handoff/summarize.md is NOT a summary command.
    # Treat an English verb as standalone only, excluding path separators,
    # extensions and compound names. Korean imperatives are recognized even
    # with polite/inflected endings, but not when immediately in a path/name.
    if (re.search(r"(?<![\w/_.-])summari[sz]e(?![\w/_.-])", r)
            or re.search(r"(?<![/_.-])요약(?:해|하|할)", r)):
        return Intent.SUMMARIZE_SELECTED
    if any(s in r for s in ("compare version", "review version", "버전 비교", "버전들을 비교")):
        return Intent.REVIEW_VERSIONS
    if any(s in r for s in ("check required", "check missing", "필수 파일 확인", "누락 파일 확인")):
        return Intent.CHECK_REQUIRED
    if any(s in r for s in ("handoff", "deliverable", "납품", "인계", "프로젝트 준비")):
        return Intent.HANDOFF_AUDIT
    if any(s in r for s in ("version", "compare", "conflict", "버전", "최종본", "비교")):
        return Intent.REVIEW_VERSIONS
    if any(s in r for s in ("summarize", "summary", "document", "요약", "문서")):
        return Intent.SUMMARIZE_SELECTED
    if any(s in r for s in ("check", "missing", "file", "확인", "누락", "파일")):
        return Intent.CHECK_REQUIRED
    return None


def draft_plan(
    request: str,
    root: str = "",
    required_paths: Sequence[str] = (),
    *,
    metadata_approved: bool = False,
    unknown_processing_accepted: bool = False,
    document_approved: bool = False,
    returned_document_refs: Sequence[str] = (),
) -> Plan:
    """Draft one bounded read-only flow, without pretending runtime support.

    The caller's booleans are *claims*, not proof of consent or NAS permissions.
    Registered-agent checks and actual expert results remain mandatory.
    """
    questions: list[str] = []
    limitations = ["OFFLINE_PLANNER_ONLY", "LIVE_AGENT_AND_PERMISSIONS_NOT_VERIFIED"]
    if not isinstance(request, str) or not request.strip():
        return Plan(State.WAITING_USER, None, "", (), (), ("What NAS handoff/check/version/document task?",), tuple(limitations))
    if _WRITES.search(request):
        return Plan(State.BLOCKED, None, "", (), (), (), ("Mutating or external-transfer requests are outside the contest read-only MVP",))
    intent = _intent(request)
    if intent is None:
        return Plan(State.WAITING_USER, None, "", (), (), ("Choose handoff audit, required-file check, version review, or selected-document summary.",), tuple(limitations))
    if not root:
        questions.append("Which exact owner-authorized NAS folder?")
    if not required_paths:
        questions.append("Which exact mandatory relative file paths?")
    if questions:
        return Plan(State.WAITING_USER, intent, "", (), (), tuple(questions), tuple(limitations))
    root = _safe(root, root=True)
    paths = tuple(_safe(path, root=False) for path in required_paths)
    if len(set(paths)) != len(paths) or len(paths) > 100:
        raise ValueError("Duplicate or excessive required paths")
    # Dataclass/type annotations do not enforce input booleans. A nonempty
    # string or integer is not owner approval.
    if metadata_approved is not True:
        questions.append("Approve read-only metadata access to this exact folder?")
    if unknown_processing_accepted is not True:
        questions.append("Processing location is unverified; continue with scoped metadata only?")
    if questions:
        return Plan(State.WAITING_APPROVAL, intent, root, paths, (), tuple(questions), tuple(limitations))
    steps = [Step("inventory", "file-agent", "List/find/stat only for approved root and checklist; require complete pagination and attributable source refs")]
    if intent in (Intent.HANDOFF_AUDIT, Intent.REVIEW_VERSIONS):
        steps.append(Step("versions", "file-agent", "Compare only scoped candidate names; do not automatically choose latest"))
    if intent == Intent.SUMMARIZE_SELECTED:
        if document_approved is True and returned_document_refs:
            if any(not isinstance(ref, str) or not ref.strip() for ref in returned_document_refs):
                raise ValueError("Invalid returned document reference")
            steps.append(Step("document", "document-agent", "Only exact verified returned references, separately approved; never widen scope"))
        else:
            limitations.append("DOCUMENT_STAGE_WAITING_SEPARATE_APPROVAL_AND_REAL_FILE_REFS")
            questions.append("After file-agent returns exact references, separately approve selected content and the question.")
    steps.append(Step("report", "parent-skill", "Evidence-linked PRESENT/MISSING/NOT_CHECKED/VERSION_REVIEW; no optimistic READY"))
    return Plan(State.READY_FOR_ADAPTER_CHECK, intent, root, paths, tuple(steps), tuple(questions), tuple(limitations))
