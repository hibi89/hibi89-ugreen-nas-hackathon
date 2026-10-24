# ProjectReady NAS — APPROVED UGREEN DELIVERY PLAN
2026-10-24 KST | Status: user-approved PRODUCT/PLAN, not a tested implementation.
Owner: UGREEN lead, lead/ugreen. Other hackathon schedules intentionally excluded.

## Product fixed by the user
ProjectReady NAS (working title), one Uliya AI Skill, track: Automate Your Workflow.
Target user: a freelancer or small production team preparing a project folder for customer delivery.
User request: "Is this project ready to deliver?"
Distinctive value: compare a specified client delivery contract/checklist against actual permitted NAS files/documents, attach evidence for each requirement, explain blockers, and give a Go/No-Go decision. Not just a generic duplicate-file cleaner.

Flow: user grants folder scope and supplies mandatory deliverables -> supported registered Expert Agents and UGOS CLI read permitted files/documents -> missing deliverables, competing versions, and permitted information-disclosure concerns are checked -> evidence-based READY / BLOCKED / NEEDS_REVIEW report.
Every required criterion has PASS, FAIL, REVIEW or NOT_CHECKED status and a file/document reference or explanation. A required NOT_CHECKED must never produce READY. Read-only by default; never auto-delete, move, upload, share, or expose user data. No calls to undocumented CLI. Hash comparison, deep content inspection, local AI and PII detection are conditional on real Starter Kit support.

Data contract to refine at G2: input {authorized_folder, required_deliverables, scan_scope}; observation {requirement_id, supported_capability, evidence_refs, observed_value, confidence_or_uncertainty}; output {requirement_id, check_type, verdict, evidence_refs, limitation, next_action}. Not actual Uliya API syntax.
Separate reads from writes: v1 stores no new customer data and has no permanent custom DB. Repeat reads should not mutate or widen privileges. Partial failures return NOT_CHECKED and explicit next actions.

## [LATEST APPROVED EXECUTION POLICY — 2026-10-24 KST]

**Parallel across competitions; sequential inside each competition.** UGREEN has exactly one active feature worker at a time. Current active worker: **NONE**. The older three-worker concurrent-development plan is superseded. W1 Oct 28-29 -> W2 Oct 30-31 -> W3 Nov 1-2, with lead verification before each handoff; lead integration Nov 3-5. No change to the Nov 10 early submission or the Nov 16 official deadline. See docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md.

## Dated checkpoints — KST
| Date | Gate / work | Measurable acceptance |
|---|---|---|
| 10/24 | G0: product and budget fixed | This user-approved GitHub document exists; technical implementation not yet claimed |
| 10/25-26 | G1: official package capability study | Obtain and inspect actual UGREEN Skill Developer Package, supported commands, Expert Agent registration, allowed permissions, model/data-flow/price conditions; list confirmed vs unknown |
| 10/27 | G2: architecture freeze | Contract checklist-to-file-evidence-to-verdict, permissions, recovery and unsupported-function behavior defined using real supported capabilities |
| 10/28-29 | G3a: W1 missing-files ONLY | Evidence-based missing deliverables check and tests, lead-reviewed handoff |
| 10/30-31 | G3b: W2 version-conflicts ONLY | Candidate version conflict and uncertainty results; W1 inactive |
| 11/01-02 | G3c: W3 privacy ONLY | Supported security/data handling checks; W1/W2 inactive |
| 11/03-05 | G4: lead integrates one Skill | SKILL.md and directly referenced Markdown; trace synthetic contract -> evidence -> decision. No active feature worker |
| 11/04-06 | G5: validation | Official creation-tool checks if accessible; synthetic completed/missing/version/permission-denied/empty-result tests; record PASS/FAIL and untested |
| 11/07-08 | G6: English proposal | Ten required answers, <=500 English words (internal target 430-470), PDF <=1 MB; differentiate from existing file tools with clear real-world use |
| 11/09 | G7: release candidate | PDF/ZIP size, structure, AI/third-party disclosure, no secrets/PII, file checksum/backup verified |
| 11/10 | G8: early final submission | Create Devpost project, submit PDFs/ZIP, confirm final receipt not just draft; user retains ultimate decision |
| 11/11-16 | Buffer | Fix only evidenced problems, revalidate receipt before official deadline **2026-11-16 16:45 KST** |

