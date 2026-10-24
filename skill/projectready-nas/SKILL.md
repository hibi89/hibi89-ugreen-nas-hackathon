---
name: projectready-nas
description: Read-only evidence review of required delivery documents in a user-authorized NAS project folder.
---

# ProjectReady NAS

## When to use
Use when the owner asks whether a specific project-delivery folder contains an explicit checklist of required files, with version and permission uncertainties identified. This is a read-only review, not a privacy certification or NAS security scan.

## Scope and permission
1. Obtain the owner's exact folder and mandatory file checklist. Never invent required paths or infer access consent.
2. Limit all requests to that folder. Do not enumerate other folders or follow links outside scope. Before invoking any listing or document tool, reject an owner folder or checklist entry that targets `.env`, `.git`, `config.json`, private key/certificate/SSH credential files, browser sessions, authentication tokens or similar secrets. UGREEN publishing policy prohibits searching for or transmitting these sensitive materials even when a checklist includes them. Do NOT probe a restricted path to verify that it exists; redact restricted details in output and mark that required check NOT_CHECKED (restricted), requesting a nonsensitive replacement checklist. If incidental restricted file names appear in an otherwise authorized listing, do not read, expand, quote or report their names. Never count an excluded path as a verified absence.
3. The official public Uliya v0.7.3 capability catalog lists `file-agent` with `ug-filesystem` and `document-agent` with `ug-document` actions. Consult the [pinned catalog read-only action matrix](references/catalog-actions.md). This establishes only catalog declarations, NOT live Agent registration, actual command invocation or privileges. Before any call, verify the installed official runtime, permission and exact invocation instructions; permission knowledgeStatus is unknown. Do not invent Agent IDs, unsupported flags, command syntax or output fields. If unsupported, unavailable or unauthorized, report NOT_CHECKED and stop.

## Audit flow
1. Subject to actual installed Agent and owner-folder authorization, use the documented `ug-filesystem` read-action candidates `ls` (required `path`, optional `recursive`, `max-depth`, `limit`) and/or `find` (required `path`, optional `pattern`, `max-depth`, `limit`). Treat parameter names as catalog keys, NOT confirmed shell flags. Record actual returned paths and attributable references. A `limit` parameter does NOT establish pagination/completeness; partial, truncated or denied results cannot establish absence.
2. Compare every mandatory path exactly against returned files. An observed file with a source reference is PRESENT. Only a demonstrably complete authorized listing can establish MISSING; otherwise use NOT_CHECKED.
3. Identify candidate version conflicts when multiple similarly named files appear. Mark VERSION_REVIEW. Never select an approved final version solely from filename suffixes, date or size. Ask the owner for authoritative selection or verifiable content evidence.
4. After a separately authorized document-content review, and ONLY if the actual supported runtime provides it, use `ug-document qa` or `extract` with required `query` and the exact owner-selected `file` references (catalog: `file` repeatable, but not mandatory); `reconcile` may compare authorized selected files. `ug-document metadata` must likewise be restricted to explicitly selected files even though its catalog `file` parameter is optional. `ug-filesystem cat` reads contents; use only after separate approval. Without validated installed capability, known safe data flow and explicit scope, mark CONTENT_NOT_CHECKED. Do not upload, transmit, copy, modify, rename, move or delete files.
5. The official catalog calls these selected actions `effect=read`, `approval=none`, but their permissions knowledgeStatus is `unknown`; neither catalog label grants user consent, validates NAS rights, nor confirms local-only AI processing. Unless supported authorized checks produce evidence, mark access security and exposure of personal/sensitive content NOT_CHECKED. File names alone cannot prove confidentiality or permission safety.
6. Orchestrate only actual registered-agent results: folder approval → Files Agent listing with completeness and attributable file evidence → conditional Documents Agent reading on separately approved files → deterministic missing/version/privacy uncertainty report. Any unavailable intermediate response is NOT_CHECKED; no fabricated fallback. Apply the [decision policy](references/decision-policy.md) using actual prior results only; never silently substitute similarly named content.
7. Read [disclosures and data-flow boundaries](references/attribution.md), including AI tools, external components, unresolved Uliya model processing and missing official SDK license/validator evidence. Do not describe this provisional skill as NAS-certified.

## Response
Report the authorized folder, each mandatory path, PRESENT/MISSING/NOT_CHECKED status and observed source reference, version concerns, listing completeness, permission and privacy gaps, final READY/BLOCKED/NEEDS_REVIEW status, and the precise human review needed. If no result appears, state the searched scope and whether the scan was complete, then stop.

## Safety
No mutation or external sharing is authorized by this Skill. Ask the user for explicit consent before any high-risk action, even if a tool offers it. Do not declare READY with unresolved mandatory checks, guessed versions, unverifiable tool output, or privacy marked NOT_CHECKED.
