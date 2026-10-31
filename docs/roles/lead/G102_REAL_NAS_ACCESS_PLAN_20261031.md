# G102 — Real NAS access decision and one-day acceptance runbook (2026-10-31 KST)

## Decision, corrected official access entitlement

**Official rules, independently checked:** https://ugreenhackathon.devpost.com/rules and https://ai.ugreen.com/pages/ugreen-hackathon

- Round 1 deadline **2026-11-15 23:45 PST = 2026-11-16 16:45 KST**. Round 1 accepts PDF and Markdown-only Skill ZIP; it expressly **does not require live NAS access, a video or a demonstrable runtime**. Do not block pretest solely because an actual device is unavailable. Official original skill creation tool, supported delegate design, integrity, rights and owner submission authorization remain important independent gates.
- Finalist invitations **2026-11-21** by email; up to 30 selected projects.
- Each selected finalist is assigned **exactly one** day in **Nov 22–28 2026 Pacific time**, with an exclusive **24-hour access window (00:00–23:59 PST)** to a UGREEN iDX6011 Pro 64GB, not three hours. The same day in KST is **17:00 on the assigned PST calendar day to 16:59 the following day**. E.g. Nov 22 PST → Nov 22 17:00 to Nov 23 16:59 KST. Credentials and device details must come from the official finalist invitation. No separate NAS purchase/application/payment/credit redemption is required. Do not activate anything or enter owner credentials until permission is obtained.
- **A separate alleged 'three-hour early NAS trial' is NOT_VERIFIED**: no independently confirmed official trial URL, owner invitation, start window, credentials, activation, or usage evidence in the accessible checked project context. Earlier user-facing statements that such a ticket 'exists' were too strong. Do not assume an early device can be accessed or that a trial starts automatically.
- Official Round 2 submission cutoff: **2026-11-30 23:45 PST = 2026-12-01 16:45 KST**. Official marketing materials also mention a NAS testing period extending to Nov 30, but the binding rules distinguish the **assigned one day Nov 22–28** from the larger Round 2 submission period. Prioritize binding rules.

## Existing source baseline and zero external effects

- Repo `hibi89/hibi89-ugreen-nas-hackathon@lead/ugreen`, verified prior HEAD `0d7e62749ba0230c7b43c8927eb208397022ec72`, source G101 `87a0a7856c668067b6b4c77f44152f9f9c5ca654`. G101 full Linux 907 total / 902 PASS / 0 FAIL / 5 SKIP; Windows PowerShell 5.1 full PASS; source CI 4/4 SUCCESS. These are **offline** results, not NAS.
- Exact local G99 candidate `flowpilot-3/SKILL.md` SHA-256 `f21c184f4a0bf370d438b3918a345870faf9d69ee88aac239fe13241a8960ca6`, single-member initial Skill ZIP `f28acfbeba9d3a6e33b9977d1ea1de15b50ca48dbc505144c0b2cb719efc2cfc`; independently re-opened from retained local sandbox and checked original ZIP/member hashes and member size 9,689 bytes. G99 PDF exists, 10 answers, 356 substantive English words, one page; G99 vendor Checker **NOT_RUN** because official 0.7.3 Kit original not available in model environment. The previous G80 owner's static result was 0 errors + 1 delegation warning, which cannot prove G99 passes.
- No new official Skill ZIP/public repository publication, source overwrite, NAS authentication, trial activation, external upload, Devpost action, payment or production deployment performed in G102. Release remains HOLD; Vercel N/A. Do not conflate local Python HAE/LA/SQLite E2E with native Uliya device results.

## Test-day safe entry gate (once assigned and expressly owner-authorized)

1. Verify the **actual finalist email** matches the entrant, assigned date, device and declared expiration, without sharing/publishing credentials. Confirm official NAS environment, permitted role, registered `file-agent` and `document-agent`, callable supported actions and effective folder permissions. Record binary/machine versions and only sanitized redacted metadata. Never infer access from catalog names.
2. Use a **dedicated owner-approved synthetic project folder** with disposable file names, no actual secrets, private documents or customer data. Avoid modifying non-test folders. Install only the expressly approved Markdown Skill ZIP, after confirming its exact version/hash and official checker result. No Python/scripts in Uliya ZIP.
3. Limit test operations to the approved synthetic root. Never follow symlinks outside scope. Do not make repeated write calls on ambiguous responses, bypass interactive approvals or invoke undocumented direct CLIs.

