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

## Real-input delegation procedure (no sample commands)

For each real request, build a complete self-contained expert instruction using
only owner-supplied, currently validated and authorized data. No expert is assumed
to see the parent conversation.

1. The file-agent instruction must inject the exact approved folder and each
   required relative path, every approved version-candidate pattern and the
   requirement it represents. Restrict work to read-only ls/find/stat within
   that folder; prohibit symlinks, content reads, mutations and other folders.
   Require attributable file references, scan completeness/truncation, errors,
   permission status and stop conditions. Incomplete or denied scans yield
   NOT_CHECKED, never MISSING; absent approval or required input yields
   waiting_user rather than a delegation.
2. The document-agent instruction must inject only the exact in-scope references
   actually returned by file-agent and separately approved for document reading,
   plus the owner's actual question verbatim. Bind an approved file to file and
   the actual question to query only when supported by the catalog action.
   Restrict to declared metadata/qa/extract/reconcile read operations; prohibit
   independent discovery, mutations and guesses about authoritative versions.
   Require attributable evidence for each referenced document or version
   candidate, coverage, permission state and errors. Missing reference,
   separate approval, actual question or supported argument mapping yields
   waiting_user, not a broadened fallback.

The catalog alone does not establish the actual delegation CLI syntax, live
agent registration, effective permissions or processing location. If any are
required but unverified, stop and report NOT_CHECKED.

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
