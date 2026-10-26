---
name: projectready-nas
description: Read-only evidence review of owner-authorized project delivery folders; use when an owner needs required-file readiness and version uncertainty checks.
---

# Goal

ProjectReady NAS compares one owner-authorized delivery folder with an owner-provided mandatory-file checklist. It reports per-item `PRESENT`, `MISSING`, `NOT_CHECKED`, or `VERSION_REVIEW`, and an overall `READY`, `BLOCKED`, or `NEEDS_REVIEW` only when the evidence supports that result. It does not modify files or certify NAS privacy or security.

# Required input

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

## Required delegation payload construction

Before a real delegation, build the complete instruction from validated, owner-approved values. Do not rely on the expert seeing the parent conversation. Never send phrases such as “supplied in this request,” “returned by the previous step,” “the files above,” or unresolved placeholders in place of actual values.

- For `file-agent`, include the exact approved folder path, every exact mandatory relative path, every owner-defined candidate version pattern and its intended requirement, and the read-only limits. Confirm every path and pattern remains within the approved folder. If a value or the required authorization is missing, do not delegate; ask only for the missing owner input and classify the check as `NOT_CHECKED` until supplied.
- For `document-agent`, include the exact in-scope file references actually returned by `file-agent`, the exact version-candidate references to compare, the explicit owner approval covering each reference, and the owner question verbatim. Include only nonsensitive values. If the question or any reference includes restricted material, redact it and request a safe replacement instead of forwarding it.
- Keep each child instruction self-contained: scope, exact inputs, permitted action, prohibited actions, output evidence, completeness and error reporting, and stop conditions must all be present in that instruction. If the supported action cannot accept the approved references or question, stop rather than widening scope or changing the question.

## Standard agent delegation (runtime-constructed, scope-checked)

**G32 shell-quoting and mandatory binding:** The two single-quoted `delegate` commands below are *inert refusal examples for the vendor-required command grammar*, not complete live instructions. They must not be executed as the actual file/document review. For a real delegation, first construct the complete owner-approved instruction containing exact in-scope path(s), checklist/patterns, returned references, scope limits, consent and stop conditions. Replace the **whole** example's quoted instruction with that complete text. Where POSIX shell quoting is supported, enclose the fully rendered text in single quotes and escape every internal apostrophe by ending the quoted span, inserting an escaped apostrophe, and reopening the span. Never place `$FILE_AGENT_INSTRUCTION` or `$DOCUMENT_AGENT_INSTRUCTION` inside single quotes expecting shell expansion. Do not use `eval`; if runtime quoting/dispatch is unverified, stop as `NOT_CHECKED`.

Both expert agents are required for their respective stages: `file-agent` for
file/checklist evidence, and, **only after separate owner approval of specific
returned document references**, `document-agent` for optional content review.
These are ordinary Uliya catalog mappings; their existence does not prove live
registration, actual permission grants, or a specific execution environment.

**Mandatory pre-dispatch binding.** Build a fresh, complete instruction for each
call; the agent does not automatically inherit the parent's context. The names
`FILE_AGENT_INSTRUCTION` and `DOCUMENT_AGENT_INSTRUCTION` below represent
transient, fully rendered instruction strings in the parent orchestrator, **not**
text or environment variables that can be sent to the expert as-is. First
materialize all approved scope values into the instruction. The final standard
`--instruction` argument must contain those actual values literally, quoted
as a single argument. Never transmit either symbolic name, an unresolved
variable, any invented path, or demo inputs; if exact rendering or the runtime
standard delegate interface cannot be confirmed, stop at `waiting_user` or
`NOT_CHECKED` without attempting any NAS access.

1. Before invoking the file expert, assemble `FILE_AGENT_INSTRUCTION` with the
   owner's explicit folder permission, exact approved folder, each mandatory
   relative path, every approved candidate pattern and its required item,
   and the read-only bounds. Prohibit parent-child folder escapes, symlink
   traversal, content reads, writes and all other directories. Require a
   complete/truncated listing indication, attributable file references,
   effective permission state and errors. If approval, scope, or instruction
   assembly is incomplete, do **not** delegate; return `waiting_user` and
   `NOT_CHECKED`. Only after the complete string exists, render the approved full instruction
   in the following canonical syntax, replacing the inert refusal text:

   `delegate --target file-agent --instruction 'No owner-approved folder, checklist, or version patterns are included in this syntax-only example. Do not access NAS data. Return NOT_CHECKED.'`

