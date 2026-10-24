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
