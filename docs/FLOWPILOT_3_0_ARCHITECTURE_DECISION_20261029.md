# FlowPilot 3.0 — Architecture Decision and 4-Day MVP WBS

Date: 2026-10-29
Status: USER-APPROVED DESIGN DIRECTION; CODE INTEGRATION NOT VERIFIED
Target: UGREEN Uliya AI Skill / UGOS Pro
Branch: `lead/ugreen`

## Product objective
A user describes an automation in natural language. FlowPilot inspects explicitly authorized NAS data, asks for missing parameters step by step, builds a previewable workflow, requires explicit execution approval, runs an allowlisted workflow, produces a report, and retains execution evidence.

## Component contracts
- **HAE**: user intent, multi-turn slot filling, planning and orchestration.
- **LA / Lightning Azent**: user's n8n-derived workflow engine. Reuse *actual existing* workflow-generation/validation modules where technically compatible; do not relabel a new JSON generator as a proven LA integration. A bounded Python runner may execute a limited set of approved operations when the full LA/n8n runtime is unsupported, with its provenance disclosed.
- **FlowPilot Skill**: Uliya entrypoint, authorized NAS file access, CSV schema/metadata parsing, local output/report.
- **DBVORA**: future database management adapter; SQLite execution history alone is **not** evidence of actual DBVORA integration.
- **SOVIA**: future sovereign behavioral risk/audit adapter; SQLite logging or a `sovia_risk_level` column alone is **not** evidence of actual SOVIA integration.
- **Safety guard**: explicit user consent for file inspection and separate approval for execution; path scoping, source read-only, output allowlist, rejection of unapproved/destructive actions. Audit does not substitute for pre-execution enforcement.

## Bounded P0 demo
1. User requests: "Combine sales CSVs in my NAS and produce a customer-level monthly summary."
2. HAE asks for missing input folder, grouping column, output path and execution cadence where necessary.
3. FlowPilot reads authorized CSV schema and prepares a workflow plan.
4. LA-derived generator, if source-compatible, produces a validated workflow definition. Otherwise clearly label the fallback implementation.
5. User sees plan and approves execution (distinct from clarification confirmation).
6. Bounded runner reads source CSVs, aggregates by customer, writes a new report to an approved output path.
7. SQLite records execution ID, timestamps, inputs/outputs and errors. SOVIA/DBVORA names are attached only if their real modules are invoked and verified.
8. Show report, workflow definition, consent/approval evidence and audit trace.

## Scope
P0: real natural-language/slot flow, scoped CSV read, workflow preview, explicit approval, actual CSV execution, report, SQLite trace.
P1: file-change metadata, duplicate/version checks, verified DBVORA and SOVIA adapters, project-delivery readiness.
P2: local document RAG, scheduled/background runs, broad n8n node coverage.
Excluded from MVP: external scraping, silent file modification/deletion, heavyweight multi-service deployment.

## Four-day WBS (targets, not measured durations)
- **Day 1 — source compatibility**: inspect HAE/LA actual code and licenses, existing FlowPilot functionality and official Uliya permissions; choose in-process module vs external execution based on evidence; integrate minimum request/CSV access contracts. Do not assume HAE/LA are Python-only.
- **Day 2 — workflow planning**: reuse existing FlowPilot conversation/consent mechanisms; add CSV schema parsing, LA workflow definition, preview and separate execution approval.
- **Day 3 — execution and trace**: run bounded CSV aggregation, preserve originals, constrain output paths, persist SQLite history, add actual SOVIA/DBVORA adapters only if source compatibility is verified; demonstrate end-to-end.
- **Day 4 — evidence and packaging**: regression/security tests, official Skill checker on final ZIP, concise English summary PDF (<=500 words and <=1MB per current repository requirements), demo capture if required/valuable, update STATUS/HANDOFF, prepare Devpost entry. Submission requires owner authorization.

## Acceptance / evidence gates
- Never claim an official NAS/Uliya runtime success based only on local Python tests or static Skill checker.
- Never claim LA, SOVIA or DBVORA integration without source-level calls and execution evidence.
- Record exact commit SHA, tests, generated output and audit record for the happy path; verify rejection/no-consent cases.
- Do not silently replace the existing canonical Skill, G52 PDF/ZIP, or other project repositories.
- Existing G68 local metadata workflow (496/496 offline tests in 2026-10-28 handoff) is a starting point, not evidence of NAS automation completion.
- Official deadline recorded in REQUIREMENTS.md: 2026-11-16 16:45 KST. Internal target may be earlier. Recheck live official rules and submission form before release, including video requirements.
- Actual NAS/Uliya Expert, external upload, release and Devpost submission remain on HOLD until owner approval.

## Integration decision
**Option B: lightweight bounded reuse is preferred**, conditional on actual HAE/LA source and Uliya runtime capabilities. Avoid assuming the Uliya Skill sandbox supports persistent n8n services or arbitrary Python execution; these claims need official documentation or runtime proof. If runtime execution is unavailable, ship an honest Skill proposal and a clearly labeled separate local proof-of-concept rather than misrepresenting the two as integrated.
