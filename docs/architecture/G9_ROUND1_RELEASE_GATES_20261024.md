# G9 — Round 1 technical integrity versus submission authorization
Date: 2026-10-24 KST

## Problem identified
The previous `validate_pdf` scanned all ten question headings but only tested the **first 35 characters of the first and last answers**. A damaged or stale middle answer could have passed the technical draft PDF check. Also the ZIP/PDF SHA256 manifest did not itself expose a clear, human-readable release authorization decision.

## Implemented controls
1. `missing_pdf_sections` compares all ten exact official questions **and complete substantive answers** against text extracted from the rendered PDF. Missing or modified middle content fails the pipeline, instead of checking only question headings and first/last prefixes.
2. `tools/round1_release_gate.py` takes the generated manifest and the **exact built PDF/ZIP bytes**, cross-checks both SHA-256 digests and lengths, expected PDF parse report, 4 Markdown-only ZIP inventory, exactly ten questions and <=500 English answer words. It refuses forged `SUBMITTED`/`CLEARED` states.
3. New `tests/test_round1_release_gate.py` gives 8 positive/negative synthetic tests including tampered ZIP/PDF, fake approval, false official checker claims and duplicate ZIP paths. Two additional tests cover intentionally modified middle answers.
4. The CI preview artifact now includes reproducible release evidence: `Round1_DRAFT_Release_Gates.json` and `Round1_DRAFT_Release_Checklist.md` alongside PDF, ZIP and manifest. This is strictly a **draft preview**.
5. Output is constrained: `assessment=OFFLINE_TECHNICAL_PREVIEW_PASS` is **not** an `official Skill checker pass`, a NAS permission grant, a Devpost submission or finalist result. `release_decision=NOT_APPROVED_FOR_SUBMISSION` until the participant and primary sources genuinely verify outstanding conditions.

## Unresolved external requirements
- Participant acceptance of final answers, PDF appearance and accurately disclosed AI assistance
- Official SDK license/third-party rights, actual model/data handling and access scope
- First-party Creation Tool validator run in an authorized suitable environment
- Actual Devpost form submission and verifiable receipt

Official starter kit guidance: https://ai.ugreen.com/pages/hackathon-starter-kit (§5–7: genuine supported actions, human authorization, checker, finalist-only NAS tests). The historical official event rules are linked at https://ugreenhackathon.devpost.com/rules; live rules page may block direct scraping, so no new unsupported claim is inferred.

**Work accounting:** On Oct 24 these controls advance original D16 and D17 (Nov 8/9) but DO NOT satisfy their whole final acceptance. Both remain PARTIAL. Master 24-day status 2 DONE, 12 PARTIAL, 3 BLOCKED, 7 NOT_STARTED. Original 10/24 limited task list 100%, 0h remaining; extra work outside that denominator. Future G1 time allocation Oct25 1.5h+1.5h reserve, actual hours NOT_MEASURED. No fees, no NAS test, no Devpost submission.

**Remote proof:** pending on initial source commit; replace no PENDING with SUCCESS until exact GitHub Actions verified.

## 2026-10-24 KST G9 FINAL VERIFIED — all PDF answers, release checks and 200-test CI
- **Source SHA** `d666fc593a680ee357c0cc84aa20a5347924300b`. [Offline readiness](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40078079863) **200/200 PASS**, actual 4-file Skill preflight PASS (not official checker). [Round 1 draft candidate and release audit](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40078079879) **SUCCESS**: PDF 1 page / 4,722 bytes; Skill ZIP 4 Markdown / 6,004 bytes; all ten official question titles AND full answers matched extracted PDF text, 351/500 words. PDF/ZIP SHA256 byte check PASS; draft release decision `NOT_APPROVED_FOR_SUBMISSION`. [Master progress](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40078079878) SUCCESS and [closeout](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40078079857) SUCCESS on same source.
- GitHub Actions artifact [`UGREEN-Round1-DRAFT-NOT-SUBMITTED`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40078079879/artifacts/12553977616) ID **12553977616**, created 2026-10-24 08:27 UTC, expires **2026-10-31 08:27 UTC** (7 days). Contains draft PDF, Skill ZIP, SHA256 manifest, `Round1_DRAFT_Release_Gates.json` and `Round1_DRAFT_Release_Checklist.md`. A draft artifact is NOT a Devpost entry/receipt.
- G9 code `tools/round1_release_gate.py` + 8 tests and upgraded `tools/round1_candidate_bundle.py` + 2 tests. Corrected PDF integrity weakness (previously first/last answer prefix only): all ten complete answer bodies now checked. Independent SHA checks catch tampered PDF/ZIP. Report requires real participant editorial approval **PENDING**, license/attribution **NOT_CLEARED**, privacy/dataflow/access **NOT_CLEARED**, official Uliya creation-tool checker **NOT_RUN**; actual NAS **NOT_RUN** and Devpost **NOT_SUBMITTED**. No official kit source/customer NAS data or secrets redistributed.
- Master original 24-day statuses **DONE 2 / PARTIAL 12 / BLOCKED 3 / NOT_STARTED 7**. Original D16 (Nov8 PDF/ZIP) and D17 (Nov9 release audit) advanced but still **PARTIAL**, not falsified completed; current 10/24 finite day **100% / 0h assigned remaining**. No double count. Next original G1 work D02 on Oct25 base 1.5h + separate reserve 1.5h, actual completion ETA UNKNOWN, work hours NOT_MEASURED, incremental spend 0 KRW.
- This separate docs/evidence closeout commit is PENDING GitHub CI until its exact remote SHA is verified. Next `ㄱ`: attempt official G1 first-party registered Agent/permission/CLI runtime proof or official support; when external access blocked, continue independent release review but do NOT claim readiness or submit without participant authorization. Use MASTER_PROGRESS.md then current LIVE_HANDOFF as source of truth.

