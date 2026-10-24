# G22 — Official Creator one-file UGREEN Round 1 PREVIEW construction (2026-10-24)

**Source selection:** reviewed official Creator output at `review/ugreen-official-creator@7af2cb750b37826fb02a00e2d45cb73f3a85c239` with exact `SKILL.md` SHA256 `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead`. This is a **separate candidate preview**, not a merge into `lead/ugreen` or a Devpost submission.

## Official rule basis (newly rechecked Oct 24)

[UGREEN Devpost Official Rules](https://ugreenhackathon.devpost.com/rules): Round1 can consist of `SKILL.md` alone. `references/*.md` files are optional but, if present, must be directly linked. ZIP up to 10MB, each file up to 1MB, Markdown-only; English proposal 10 questions ≤500 substantive English words and PDF ≤1MB. The official [overview](https://ugreenhackathon.devpost.com/) explicitly requires **third-party and open-source components, sources/licenses, principal newly developed functionality and AI tools/use** to be disclosed **inside SKILL.md or its linked references**, not solely inside the PDF.

## Implementation choice and why

- **Selected:** checkout the participant-controlled **pinned exact review commit** in a separate private CI directory. Verify the real `SKILL.md` SHA and actual checker JSON SHA `92a6891b0889a89cd09f16ed960e9f72a4df33f8114ce0ee22b9beefeff50140`, ensure JSON says `static-pass` (0 errors/warnings/info) and exact Skill target SHA. The *official checker invocation itself is Codex-reported*; CI here does not run vendor code.
- Extract **only `projectready-nas/SKILL.md`** into an isolated staging folder; do **not** copy unlinked preexisting `references/*.md` (3 legacy files) or reviewer-only JSON/Markdown into the contest ZIP.
- Append a clearly marked Markdown **Development provenance and third-party disclosures** section to the **staged Skill copy only**, covering entrant-directed original workflow, OpenAI ChatGPT/Codex roles, UGREEN official source, no bundled third-party executable, unverified applicable vendor license, intended data flows, unknown Uliya cloud/local processing and unperformed NAS validation. **This changes the staged candidate SHA** and has **NOT been rerun through the official checker**; no official-pass claim for augmented bytes.
- Create an **isolated English proposal** by cloning the existing ten-answer JSON in memory and amending Q8 from 'no official validator' to distinguish participant-reported official original creation/static-check PASS from no runtime NAS/Agent access. Update AI/tool disclosures consistently, recalculate the ten-answer word count and build a searchable, parse-checked PDF. **Do not modify canonical old four-file proposal JSON/MD or old Skill/PDF/ZIP candidate**.
- Create a deterministic **single-Markdown ZIP** and a manifest proving its exact SHA, one file, size, PDF SHA/pages, word count and every external gate **NOT_CLEARED**. Stage as a GitHub Actions artifact retained seven days, not Devpost/SkillHub.
- Test failures for source SHA drift, report SHA drift, false checker status and ZIP members; run independent manifest and decoded ZIP check in CI. Official checker results from old SHA do not transfer to new SHA.

## Current guards

`SOURCE_PINNED`, `NO_LEGACY_REFERENCES_IN_ZIP`, `NEW_AI_IP_DATAFLOW_DISCLOSURES_IN_SKILL`, `PDF_Q8_CORRECTED_FOR_CREATOR_REPORT`, `OFFICIAL_CHECKER_ON_AUGMENTED_PREVIEW=NOT_RUN`, `REAL_NAS=NOT_RUN`, `EXPENSES=0`, `ENTRANT_RIGHTS/EDITORIAL_APPROVAL=PENDING`, `DEVPOST=NOT_SUBMITTED`.

The old four-file packaging tests and old PDF are intentionally unchanged; they do not certify or stand in for this separate new candidate.

## Operator notes

- Builder: `tools/round1_official_creator_preview.py`.
- PDF rendering: existing `tools/render_round1_proposal_pdf.py` now accepts an optional validated in-memory proposal without changing its default behavior.
- Unit tests: `tests/test_round1_official_creator_preview.py`.
- CI: `.github/workflows/round1-official-creator-preview.yml` (pinned checkout, preview files in runner temp; no repository push).
- Follow-up **only after entrant has time / approves the candidate**: locally rerun official `uliya-skill-kit` checker on the **exact disclosure-augmented Skill** and return new SHA/checker JSON. Judge novelty/value and review UGREEN SDK terms. Then do final package and user-signoff flow; never treat a preview upload or CI PASS as Devpost acceptance.

**CI state when report was authored:** PENDING until an actual GitHub Actions run completes; do not claim a success before confirming its run ID. Daily original plan 100% delivered, 0 scheduled Oct24 hours remain, actual work hours unmeasured; master total states 2 DONE / 12 PARTIAL / 3 BLOCKED / 7 NOT_STARTED and next Oct25 G1 base 1.5h + separately reserved 1.5h unchanged.
