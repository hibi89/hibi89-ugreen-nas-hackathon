# G41 — Exact-original Round 1 PDF / Skill third-party and AI disclosure audit (2026-10-26 KST)

**Status: technical source-and-disclosure integrity PASS; publication/release HOLD.** No external communication, NAS access or Devpost submission. Checked [official UGREEN 2026 rules](https://ugreenhackathon.devpost.com/rules) §4 Round1, Third Party Integrations, and [Resources FAQ](https://ugreenhackathon.devpost.com/resources) on October 26, 2026.

## Evidence chain and actual run
- Dedicated independent [G41 Actions run 40321597804](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40321597804) **SUCCESS**. Reads the **original** G37 artifact 12644844524 from finished GitHub run 40312824725 (not locally regenerated) and exact first-party G36 source from GitHub. Focused regression **8/8 PASS**; broad offline readiness suite **269/269 PASS** on initial G41 code commit `7eedef326c71529fbb1a98697ad2c2439e5140d4`. Original push's mandatory handoff check initially failed because this ledger was not in the same commit; closeout documents are synced separately with result verified on final HEAD.
- PDF **5,227 bytes SHA256 `d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936`** contains 10 complete English official questions and answers, **378/500** words, all four disclosure fields, 1 extractable page. ZIP **5,685 bytes SHA256 `b3efbe261dc0ea35e90c290e362fc0efad70e59315d8cc5f0a009d445ece66d7`** contains exactly one `projectready-nas/SKILL.md`, byte-equal to G36 **14,522 bytes SHA256 `e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4`**, exact independent first-party checker `static-pass` run 40311253113. Original JSON/Markdown body match original hashes and full PDF text. **Do not use 30,188-byte sandbox-transformed PDF copies**, flagged in G38.
- Permanent [machine evidence](evidence/G41_IMMUTABLE_DISCLOSURE_CI_20261026.json), G41 Python audit source `tools/g41_submission_disclosure_audit.py`, synthetic unit tests `tests/test_g41_submission_disclosure_audit.py`, CI `.github/workflows/g41-submission-disclosure-review.yml`. No user data included, no release action available.

## Policy matrix: identified vs still unproved

| Area | Evidence from exact G37 original | G41 disposition |
| --- | --- | --- |
| Official 10 English questions, 500 answer-word cap | 10 fully matched, 378 words; PDF text extractable | **TECHNICAL PASS** |
| Initial Skill ZIP, supported file type | Single Markdown SKILL, source exact official G36 SHA | **TECHNICAL PASS**, NAS runtime not proven or required for Round1 |
| AI coding tools | PDF lists OpenAI ChatGPT + Codex roles; Skill also lists them | **DISCLOSED**, human entrant confirms all tools used and owns/reviews wording |
| Required UGREEN official kit source | G36 Skill identifies `https://ai.ugreen.com/pages/hackathon-starter-kit` | **SOURCE IDENTIFIED** |
| **Applicable UGREEN kit/platform license** | Current PDF and Skill explicitly say **not cleared / pending**; official ZIP (G39) has no separate filename-matched license document | **EXTERNAL LEGAL / VENDOR HOLD**: cannot invent MIT or assert rights; rule explicitly requires components/sources/applicable licenses |
| Offline packaging tools | PDF lists Python, ReportLab, pypdf | **INVENTORY PARTIAL**: G37 CI also installs and uses **PyMuPDF**, absent from PDF third-party tooling list |
| External services/data flow | Owner-approved NAS file listing / separate doc consent; local vs cloud routing unknown | **HONESTLY QUALIFIED**, installed runtime processing location not verified |
| Original official Creator usage | Entrant Codex creation report, G20 review Git source proof; G36 exact first-party checker independent | **CREATOR LOCAL ACTION ONLY PARTICIPANT-REPORTED**, does not equal independent replay |
| Entrant originality, writing voice, rights | No entered human attestation | **PENDING** |
| Actual upload and receipt | No entrant submission instruction or Devpost receipt | **NOT SUBMITTED** |

**PyMuPDF nuance:** It was used as an **offline QA raster/PDF geometry tool**, not in the delivered ZIP, and the official text names third-party components and applicable licenses rather than explicitly requiring every local test tool in the user-facing PDF. Treat this as an **inventory completeness warning** to resolve during next owner-approved PDF edit, not independently as a confirmed disqualifying violation. Any new PDF changes its SHA and require regenerating and revalidating the actual PDF and matching release manifest; the G36 Skill does not need a new checker if its bytes remain unchanged. Never silently change the G37 original.

## Proposed entrant-reviewed wording (NOT inserted in PDF)
> Required official development platform: UGREEN UGOS/Uliya Skill Kit v0.7.3, source https://ai.ugreen.com/pages/hackathon-starter-kit, referenced but not shipped; its precise applicable license/service terms remain subject to vendor and entrant verification. Development and offline quality checks used Python, ReportLab, pypdf, and PyMuPDF; none of these libraries ships inside the Markdown-only Skill ZIP. OpenAI ChatGPT and Codex assisted the design, tests, and drafting. The human entrant owns final disclosure approval. No customer NAS data was accessed. If run later, NAS file lists require per-folder authorization and document content separate approval; supported Uliya processing location is not independently verified.

This text is intentionally a **draft with unresolved rights**, not a license declaration or release authorization. Do not use it to claim required applicable license has been identified.

## Remaining owner and lead actions
1. Entrant/organizer establishes a **real applicable UGREEN kit license or official terms basis** and proper disclosure wording; request no outbound assistance until separately authorized. The official kit website and SkillHub service terms are sources, not automatic proof of a named standalone SDK copyright license.
2. Entrant personally validates original work, registered team eligibility, original Creator use, all AI tools used, and the PDF answers in their own words. [Official FAQ](https://ugreenhackathon.devpost.com/resources) **permits AI tools with disclosure and recommends human-authored answers**; recommendation is not an AI ban.
3. Technical G42 next: independent fail-closed source/data-integrity and code stability tests, with no NAS call, file upload, or material changes to G37 exact deliverables. If PDF text is later changed, mint a separate preview with a **new hash** and rerun audit.
4. Explicit separate approval of exact artifact SHA pair, followed by entrant-controlled Devpost upload and actual receipt. `ㄱ` means continue *internal work*, not publish.

**Deadline:** 2026-11-15 23:45 PST = 2026-11-16 16:45 KST. Original 24-day plan unchanged: **2 DONE /12 PARTIAL /3 BLOCKED /7 NOT_STARTED**; Oct26 G1 real NAS 0% BLOCKED, base 1.5h and separately reserved 1.5h; actual human work hours unknown.