2. Before invoking the document expert, require **new, separate consent** for
   every exact file/document candidate reference returned by the first expert,
   plus the owner's exact document question. Assemble the complete
   `DOCUMENT_AGENT_INSTRUCTION` with the approved folder, those exact returned
   references and version candidates, owner question verbatim, supported
   `ug-document` read actions only, result evidence requirements, permission
   reporting, and no independent discovery/write/final-version guessing. Use
   the actual supported `file` and `query` parameter mappings if required by
   the selected catalog action. If any actual value or separate approval is
   missing or the input cannot be preserved exactly, do not delegate. Once
   fully bound, render the owner-approved full instruction in the same
   canonical syntax, replacing the inert refusal text:

   `delegate --target document-agent --instruction 'No separately owner-approved exact document references or question are included in this syntax-only example. Do not read documents. Return CONTENT_NOT_CHECKED.'`

**Execution safety:** The displayed command forms document the intended
standard dispatch syntax and must be fully rendered before execution, not run
literally in a shell. No expert request may contain `$FILE_AGENT_INSTRUCTION`,
`$DOCUMENT_AGENT_INSTRUCTION`, symbolic slot names, placeholder paths, or any
unapproved references. Do not execute either command without a supported
runtime dispatcher, approved folder scope, and the verified prerequisite
result/consent. If the available runtime does not expose the catalog-declared
agents or command contract, report `NOT_CHECKED` and do not invent a fallback.

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

Handle every expert delegation state explicitly:

- `completed`: report only business results supported by the returned evidence. If the result is partial, classify unresolved items as `NOT_CHECKED`.
- `failed`: stop dependent work and report the failure without fabricating a fallback.
- `cancelled`: report that the review was cancelled; do not present partial output as completion.
- `waiting_user`: ask only for the missing scope, checklist, or required approval.
- `waiting_approval`: wait for the approval result; do not treat the request itself as approval.

Never describe a missing or empty response as a successful scan. Do not infer NAS execution from local authoring or static checking.

# Safety

This is an independent ProjectReady NAS Skill concept, not a UGREEN-provided or UGREEN-certified product. Do not write, rename, move, delete, copy, tag, upload, or externally share user files. Do not access credentials or other private data. Never call the workflow a privacy certification or claim that Uliya processing is local. If the actual expert, permission, result, or data-flow condition cannot be verified, stop the dependent step and report `NOT_CHECKED` or `NEEDS_REVIEW`.
# Development provenance and third-party disclosures

- **New hackathon functionality:** Original entrant-directed read-only ProjectReady NAS orchestration: owner-scoped file checklists, conservative evidence states, uncertain-version review, delegated NAS file/document experts, and fail-closed readiness reports.
- **AI development tools:** OpenAI ChatGPT (GPT-6) assisted workflow design, safety policies, offline review and drafting. OpenAI Codex, using the official UGREEN Uliya Skill Creation Tool, generated the initial Skill and assisted a subsequent reviewed update. The human entrant directs and must approve the final submission.
- **Third-party platform and licenses:** The planned platform dependency is the official UGREEN UGOS/Uliya Skill Kit, published at https://ai.ugreen.com/pages/hackathon-starter-kit . No UGREEN SDK source, executable, additional third-party code library or AI model weights are bundled in this Markdown-only package. Applicable UGREEN tool/service license rights are still pending entrant verification; this preview is not authorized for publication.
- **Data and external services:** Future operations require explicit per-folder permission and separately approved document references. No customer NAS information was accessed during drafting. No independent outbound integration is intentionally configured. Whether Uliya model processing happens locally or in a cloud service is unverified and must not be advertised as local-only.
- **Validation and ownership limits:** The previous disclosure-augmented G22 Skill (SHA-256 770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169) passed the official static checker in a participant-reported Codex run with zero errors, warnings and information messages. That result applies only to the exact G22 SHA. Validation of a later revision requires its own file SHA and separate official checker evidence; never infer a pass. Actual NAS runtime, registered Agent permissions, contents privacy and the entrant's original-work/licensing approval remain unverified. This is a DRAFT, not UGREEN certification or a Devpost submission.
