---
name: flowpilot-nas
description: Use when a NAS project owner needs a conversational, read-only handoff audit, exact required-file check, competing-version review, or separately approved selected-document summary through verified Uliya registered experts.
---

# Goal

NAS FlowPilot converts one owner-initiated, natural-language NAS project task into a **previewed, conditional, read-only expert plan**. The four bounded variants are HANDOFF_AUDIT, CHECK_REQUIRED, REVIEW_VERSIONS and SUMMARIZE_SELECTED. It asks only for the missing inputs, presents the chosen steps and consent gates, delegates only to verified registered experts for the exact owner-selected folder, then reports attributable evidence. It never silently runs a general workflow graph, schedules future jobs, changes files, accesses SaaS apps or claims local processing.

The evidence states are `PRESENT`, `MISSING`, `NOT_CHECKED` and `VERSION_REVIEW`; optional document reviews can return `CONTENT_NOT_CHECKED`. Overall status may be `BLOCKED` or `NEEDS_REVIEW`; `READY` needs authoritative, fully supported runtime evidence that is **not provided by this offline candidate**.

# Required input

- Owner's natural-language goal, narrowed to one supported intent: handoff review, exact required-file check, version review, or separately authorized selected-document question.
- One exact delivery folder chosen by the owner.
- The exact required relative file paths and any owner-defined candidate patterns.
- Explicit permission to use Uliya read-only expert agents for this folder.
- Separate explicit approval before reviewing the contents of any document, with the exact file references selected.

The public catalog does not establish whether Uliya processes data locally or remotely. Before any delegation, explain that this is unknown and ask whether the owner still authorizes the requested scoped review. If the owner requires verified local-only processing, stop without delegating. Do not access any NAS data without this authorization.

Before delegation, screen the folder and checklist for restricted targets such as `.env`, `.git`, `config.json`, private keys, certificates, SSH credentials, browser sessions, or authentication tokens. Do not probe restricted targets. Mark them `NOT_CHECKED (restricted)` and display only `[restricted item]`; do not include their names in a delegation or report. If a restricted name appears incidentally in a listing, do not read or repeat it. Never count an excluded item as absent.

# Generation-time capability evidence

The local official Uliya Skill Kit v0.7.3-en catalog declares these unique CLI-to-expert mappings. This is catalog-level support evidence only; it does not prove live registration, effective permissions, completeness reporting, or data-processing location.

- `ug-filesystem` → `file-agent`
- `ug-document` → `document-agent`

The catalog declares `ug-filesystem ls`, `find`, `stat`, and `sha256sum` as `effect=read` with `approval=none`. `ls` and `find` require `path`; the optional `limit` value does not prove complete or paginated results. The catalog declares `ug-document metadata`, `qa`, `extract`, and `reconcile` as read actions with `approval=none`. For all selected actions, `permissions.knowledgeStatus` is `unknown`. Do not claim a permission, complete scan, or supported return field unless the actual expert result establishes it.

# Orchestration

The parent Skill only delegates NAS work to the catalog-mapped experts. Do not directly call `cli.invoke` from the parent Skill. The second delegation must use only the real references and business results returned by the first delegation; it must not independently discover or invent inputs.

## Intent-based workflow selection

After the owner supplies a supported task, exact folder, exact checklist and metadata approval, show the **dynamic plan** before dispatch. HANDOFF_AUDIT includes owner-scoped inventory, competing version grouping and cited handoff report. CHECK_REQUIRED performs owner-scoped inventory and required-item report only. REVIEW_VERSIONS performs inventory, candidate grouping and review report but never chooses a final. SUMMARIZE_SELECTED first obtains independently verified scoped file references; the optional document expert only follows separately approved exact references and the owner's verbatim question. All variants stop when a permission, registered expert, return schema, privacy processing location, completeness flag or scope is not sufficiently established. If the goal falls outside the four intents, return `waiting_user` without inventing a DAG or command.

No plan is executed by the offline Python planner; that code exists only in development and is NOT bundled in the submission ZIP. All real calls must be authorized at runtime by Uliya. 


## Required delegation payload construction

Before a real delegation, build the complete instruction from validated, owner-approved values. Do not rely on the expert seeing the parent conversation. Never send phrases such as “supplied in this request,” “returned by the previous step,” “the files above,” or unresolved placeholders in place of actual values.

- For `file-agent`, include the exact approved folder path, every exact mandatory relative path, every owner-defined candidate version pattern and its intended requirement, and the read-only limits. Confirm every path and pattern remains within the approved folder. If a value or the required authorization is missing, do not delegate; ask only for the missing owner input and classify the check as `NOT_CHECKED` until supplied.
- For `document-agent`, include the exact in-scope file references actually returned by `file-agent`, the exact version-candidate references to compare, the explicit owner approval covering each reference, and the owner question verbatim. Include only nonsensitive values. If the question or any reference includes restricted material, redact it and request a safe replacement instead of forwarding it.
- Keep each child instruction self-contained: scope, exact inputs, permitted action, prohibited actions, output evidence, completeness and error reporting, and stop conditions must all be present in that instruction. If the supported action cannot accept the approved references or question, stop rather than widening scope or changing the question.