The dates are execution targets when each AI chat is called, not unattended automation. If G1 is blocked, investigate cause, retry once with a materially better approach, then pivot to official free support or a supportable flow. Scope reduction, new cost, privacy/permission change requires user approval.

## Worker responsibilities
- feature/missing-files: map each explicit delivery requirement to actual authorized file evidence; distinguish absent from not searched and ambiguous rules.
- feature/version-conflicts: competing deliverable/version candidates; explain evidence and request user confirmation rather than assuming newest based on filename. Never invent hash or version-history APIs.
- feature/privacy: read permissions and unauthorized transmission guardrails; PII scanning only if officially supported. If not checked, state that clearly; never claim that a file is safe.
- lead/ugreen: official tool/capability evidence, input/output contract, integration, ZIP/PDF, 4 judging dimensions, Devpost receipt, reporting.
Assignments: docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md. **Workers operate strictly sequentially (one active at a time).** Each worker reads its own branch HANDOFF / STATUS / AGENTS / REQUIREMENTS / OPERATIONS, and returns results via TO_UGREEN_LEAD.md. No AI chat starts automatically.

## Tests and judging
CORE1: 7 mandatory deliverables present with usable evidence -> READY only if all required checks were performed.
CORE2: 2 missing deliverables plus 2 conflicting final versions -> BLOCKED or NEEDS_REVIEW with evidence and concrete action.
EDGE1: access denied, partial folder search, unsupported CLI, missing PII analyzer -> NOT_CHECKED, no fabricated completion.
Also check repeat execution leaves source unchanged. Assess each official 25% dimension: user value, meaningful differentiation, technical quality, NAS feature fit. Judge score or finalist probability is not yet known.

## Submission contract
Round 1: English 10-answer PDF <=500 words and <=1 MB. One ZIP with SKILL.md and directly linked references/*.md only. Frontmatter name lowercase hyphenated length 2-64; description <=1024 characters. ZIP compressed/uncompressed each <=10 MB; each file <=1 MB; <=100 files. No separate scripts, executables, manifests, binaries. List AI tools, sources/licences, third-party components and external flows. No real credentials or personal data.
NAS hardware, code repository link and demo video are NOT required in Round 1. Only one project per individual/team.
Round 2 if invited (up to 30): Nov 21 PT invitation; one free remote NAS iDX6011 Pro testing day Nov 22-28 PT; install/test/record same Skill; submit final ZIP and <3-minute public YouTube demo with English narration or full English subtitles by Dec 1 16:45 KST. Take backups before remote access expires.

## Budget — zero new cash spend target
| Item | Additional planned cash |
|---|---:|
| Devpost entry and official dev resources | KRW 0 |
| Existing GitHub and available AI subscription | KRW 0 additional |
| New paid APIs, new hosting, domain, DB | KRW 0 (do not use) |
| PDF/ZIP creation with free tools | KRW 0 |
| Purchase of NAS / finalist free remote NAS | KRW 0 |
| Free screen recorder/editor and YouTube if finalist | KRW 0 |
| Total incremental payment target | **KRW 0** |

Existing subscriptions, electricity, internet, own labor, prize taxes/transfer fees excluded; actual model access and included quotas must be verified. No paid action without explicit approval.

## State and source
Verified: registration screen provided by entrant, official contest requirements, GitHub branches and original planning documents. Still UNVERIFIED: actual downloaded package internal CLI, PII/version functionality, API, skill running on NAS, Devpost project creation and final submission, CI and deployment.
Official rules: https://ugreenhackathon.devpost.com/rules
Official package: https://ai.ugreen.com/pages/hackathon-starter-kit
