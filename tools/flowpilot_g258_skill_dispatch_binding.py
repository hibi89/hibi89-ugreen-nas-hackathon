"""G258 exact-current-Skill stage/consent/catalog gate, NO Uliya runtime.

G257 used an old G256 source receipt without opening the present Skill. Here
we bind the real archived bytes to both guarded delegate examples and to the
pinned public read-only Kit catalog. This does NOT verify registration, runtime
signatures, permissions, vendor Creator, NAS, or actual source ownership.
"""
from __future__ import annotations

import hashlib
import io
import re
import stat
import zipfile

from sdk_parameter_matrix import matrix
from sdk_semantic_index import EXPECTED_SHA256 as KIT_SHA
from inspect_official_sdk import UnsafePackage

SCHEMA = "flowpilot-g258-exact-skill-runtime-policy-v1"
G226_SHA = "fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803"
FILES = frozenset({
    "flowpilot-3/SKILL.md",
    "flowpilot-3/references/failure-and-disclosure.md",
    "flowpilot-3/references/modes-and-evidence.md",
    "flowpilot-3/references/workflow-council-and-repair.md",
})
MODES = ("CHECK_DELIVERY","REVIEW_VERSIONS","REVIEW_DOCUMENT",
         "DESIGN_WORKFLOW","PLAN_ONLY")
EXPECTED_ACTIONS = {
    "ug-filesystem": ("file-agent",("ls","find","stat","sha256sum")),
    "ug-document": ("document-agent",("metadata","qa","extract","reconcile")),
}
EXAMPLE = re.compile(r"\x60delegate --target ([a-z][a-z-]{0,31}) --instruction '([^\x60]+)'\x60")


