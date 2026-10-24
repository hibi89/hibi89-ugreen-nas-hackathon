# G8 — Round 1 reproducible candidate delivery, 2026-10-24 KST

**Status:** code prepared; OFFLINE_CI_PENDING at source-commit time. Official Uliya Skill Creation Tool **NOT_RUN**, real NAS **NOT_RUN**, privacy & SDK license **NOT_CLEARED**, Devpost **NOT_SUBMITTED**.

## Primary official-rule correction
At [UGREEN Devpost Official Rules](https://ugreenhackathon.devpost.com/rules), Section 4, Round 1 requires the **ten exact listed questions**, total substantive English responses <=500 words, a PDF and an Initial Skill ZIP. The Round 1 ZIP requires `SKILL.md` and directly linked Markdown references only; executable scripts cannot be included. The Initial Skill Package does **not** need to run on NAS during Round 1, so no invented runtime proof is necessary. The older draft used synonymous, non-identical headings; **all ten headings** are now replaced with the exact first-party text. Substantive answers remain 351 words. The previous local PDF is superseded and must be regenerated using the updated sources.

## Concrete source changes
- `docs/submission/round1_proposal.json` and `ROUND1_PROPOSAL_DRAFT.md`: official ten prompt texts with all draft disclosures and unchanged 351-word answers.
- `tools/check_round1_proposal.py` and tests: forbid source question drift, missing disclosures and false submitted/NAS claims.
- `tools/round1_candidate_bundle.py` with six new offline tests: reproducible SHA256 ZIP, independent ZIP byte-for-byte member verification, no extra files, PDF size/header, strict PDF parse + text retrieval for ten exact question headings and first/last answers, no source ZIP/scripts or SDK embedded, and manifest for review.
- `.github/workflows/round1-candidate.yml`: in a temporary GitHub runner, generate **draft** PDF with ReportLab, verify with pypdf, assemble ZIP + manifest, upload a **seven-day GitHub Actions artifact** labelled `UGREEN-Round1-DRAFT-NOT-SUBMITTED`. Only locally authored Markdown enters the ZIP. PDF libraries are build-only and excluded.
- The workflow must not submit to Devpost or invoke any Uliya checker/NAS service. The exact file/folder wrapper of the ZIP needs official validator verification before describing final compliance.

## Work attribution / full schedule
Pulled forward as independent G8 portion of D16 (2026-11-08 ZIP/PDF preparation) and D17 (2026-11-09 package quality). These dates remain **PARTIAL** until approved final artifacts, license/security release gates, and real submission evidence; separate D15 (Nov 7 English 10-answer draft) stays **DONE**. Original 2026-10-24 finite 100% task scope and 0 scheduled hours unchanged. Original 24-day status tallies **DONE 2/PARTIAL 12/BLOCKED 3/NOT_STARTED 7**. Future hours unchanged: baseline 34.25h + separate reserve 26.75h overall; actual time spent NOT_MEASURED; G1 on 10/25 remains 1.5h base + 1.5h reserve, ETA unknown.

## Manual release gates
1. Participant must approve exact English proposal and third-party/AI disclosures, including platform license status.
2. Check the generated PDF render visually for text overflow and correct official ten question headings; regenerate on every change.
3. Confirm ZIP root-folder interpretation and official Uliya checker status before claiming full validator compliance.
4. Approve NAS data-safety scope separately. Never put real credentials, private data, official SDK originals or commercial assets in any public GitHub artifact.
5. Submit via authorized Devpost entry and record a **real submission receipt**. Current state remains NOT_SUBMITTED.

Source SHA/CI run IDs are to be attached only **after** GitHub Actions finishes. In-progress evidence is not success.
