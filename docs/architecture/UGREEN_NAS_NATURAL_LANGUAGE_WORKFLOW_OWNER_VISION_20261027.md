# UGREEN NAS FlowPilot — Owner Natural-Language Automation Vision and Official Contest Boundary
Decision documented 2026-10-27 KST. **VISION / IMPLEMENTATION PROPOSAL ONLY, NOT REAL NAS WORKING SYSTEM OR OFFICIAL SUBMISSION.** Existing G36/G37 ProjectReady originals remain immutable. Competition Skill must be original and newly authored.

## Owner's product hypothesis
Make UGREEN NAS the user-owned AI automation center: using the owner's authorized files, natural-language requests dynamically form an n8n-like workflow. The assistant clarifies missing inputs, previews steps/permissions/outputs, runs only safe authorized tasks, verifies and presents results, and (if actual platform capabilities permit) saves a reusable workflow. Meaningful use of personal NAS data can improve utility/retention, but lock-in and worldwide Top 2/3 awards are **ambitions, not measured outcomes**.

### Example user journey
"Find today's deliverables in my NAS folder, check required files, compare changes and prepare a handoff report." The AI collects folder/checklist/content permissions, builds a multi-step plan from supported registered expert-agent actions, previews it, executes only approved steps, and cites file evidence per action. Denied, unavailable, ambiguous and unverified actions return NEEDS_REVIEW, not fabricated success.

### Future connectors (optional, not functioning by default)
Potential GitHub, supported deployment site(s), Google Sheets/Docs/Drive, Notion and common SaaS. **ChatGPT's own connectors do NOT prove Uliya/NAS can access those apps**. Only promise an integration once official UGOS Expert Agent/CLI, license, authentication scope, data egress consent, privacy, rate and real NAS runtime have independently passed. No secret storage in public ZIP; no off-NAS data transfer without consent.

## Official compliance — no arbitrary n8n
https://ugreenhackathon.devpost.com/rules : official Uliya Skill Creation Tool, newly authored Markdown **SKILL.md** and directly linked references/*.md, registered authorized Expert Agents/official supported CLI; **no arbitrary scripts, execution runtime, unauthorized NAS direct access or arbitrary REST bridge** in contest Skill ZIP. Round 1 by Nov16 16:45 KST: English 10-answer <=500 substantive words PDF + <=10MB Markdown-only Skill ZIP. No live NAS or public video required. Round 2 only if finalist Nov21: one assigned device day, same Skill must actually work on provided NAS; final package + YouTube video by Dec01 16:45 KST.

## Alternative designs
| | A: Complete n8n-equivalent workflow engine | B: Bounded official Uliya natural-language multi-step Skill |
| --- | --- | --- |
| Vision | Arbitrary connectors, schedule, API calls, scripts, workflow execution | User chooses goal, dynamic slot questions, plan, consent, authorized Files/Documents/other verified registered Expert Agent orchestration, evidence, fail-closed status |
| Contest legality | Generic engine/scripts/REST bridge are not supported in Skill ZIP | Fits Markdown/Expert Agent constraints if each action is authorized and actually supported |
| Time/cost | Large third-party OAuth, security, runtime and real-NAS scope | Small, no independent runtime, offline validators, actual NAS later |
| Demonstrability | Full platform likely infeasible before cutoff | One bounded multi-step NAS-data workflow can be visibly judged, if supported and tested |
| Long term | Owner's preferred product direction, possible after contest / platform agreement | Practical first building block and demonstration of n8n-like UX |
Chief recommendation: **B for contest compatibility, with A stated as long-range platform vision**, subject to owner choice before broadening existing one-HANDOFF_AUDIT submission freeze. Unsupported multi-agent chaining is NOT assumed. If only one official flow actually works, disclose limitation and keep currently accepted single recipe rather than fabricating general automation.

## Proposed competition-visible workflow (capability gates required)
1. User says what they need. Prompt for precise authorized NAS root, desired outputs, required checklist, document-content and destination permissions.
2. Validate tasks against an allowlist of actually registered official Expert Agent operations. Produce inspectable plan, typed inputs/outputs, limited branching and explicit negative/failure states.
3. Obtain human approval for sensitive access or changes. Read-only by default. Strict root/secret/symlink protection, no file-body prompt injection instructions.
4. Execute ONLY verified supported steps. Record source paths/IDs and observed timestamps; incomplete listing, failed privilege, unknown API and ambiguous versions => NEEDS_REVIEW/BLOCKED.
5. Produce evidenced report. Workflow persistence/cron/mutations/external connectors cannot be claimed without real platform support and independent tests.
6. Round-2 real device must run this same Skill, not an external mock. Testing: one happy, one missing-input, denied-root, incomplete-list, prompt injection, missing-agent and publication/rights gates.

## Strategic credibility
UGREEN user value and NAS fit could be stronger from user-owned data as the workflow's substrate, but final score/rank/prize depends on actual evidence. Do not imply a specific pure 'idea prize' until official prize criteria show one. Bigger feature list with no operational path can reduce technical-quality ratings.

## Current execution boundary and provenance
The existing [submission freeze](../../SUBMISSION_SCOPE_FREEZE_20261027.md) remains active until explicit owner acceptance of a verified bounded multi-step adjustment. Current old ProjectReady G36/G37 originals and exact hashes remain unchanged. No code/Skill/PDF/rights/third-party keys/authorized NAS/external connection/Devpost submission performed in this documentation task.