class SkillBoundaryRefused(ValueError):
    pass


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def verify_current_skill(candidate: bytes, kit: bytes, *,
                         skill_pin: str = G226_SHA, kit_pin: str = KIT_SHA,
                         synthetic_only: bool = False) -> dict:
    if (type(candidate) is not bytes or type(kit) is not bytes or
            not 0 < len(candidate) <= 1_000_000 or
            not 0 < len(kit) <= 500_000):
        raise SkillBoundaryRefused("UNBOUNDED_OR_MISSING_BYTES")
    if not synthetic_only and (skill_pin != G226_SHA or kit_pin != KIT_SHA):
        raise SkillBoundaryRefused("UNTRUSTED_OFFICIAL_DIGEST_OVERRIDE")
    if digest(candidate)!=skill_pin or digest(kit)!=kit_pin:
        raise SkillBoundaryRefused("CURRENT_SKILL_OR_KIT_CHANGED")
    try:
        with zipfile.ZipFile(io.BytesIO(candidate)) as z:
            entries=z.infolist()
            if (len(entries)!=4 or {e.filename for e in entries}!=FILES or
                    z.testzip() is not None or
                    any(e.file_size>1_000_000 or e.is_dir() or
                        stat.S_ISLNK(e.external_attr >> 16) for e in entries)):
                raise SkillBoundaryRefused("UNEXPECTED_MARKDOWN_CONTENTS")
            docs={name:z.read(name).decode("utf-8") for name in FILES}
    except (zipfile.BadZipFile,KeyError,UnicodeError,OSError,RuntimeError) as ex:
        raise SkillBoundaryRefused("BAD_SKILL_ZIP") from ex
    main=docs["flowpilot-3/SKILL.md"]
    council=docs["flowpilot-3/references/workflow-council-and-repair.md"]
    if any("".join([chr(96)]*3) in value or
           "http://" in value or "https://" in value for value in docs.values()):
        raise SkillBoundaryRefused("UNAPPROVED_EXECUTABLE_OR_REMOTE_INSTRUCTION")
    if (not main.startswith("---\nname: flowpilot-3\ndescription:") or
            any("# "+h not in main for h in
                ("Goal","Required input","Orchestration","Completion and failure")) or
            any(mode not in main for mode in MODES) or
            any(name.removeprefix("flowpilot-3/") not in main
                for name in FILES if name!="flowpilot-3/SKILL.md") or
            any(role not in council for role in ("Architect","Security","Builder","QA")) or
            "Maximum one bounded correction" not in council):
        raise SkillBoundaryRefused("CURRENT_SKILL_DESIGN_DRIFT")
    commands=EXAMPLE.findall(main)
    if (len(commands)!=2 or main.count("delegate --target ")!=2 or
            [x[0] for x in commands]!=["file-agent","document-agent"]):
        raise SkillBoundaryRefused("UNSUPPORTED_DELEGATED_AGENT_OR_COUNT")
    a,b=commands[0][1],commands[1][1]
    if (any(not 10<len(x)<=2048 or "'" in x or
            any(ord(ch)<32 or ord(ch)==127 for ch in x) for x in (a,b)) or
            "current-session owner metadata approval" not in a or
            "without following symlinks" not in a or
            "real document references" not in b or
            "separate explicit owner consent for each reference" not in b or
            "Do not search other files" not in b):
        raise SkillBoundaryRefused("DELEGATE_CONSENT_QUOTE_OR_NO_FOLLOW_MISSING")
    fst=main.find("delegate --target file-agent")
    snd=main.find("delegate --target document-agent")
    if (not 0<=main.find("PLAN_ONLY / NOT_CHECKED")<fst<snd or
            not 0<=main.find("DESIGN_ONLY / NOT_EXECUTED")<fst or
            not 0<=main.find("owner separately approves content access")<snd or
            not 0<=main.find("exact document references")<snd):
        raise SkillBoundaryRefused("PLAN_ONLY_OR_DOCUMENT_UPSTREAM_GATE_MISSING")
    for state in ("completed","failed","cancelled","waiting_user","waiting_approval"):
        if "- "+chr(96)+state+chr(96)+":" not in main:
            raise SkillBoundaryRefused("DELEGATE_FAILURE_STATE_NOT_HANDLED")
    try:
        catalog=matrix(kit,kit_pin)
    except (UnsafePackage,ValueError,TypeError,KeyError) as exc:
        raise SkillBoundaryRefused("PINNED_KIT_CATALOG_REFUSED") from exc
    rows={(row["cli"],row["action"]):row for row in catalog["actions"]}
    if len(rows)!=len(catalog["actions"]):
        raise SkillBoundaryRefused("DUPLICATE_ACTION_LABEL")
    for cli,(agent,actions) in EXPECTED_ACTIONS.items():
        for action in actions:
            entry=rows.get((cli,action))
            if (not entry or entry.get("agent_label")!=
                    ("fake-agent" if synthetic_only else agent) or
                    entry.get("effect")!={"kind":"scalar","value":"read"} or
                    entry.get("approval")!={"kind":"scalar","value":"none"} or
                    entry.get("permissions",{}).get("knowledge_status")!="unknown" or
                    chr(96)+action+chr(96) not in main):
                raise SkillBoundaryRefused("UNAPPROVED_OR_UNKNOWN_SKILL_ACTION")
    return {
        "schema":SCHEMA,
        "status":("SYNTHETIC_DISPATCH_POLICY_ONLY" if synthetic_only else
                  "EXACT_G226_SKILL_TO_CATALOG_RECHECKED_NOT_NAS"),
        "candidate_sha256":skill_pin,
        "kit_sha256":kit_pin,
        "registered_expert_targets_claimed_only":["file-agent","document-agent"],
        "guarded_instruction_sha256":[digest(x.encode("utf-8")) for x in (a,b)],
        "read_only_catalog_actions_rechecked":8,
        "new_consent_for_document_required":True,
        "plan_only_never_dispatches":True,
        "real_registered_expert_verified":False,
        "effective_permissions_verified":False,
        "native_response_verified":False,
        "executable_command_generated":False,
        "official_creator_verified":False,
        "nas_verified":False,
        "release_gate":"HOLD",
    }
