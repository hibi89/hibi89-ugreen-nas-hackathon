# ProjectReady NAS — Round 1 official-rule compliance & lead gate audit
Date checked: 2026-10-24 KST. Owner: UGREEN lead, branch lead/ugreen.
Scope: official **public** Devpost Rules and UGREEN Starter Kit web page ONLY. This is an independent lead submission-compliance review, NOT the worker's UGR-001 archive/CLI capability matrix, nor an SDK/NAS run.

## Sources and precedence
- Official Rules: https://ugreenhackathon.devpost.com/rules — sections 1, 4 (Project Requirements, Round 1 Submission Requirements), 6 (Judges & Criteria), 11 (General Conditions).
- Official Kit landing page: https://ai.ugreen.com/pages/hackathon-starter-kit — sections 2-8.
- Where landing-page examples and the *Round 1 submission* requirements differ, follow Rules (section 11 says Rules prevail); do not infer that all example files are permissible as ZIP submission content.
- Contents of linked **downloadable creation-tool archive have NOT been inspected in this lead audit**; exact CLI syntax, registration and expert-agent capabilities remain **UNVERIFIED**, delegated to UGR-001.

## Source-verified requirements (public Rules)
1. **Round 1 deadline**: 2026-11-15 23:45 Pacific Standard Time = 2026-11-16 16:45 KST. Internal target 2026-11-10 KST is NOT the official deadline.
2. **English PDF**: answer all ten substantive questions from Rules section 4: purpose; target user/problem; solution; core flow; difference; NAS capabilities per step; technical approach (CLI, expert agents, inputs/permissions/model/data handling); actual implementation status; TWO core + ONE edge validation scenarios; known limitations. Aggregate substantive responses **<=500 English words** (specified declarations/license information excluded).
3. **ZIP**: initial SKILL.md with Skill name, description, inputs, supported CLI, orchestration and completion/error behavior. Name lowercase-hyphenated **2-64** characters; description **<=1024** characters. Optional Markdown files under `references/` **each directly linked** from SKILL.md.
4. **ZIP <=10 MB** in public Rules. No scripts, executables, binaries, extra manifests, general-purpose runtimes, unauthorized direct NAS access; no genuine credentials, real personal data, unlicensed components or undisclosed dangerous external data flows. Do NOT pack READMEs merely because landing-page section 5 shows an illustrative development-folder README; Rule's submission list is more restrictive.
5. **Round 1 skill need not run/install on real NAS**; no NAS access, video, repository, demo, screenshot, test report required for preliminary stage. Never claim practical SDK/NAS testing unless actually performed.
6. **Model**: local NAS model encouraged, **not mandatory**; authorized third-party models permitted under terms, licenses and data-flow/privacy disclosure. No new paid API without participant approval.
7. **Judging**: equally weighted User Value, Innovation & Differentiation, Technical Quality, AI NAS Fit & Validation. The first viability/theme gate is pass/fail. Rank cannot be predicted from documentation.
8. **Round 2**: same skill, official NAS runtime and public YouTube demonstration under 3 minutes; finalist remote NAS only by invitation and assigned day.

## Internal conservative packaging limits — NOT independently confirmed from public Rules
The repo's previously adopted engineering targets of **PDF <=1 MB**, **ZIP unpacked <=10 MB**, **each file <=1 MB**, and **<=100 files** are to be kept as *conservative internal release checks* pending confirmation in official archive/platform constraints. The visible public Rules directly confirm the ZIP submission file must be <=10 MB, but this audit did not locate those other exact numeric limits there. Do not mislabel them as verified Rules in the proposal.

## ProjectReady evidence contract / anti-hallucination acceptance
- Explicit folder scope, explicit delivery checklist, user authorization.
- Search outcomes are differentiated: `ABSENT_AFTER_COMPLETE_SCAN` vs `NOT_SEARCHED` (permission denied / incomplete search / unsupported query) vs `AMBIGUOUS`.
- Per requirement result: `PASS`, `FAIL`, `REVIEW` or `NOT_CHECKED` + evidence reference, limitation and next action.
- Aggregate `READY` iff all **required** checks were completed and passed and no required unresolved security check remains. Any required `NOT_CHECKED` blocks READY. `BLOCKED` for evidenced missing mandatory outputs; `NEEDS_REVIEW` for unresolved versions, insufficient evidence or unsupported mandatory checks.
- Source files remain untouched; no silent move/delete/share/upload or expanded scope. Repeated reads should not cause mutations.
- Do not present filename similarity as proven content/hash equivalence or PII absence as confirmed unless official registered capabilities permit it.

## Technical approaches for G2 (not a scope change; user approval gate if fallback reduces agreed quality)
**Approach A: authorized file-list/metadata evidence only.** Advantages: fewer capabilities, quicker, zero new services; disadvantages: weak final-version proof, cannot promise deep content/PII scans. If core missing-check remains useful but major categories become NOT_CHECKED, any material scope reduction needs participant approval.
**Approach B: official supported File + Document expert orchestration.** Advantages: inspect checklist content and version context, richer evidence, stronger judging differentiation; disadvantages: more exact CLI/permission/format assumptions and higher failure complexity. Prefer B *conditionally* if UGR-001 proves registered commands and safe flows. Both must fail closed.

## Release gate & evidence checks (pending)
- [ ] UGR-001 official archive inventory, archive version/file paths and registered CLI & expert-agent matrix received and checked; no assumption based solely on landing-page categories.
- [ ] G2 exact supported CLI and argument/output examples mapped to every workflow step; all rights/access/disclosure assumptions bounded.
- [ ] Two happy/negative core cases + permission-denied/partial-search edge; synthetic labels; no false READY.
- [ ] `SKILL.md` valid name/description, only authorized CLI, linked `references/*.md`; no README or executable in submit ZIP.
- [ ] PDF ten answers and <=500 English substantive words verified; actual implementation status stated honestly.
- [ ] PDF/ZIP size, archive contents, checksums, secret/PII/licence inventory verified. Stricter internal size caps treated as local policy until verified.
- [ ] Actual Devpost final submission receipt checked; draft is NOT submission.

## Live state at this audit
UGR-001 REVISION 1 remains READY, worker report is initial/empty, `SDK_CAPABILITY_MATRIX.md` absent on feature/missing-files. This audit does **not** satisfy or close UGR-001. No Skill code or runtime/CI, NAS interaction, PDF/ZIP build, final Devpost submission tested here.
Remote baseline: lead/ugreen 3f193407b03691e371da3914f7e6710286c22961; worker feature/missing-files 9b3052bf82ad1a8a4844b1aeee699c0b759251dc, version-conflicts f1aaf9f28800c9fb563d846622583314f6be6c85, privacy cbd7f2ac866ad338d2006dcc1337a5c44f029423, main d8cd806cb2b3842a80a571fd09910ec370e2de17. New audit documentation commit SHA must be verified after push.
