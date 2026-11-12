# FlowPilot 3.0 — Finalist Execution & Commercialization Fallback Decision

**Approved planning decision:** 2026-11-12 KST (owner instructed GitHub preservation and resume at November 21 decision).  
**Repository / branch:** `hibi89/hibi89-ugreen-nas-hackathon` / `lead/ugreen`.  
**Scope:** PLAN ONLY; no feature implementation, NAS access, third-party execution, release, or Devpost changes. Supersedes only the future-work priority after finalist announcement; keeps all Round 1 submission and original assets frozen.

## 1. Current verified baseline and strict freeze

- Round 1: **SUBMITTED — OWNER_REPORTED** (Nov 9); actual Devpost receipt and uploaded PDF/ZIP byte parity **NOT_VERIFIED**.
- Internal **NAS-excluded 100/100** and **overall NAS-inclusive 75/100 provisional**, not hardware-validation scores.
- Existing official Skill candidate and English proposal are preserved; official Skill ZIP SHA256 `d1d362f1d88507a97e04ce2b186040786aa3a6ec13b4840b7d436a8e45c45984`. Do not modify original ZIP, concept videos, proposals, any private modules, or existing submitted assets.
- Real UGREEN NAS, registered Uliya Expert, supported find/stat read-back, access-denial behavior and actual runtime video: **NOT_RUN**. QNAP trial and synthetic fixtures do not count as UGREEN evidence. HAE, LA, SOVIA are architectural lineage/independent projects, not bundled runtime.
- **No implementation before verified finalist invitation or explicit urgent submission correction.** No idle CI, emulation, NAS activation, unapproved external APIs, cloud uploads, payment, or credential handling.

## 2. Official milestones and verified rules

Official rules: https://ugreenhackathon.devpost.com/rules
- **Nov 21, 2026 (PT):** Finalist invitations via email; up to 30 projects. Confirm the official notice and assigned device/test day/connection instructions/private submission URL. Do not presume selection from generic Devpost marketing email.
- **Nov 22–28, 2026 (PT):** One *assigned* exclusive NAS testing day per finalist, 00:00–23:59 PT, UGREEN iDX6011 Pro 64GB. The owner's device access is limited to this allotted session. Confirm exact PT and KST times from invitation.
- **Nov 30, 2026 23:45 PT / Dec 1, 2026 16:45 KST:** Round 2 final package and public YouTube video URL submission deadline.
- **On/around Dec 6, 2026 14:00 PT / Dec 7, 2026 07:00 KST:** Winners announced (subject to organizer changes).
- Required final `SKILL.md` + directly linked `references/*.md` only, valid official Uliya Skill Standard. No arbitrary executable/script, custom runtime, manifest or unsupported NAS access inside ZIP. Actual functionality must reproduce on assigned real UGREEN NAS. Public YouTube demo **<= 3 minutes**, English speech or complete English subtitles, recorded from the actual assigned NAS and showing real results.
- Schedule source-of-truth is the invitation and official rules, not previous approximate dates or general marketing summaries.

## 3. Finalist branch: technical plan and decision gates

**A (reject for competition until documented):** Unrestricted AI-generated scripts + NAS Docker/VM control + arbitrary autonomous repair. Attractive breadth but unclear registered Expert support, disallowed arbitrary executables in official Skill, greater permission and cost surface, high reliability risk.

**B (SELECTED):** Official registered Expert/CLI capability orchestration + typed bounded workflows + explicit folder scope/consent + read-only evidence + deny-by-default error/recovery. Leverages existing FlowPilot planning, security council, synthetic QA, and operator guide while honestly respecting the Uliya interface.

| Stage | Delivery | Acceptance / proof |
|---|---|---|
| F0 — invitation/intake | Verify official invitation, dates, permissions and registered Expert contract | Exact permitted capabilities/limits, test window and security boundaries recorded; no private credentials in public GitHub |
| F1 — pre-session hardening | Frozen original clone, clean test fixture, dry-run and official Skill Checker | Known SHA and backup, valid Markdown package, scoped approval, no out-of-scope operations |
| F2 — first live NAS gate | Register Expert and call official supported read-only search/metadata using consented disposable folder | Actual UGREEN UI and response/readback captured; evidence classified LIVE, not synthetic |
| F3 — complete user workflow | Plain-language bounded request -> follow-up clarification -> plan -> security review -> approve -> NAS result -> step-by-step explanation | Reproducible real example, explicit denied access and missing/unknown cases |
| F4 — resilience and QA | Permission failure, unsupported API, truncation, timeout, idempotency and recovery; rollback only for authorized new writes | No destructive edits or credentials leakage, honest NOT_CHECKED state, tested recovery or safe stop |
| F5 — final deliverables | Rebuild compliant Skill ZIP, English subtitles/voice and <=3m real NAS video, final Devpost fields | Bytes/readback, screen recording of real assigned NAS, private final link submitted with participant's authorization |