## Explicit functional acceptance matrix (all on real Uliya once authorized)

| Scenario | Input and supported tool | Expected real result | Failure/hold condition |
|---|---|---|---|
| A CHECK_REQUIRED complete | Owner-authorized folder, small required checklist; file-agent `ug-filesystem ls/find/stat`; complete evidence | Exact paths `PRESENT`, absent paths `MISSING` **only if** listing completeness proven; stable attributable references | Missing consent or incomplete enumeration must instead yield `NOT_CHECKED` |
| B REVIEW_VERSIONS | Two benign same-project version candidates in approved folder; metadata only | `VERSION_REVIEW`, both attributable file references, **no automatic final selection**; hashes off by default | Any unapproved content hashing, movement, deletion, or authoritative selection FAIL |
| C HANDOFF_AUDIT | Approved checklist combining required and versionable items; no customer data | Correct dependency summary; confirmed missing mandatory item `BLOCKED`, unresolved versions `NEEDS_REVIEW`; lineage preserved | Fabricated `READY` or invented completion FAIL |
| D SUMMARIZE_SELECTED | Exact file references returned by A/B stage, separate owner document-read consent and acceptable known processing destination, registered document-agent | First file-agent lookup actually occurs; only then documented `ug-document` read; summary attributable to selected references | Unknown processing destination/permission must result `CONTENT_NOT_CHECKED`; no content sent |
| E Guarded edge cases | Scope escape `../`, symlink outside root, restricted name `.env`, denied/partial listing, missing real expert | Stop or `NOT_CHECKED`; no unauthorized read; source data unchanged | Any scope expansion, secret echo, permission bypass, or write FAIL |
| F Recovery | Failed/cancelled/waiting states of expert, empty result, repeated user request | Dependent work stops; explicit statuses; no duplicate mutation | Misreporting previous failure as completed or retrying unsafe effects FAIL |

**Release rule:** A green local test is NOT real-device evidence. Mark each result `PASS/FAIL/BLOCKED/NOT_RUN`, with real device record, exact Skill SHA, date/time with timezone, and **redacted non-sensitive observed output**. If actual supported native result semantics differ from plan, change a **new** proposed candidate and recheck; never fake a successful NAS response or mutate the old G99 owner-reviewed ZIP.

## One assigned day — time-budget priorities (not guaranteed execution)

- **Start → 60 min:** verify official registration, permissions, Skill install/validity and root-scoped `ls/stat`; stop if credentials/role wrong.
- **Next 2–4 h:** A, B, C with synthetic fixtures, actual evidence completeness, failure classification and metadata-only behavior.
- **Next 2–3 h:** D only with verified safe document-processing destination and separate consent; otherwise record `BLOCKED`, do not read.
- **Next 1–2 h:** E/F adversarial and interruption cases; security/negative results documented.
- **Remaining window:** fix actually evidenced defects in a separate candidate, verify native workflow, record short final demo in English and back up redacted non-secret results **before the test environment resets**. Do not plan nonessential feature expansion.

## Missing prerequisites / next action

- **Immediately actionable without NAS:** genuine official 0.7.3 Kit file and exact G99 Checker validation; preserve G99 until checker evidence is captured; rights/license and final entrant review of PDF+ZIP. Existing prior official support response reportedly permits MIT/Apache-2.0/BSD for authored work and "no third-party components redistributed" wording, but author still decides applicable licensing and source provenance.
- **Not actionable before finalist invite:** actual NAS testing day, official device account, native expert permissions, and real observed result schema. Do not expend unverified 3-hour trial time or request users to repeat prior local regression tests.
- **Approval gates:** separate explicit owner consent before any remote NAS access or trial activation, external data transfer, public release/Devpost upload, or security/permission changes. This G102 activity was a rules/access evidence correction and a future one-day acceptance plan, not an actual device test.
- Completed at 2026-10-31 KST; previous G101/G100/G99 checkpoint files and root `HANDOFF.md`/`STATUS.md` untouched. G102 is the latest compact checkpoint; after GitHub push, verify branch HEAD and metadata-only checks, no redundant full backend suite.