## Functional guarded delegation

This is a dynamic, owner-scoped read-only workflow, not a hardcoded NAS
demo. The parent cannot assume a child expert sees its conversation,
permissions, folder choices, file references, version patterns or questions.
**Before dispatch**, the parent must embed the complete real authorization
data **inside the same child instruction string** as the fixed task below:
the exact approved folder, explicit owner consent, every mandatory relative
file path, associated owner-approved candidate patterns, and all permitted
read bounds. For document review it must additionally bind the exact returned
file-agent references, separate consent per document and the verbatim question.
Do not delegate if any value is absent, restricted or ambiguously bound.
Never send symbolic names or unresolved placeholders to the experts.

The following two registered-expert invocations contain operational
**guarded tasks**, not syntax-only dummy commands. The first action
inside each task is the **required validation of actual bound inputs**.
The parent adds real approved values to the **same final single-quoted
instruction argument before runtime execution**, not in a separate chat turn.
The parent must verify that the installed dispatcher supports this command
contract and robustly escape internal apostrophes for its actual shell.
Never use `eval`, interpolate unresolved variables or fabricate NAS values.
If the dispatcher, effective permissions or processing location is unknown,
do not invoke and report `NOT_CHECKED` with a reason.

**Required stage 1: read-only file evidence.** After constructing the full
child instruction containing the exact approved scope and complete checklist,
dispatch only through the verified registered `file-agent`:

`delegate --target file-agent --instruction 'Verify that this exact instruction includes explicit owner authorization, the precise authorized folder, every required relative path and all candidate patterns tied to their required item. If any scope, permission, or checklist detail is absent, access nothing and return waiting_user and NOT_CHECKED. With complete bound approval, call only registered read-only ug-filesystem ls, find, and stat inside the approved folder. Do not follow symlinks, traverse parents, read contents, inspect credentials or other directories, change files, or disclose them externally. For every required item report attributable returned file references and competing versions. Include effective permissions, enumeration completeness or truncation, unsupported operations and errors. A missing required item can be MISSING only after positively verified complete authorized enumeration; all other gaps are NOT_CHECKED. Stop on unclear ownership, access scope, or runtime capability.'`

The bound and approved folder, checklist, candidate patterns and owner
authorization **must be inserted into this same one-argument task before
the call**. The guard legitimately refuses without them; a refusal is
not a scan result. Do not send the unbound printed form as an attempt
to obtain file evidence. Failed, incomplete, empty, cancelled and
truncated results do not establish absence; escalate `NEEDS_REVIEW`.

**Optional stage 2: separately consented document evidence.** Only after
the first expert returns real attributable references and the owner separately
approves reading particular selected documents, construct the second
self-contained task including exact approved references, approved folder,
verbatim owner question and independent per-reference consent. Invoke only
the verified registered `document-agent`:

`delegate --target document-agent --instruction 'Before reading any document, verify this exact instruction includes the approved folder, actual attributable document references returned by the file expert, explicit separate owner consent for each reference and the verbatim owner question. If any authorization, permission, exact reference or question is absent, read nothing and return waiting_user and CONTENT_NOT_CHECKED. With complete bound inputs only, use authorized read-only ug-document metadata, qa, extract or reconcile actions and supported file and query mappings on exactly those references. Do not search other documents, widen the scope, write data, reveal restricted items or guess a final version. Report evidence per exact reference, effective permission state, coverage, errors, any uncertainty and the actual answered question. Stop if supported invocation or processing location is unverifiable.'`

Insert the real approved file references, exact owner question and consent
**in the same final instruction string** before dispatch. If file-agent
did not return real references or approval is incomplete, skip this stage,
report `CONTENT_NOT_CHECKED`, and keep overall `NEEDS_REVIEW`. The
public catalog cannot prove live expert registration, current permissions,
a supported delegate interface or where model data is processed. Refuse
to substitute another Agent or to invent results.

If the first expert returns no results, say that no results were returned and stop; do not widen the scope or substitute similar files. If it returns a partial listing, do not treat unobserved paths as missing. Skip the document delegation if there are no exact references or separate content approval.

# Result classification