**Progress targets (NOT automatic credit):**
- 75% provisional baseline unchanged now.
- 85% goal only after official Expert contract verified and **real NAS read-only operation readback**.
- 95% goal only after full guided flow + negative tests/recovery on the assigned NAS and reproducible film evidence.
- 100% goal only after compliant final bundle, user-reviewed authentic YouTube demo, actual Round 2 submission confirmation, and all required checklists; subjective scoring remains separate from judging.
- If official API lacks an operation, remove its *claim*, not silently bypass via shell/Docker. Keep conceptual vision separate from demonstrated functionality.

**Safety/cost:** default zero additional paid API subscriptions; first-party NAS session is contest-provided to finalists. Authorize explicitly before activation of account access, data rights, external publication or official submission. Save no credentials or private files in public repository. Do not promise hardware compatibility or end-to-end completion without evidence.

## 4. Non-finalist branch: productization rather than abandoning the technology

Activation trigger: official Nov 21 finalist result/list establishes non-selection, or organizer confirms otherwise. A missing email alone is not definitive; verify Devpost/community announcement. **Plan now, develop only after user decision.**

Two product variants to evaluate after the result:

| Alternative | Buyers/use | Upsides | Limits/costs | Decision |
|---|---|---|---|---|
| **UGREEN-only Skill package** | UGREEN UGOS users | Retains existing Skill proposal and Uliya ecosystem | Actual hardware/Expert access, allowed distribution/commercial rights and version-specific compatibility need proof; limited audience | Secondary niche after authentic hardware/SDK evidence |
| **NAS-independent local FlowPilot** | Windows users, developers, SMB/NFS share users across brands | Broad market, offline first, no recurring AI API required for deterministic audit | Mounted authorized folder and OS permissions required; Synology/QNAP/UGREEN coverage is NOT proven; filesystem race/symlink/UNC/network failure tests needed | **Recommended primary commercial candidate** |

**Commercial MVP** (not approved implementation yet): a Windows-local guided folder/project-delivery verifier: select an authorized local or *mounted* NAS share -> select required files/version rules -> explicitly approve READ metadata -> report PRESENT/MISSING/NOT_CHECKED/VERSION_REVIEW with hashed/redacted receipt -> export offline HTML/JSON or portable report; never scan hidden folders or overwrite source. Add a reproducible consent/deny audit, non-technical setup guide, Windows 10/11 test, signer/license review. Python/SQLite/local deterministic parser can run without billable cloud APIs; optional local LLM only after hardware/license/accuracy verification. "Zero recurring API bill" is a goal, **not** zero hardware/electricity/support cost.

**Commercial launch gates:** verify source/third-party licenses and ownership; no copying of forbidden UGREEN SDK assets or private customer data; multi-NAS SMB/NFS integration proven on named firmware/OS versions; clean install/update/uninstall and safe permission denial; actual user acceptance; price/support and published claims independently reviewed. Release HOLD until these pass. Do not claim all-brand native NAS support merely because a shared folder can be mounted.

## 5. Resume instructions for next chat (Nov 21 KST)

1. Read `HANDOFF.md` -> `STATUS.md` -> `AGENTS.md` -> `REQUIREMENTS.md` -> this decision document -> exact source and current GitHub SHA.
2. Check official invitation email and official Devpost finalist announcement. Marketing emails are not selection evidence.
3. If selected: preserve originals, request only mandatory NAS/login/publication approvals, run F0–F5, reserve the one assigned real NAS day for critical capture; do not inflate progress from CI alone.
4. If not selected: preserve submitted assets, prepare a cost/security/market comparison and user-approval packet for **NAS-independent local FlowPilot**; start commercial development only with authorization.
5. If unresolved: status HOLD and revisit on the organizer's next verified update; do not manufacture a result.
6. On actual development/release work update `STATUS.md`, `HANDOFF.md`, source/test proof and GitHub SHA. Vercel production is **NOT APPLICABLE** for official Markdown-only Skill; productization deployment remains unchosen.

## 6. Decision record / verification

- User: "Save this plan in GitHub; if not a finalist, productize it; see you November 21." Approved **documentation preservation**, not implementation, paid services, NAS access, commercial release or final submission.
- Planning based on `lead/ugreen` G303 status: owner-reported Round1 submission, 75% provisional, freeze until finalist result.
- External references checked 2026-11-12 KST: https://ugreenhackathon.devpost.com/rules and https://ugreenhackathon.devpost.com/ .
- This document is **PLANNED / NOT IMPLEMENTED**; all prior PASS tests remain scoped to their original exact SHA; live hardware, video and future commercial product **NOT VERIFIED**.
