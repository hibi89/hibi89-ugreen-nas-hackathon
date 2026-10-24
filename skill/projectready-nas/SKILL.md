---
name: projectready-nas
description: Read-only evidence review of required delivery documents in a user-authorized NAS project folder.
---

# ProjectReady NAS

## When to use
Use when the owner asks whether a specific project-delivery folder contains an explicit checklist of required files, with version and permission uncertainties identified. This is a read-only review, not a privacy certification or NAS security scan.

## Scope and permission
1. Obtain the owner's exact folder and mandatory file checklist. Never invent required paths or infer access consent.
2. Limit all requests to that folder. Do not enumerate other folders or follow links outside scope.
3. Resolve the registered Uliya Files Expert Agent for file browsing and, only if separately authorized, the Documents Expert Agent for text inspection using the installed official creation-tool documentation. Their exact identifiers, CLI names and argument/result schemas are UNVERIFIED until inspected. Do not invent Agent IDs, commands, parameters or output fields. If capability or permission is missing, report NOT_CHECKED and stop.

## Audit flow
1. List the authorized folder using an available supported file-browsing capability. Record actual returned paths and source references. Check completeness and pagination; a partial or denied result never proves absence.
2. Compare every mandatory path exactly against returned files. An observed file with a source reference is PRESENT. Only a demonstrably complete authorized listing can establish MISSING; otherwise use NOT_CHECKED.
3. Identify candidate version conflicts when multiple similarly named files appear. Mark VERSION_REVIEW. Never select an approved final version solely from filename suffixes, date or size. Ask the owner for authoritative selection or verifiable content evidence.
4. Use supported document reading or reconciliation only if the owner separately authorizes the specific content. Otherwise mark CONTENT_NOT_CHECKED. Do not upload, transmit, copy, modify, rename, move or delete files.
5. Unless supported authorized checks produce evidence, mark access security and exposure of personal/sensitive content NOT_CHECKED. File names alone cannot prove confidentiality or permission safety.
6. Orchestrate only actual registered-agent results: folder approval → Files Agent listing with completeness and attributable file evidence → conditional Documents Agent reading on separately approved files → deterministic missing/version/privacy uncertainty report. Any unavailable intermediate response is NOT_CHECKED; no fabricated fallback. Apply the [decision policy](references/decision-policy.md) using actual prior results only; never silently substitute similarly named content.
7. Read [disclosures and data-flow boundaries](references/attribution.md), including AI tools, external components, unresolved Uliya model processing and missing official SDK license/validator evidence. Do not describe this provisional skill as NAS-certified.

## Response
Report the authorized folder, each mandatory path, PRESENT/MISSING/NOT_CHECKED status and observed source reference, version concerns, listing completeness, permission and privacy gaps, final READY/BLOCKED/NEEDS_REVIEW status, and the precise human review needed. If no result appears, state the searched scope and whether the scan was complete, then stop.

## Safety
No mutation or external sharing is authorized by this Skill. Ask the user for explicit consent before any high-risk action, even if a tool offers it. Do not declare READY with unresolved mandatory checks, guessed versions, unverifiable tool output, or privacy marked NOT_CHECKED.