- `PRESENT`: an exact required path has an attributable reference in an authorized expert result.
- `MISSING`: an exact required path is absent from an authorized listing that the expert explicitly verifies is complete.
- `NOT_CHECKED`: the scan is partial, truncated, denied, unsupported, unverifiable, or otherwise lacks evidence for presence or absence.
- `VERSION_REVIEW`: multiple plausible candidates exist and the owner has not identified the authoritative version. Never select a final version from filename, date, size, or hash alone.
- `CONTENT_NOT_CHECKED`: document contents were not separately approved or the approved review did not return verifiable evidence.

A confirmed missing mandatory item makes the overall result `BLOCKED`. Use `NEEDS_REVIEW` for unresolved permissions, privacy, completeness, content, or version questions. Use `READY` only when every mandatory item is evidenced as present and all required completeness, authorization, privacy, and version checks have actual supported evidence. Catalog declarations alone cannot establish `READY`.

Report each non-restricted requirement with its status, actual reference, limitation, and next owner action. Redact restricted details as `[restricted item]`. Keep file names and document content to the minimum needed for the owner’s checklist.

# Completion and failure

**Empty result handling:** A registered expert returning zero files, an empty payload, no attributable references or an unparseable/partial response is NOT a successful completed scan. Unless complete authorized enumeration is positively evidenced, return `NOT_CHECKED` and `NEEDS_REVIEW`, disclose the limitation, and do not widen the search. Empty results cannot prove a missing file without the required completeness proof.

Handle every expert delegation state explicitly:

- `completed`: report only business results supported by the returned evidence. If the result is partial, classify unresolved items as `NOT_CHECKED`.
- `failed`: stop dependent work and report the failure without fabricating a fallback.
- `cancelled`: report that the review was cancelled; do not present partial output as completion.
- `waiting_user`: ask only for the missing scope, checklist, or required approval.
- `waiting_approval`: wait for the approval result; do not treat the request itself as approval.

Never describe a missing or empty response as a successful scan. Do not infer NAS execution from local authoring or static checking.

# Safety

No writes, deletion, movement, upload, external transfer, scheduled execution, arbitrary tool calls, or general-purpose workflow runtime are permitted. The user must never infer that a preview plan is an execution result.

This is an independent NAS FlowPilot Skill concept, not a UGREEN-provided or UGREEN-certified product. Do not write, rename, move, delete, copy, tag, upload, or externally share user files. Do not access credentials or other private data. Never call the workflow a privacy certification or claim that Uliya processing is local. If the actual expert, permission, result, or data-flow condition cannot be verified, stop the dependent step and report `NOT_CHECKED` or `NEEDS_REVIEW`.
# Development provenance and third-party disclosures

- **Original entrant-led Skill candidate:** NAS FlowPilot is a conversational, conditional read-only handoff workflow. The four owner-goal variants select different registered expert stages rather than a general automation engine. The selected exact folder, permissions, checklist and returned references must be bound anew for every runtime delegation.
- **Tools and Creator status:** The participant directs this project. On 2026-10-28, this separate candidate was generated in Codex by following the genuine UGREEN UGOS Skill Creation Tool workflow from the installed official `uliya-skill-kit` v0.7.3-en: confirm the requested Skill name, goal, and target directory; verify catalog feasibility; then author the new `SKILL.md` using the Kit's guidance. The Kit is an assistant-guided creation Skill, not a standalone generation CLI; no generic OpenAI Skill Creator or synthetic Creator receipt was used. OpenAI ChatGPT GPT-6 assisted composition and review. Official static checking is a separate gate from Creator use and from running a NAS.
- **Third-party libraries:** The official UGREEN UGOS/Uliya Skill Kit v0.7.3-en is cited for documented registered Agent mapping, but no SDK files, executables or model weights are distributed with this Markdown Skill. A UGREEN support reply described MIT/Apache-2.0/BSD license choices for entrants' own submitted work and an accurate 'no third-party components redistributed' declaration when applicable; do not interpret that as transferring vendor rights or approving this release. Entrant approval remains required.
- **Data flow and safety:** No customer NAS folder has been accessed by authoring or testing. No external REST service, recurring automation, social connector or export is included. Local-versus-cloud processing in the actual platform and effective Agent permissions remain unknown. Never advertise NAS data as locally processed until verified.
- **Offline implementation boundary:** G64's bounded Korean/English text parser and sequential metadata workflow are Python development tools that operate on an explicitly approved local folder. They are not inside this Markdown Skill, do not invoke Uliya, and are not evidence of NAS or registered Expert execution.
- **Evidence boundaries:** Earlier ProjectReady G36 passed the first-party Uliya static checker on its different exact SHA; that result does **not** certify FlowPilot. This candidate's official Creator and exact-source Checker record is documented in `docs/submission/G58_OFFICIAL_FLOWPILOT_CREATOR_EXECUTION_20261028.md`; it is not proof of NAS runtime. Real official NAS execution, selected-document consent, privacy, user rights and Devpost submission remain NOT_VERIFIED or NOT_SUBMITTED.

