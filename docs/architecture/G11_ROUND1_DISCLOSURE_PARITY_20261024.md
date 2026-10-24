# G11 — Real Round 1 artifact rights/disclosure audit and PDF source parity (2026-10-24 KST)

## Inputs actually verified
- GitHub Actions artifact 12554397827 from code 256a766d (run 40079252294): downloaded exact outer artifact ZIP, opened inner 4-file Markdown ZIP, inspected manifest SHA-256, and rendered the generated 1-page PDF for visual review. Existing draft PDF 4,722 bytes, inner ZIP 6,562 bytes, exactly 351/500 substantive answer words, all ten Q/A visually legible. No personally identifying information, passwords or executables observed in those reviewed files; this is a bounded manual review, NOT a comprehensive confidential-data forensic guarantee.
- Official [UGREEN Devpost Rules](https://ugreenhackathon.devpost.com/rules), Section 4: Round 1 needs ten English answers <=500 substantive words, initial SKILL.md ZIP, original/authorized materials and source/license/data-flow disclosures. No NAS runtime, demo video or official checker execution required for Round 1; however the official UGOS Skill Creation Tool **must be used to create the entry**. The current source history provides only public catalog / independent Markdown authoring: official creation tool execution **NOT EVIDENCED**.
- [Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit): recommends creator checker, readable fail handling, user permission before high-risk action, original work and truthful claims.
- [UGREEN SkillHub publishing policy](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec): no sensitive content/secret targeting, prior consent, adequate rights.

## Real defect found and narrow fix
- Prior PDF renderer hardcoded a shortened AI/third-party disclosure paragraph instead of using docs/submission/round1_proposal.json disclosures, while package validation checked only ten substantive questions/answers. Therefore an author-corrected declaration could silently produce a stale PDF.
- Option A: derive all four disclosure paragraphs from canonical JSON and exact-match the extracted PDF text against that same JSON, preserving 351-word substantive answers; add synthetic regression cases. **SELECTED: zero incremental cost, one source of truth, fail-closed CI.**
- Option B: manually re-review and paste the hardcoded footer before each build, with no regression; lower up-front effort but repeat omission risk and poorer maintenance. **REJECTED.**
- Developer-only files changed: tools/render_round1_proposal_pdf.py, tools/round1_candidate_bundle.py, tests/test_round1_candidate_bundle.py. No customer data, SDK execution or Skill ZIP source changes.
- Further code correction: tools/round1_release_gate.py now distinguishes mandatory **proof of having used official creation tool and licensed/original source**, required entrant/editorial/dataflow review, from recommended official checker execution and finalist-only NAS/private runtime work. Additional test protects this separation. This does NOT waive the mandatory official tool-use requirement and never marks draft ready for submission.

## Precise unresolved release conditions
- **Round 1 substantive artifact checks**: new PDF full ten Q/A + four JSON disclosures, actual 4-Markdown ZIP and byte hashes — CI PENDING until new source workflow finishes. Visual PDF review must be repeated for newly generated PDF because layouts can change.
- **Required human/external facts still OPEN**: proof the Skill has actually been created/checked using official UGOS tool, official-package license/right to reference it, source originality and permitted third-party materials, final English editorial review, AI assistance and actual dataflow statements, actual user approval for the exact PDF/ZIP and Devpost submission. Do not invent clearances from static tests.
- **Not required before Round 1**: real NAS access or recorded demo, officially executed checker validator (recommended), live device permission/privacy attestation. These stay NOT_RUN and are separate Round 2 risks.
- **Current result**: PREVIEW / NOT_APPROVED / NOT_SUBMITTED, production N/A. Actual work time NOT_MEASURED, no new cash charge, no token, customer or NAS data touched.

## Master reconciliation and next action
- G11 early independent submission-document review maps to UGR-D16 (PDF/ZIP) and UGR-D17 (rights/release). Both remain PARTIAL; global 24-day tally stays DONE 2 / PARTIAL 12 / BLOCKED 3 / NOT_STARTED 7.
- Oct24 original finite day was already 100%/0h assigned remainder; G11 is additional advance without double-counting. G1 official runtime/Agent gate on Oct25 remains 1.5h base + 1.5h separate reserve, real ETA unknown.
- **Next single work item**: verify newly generated PDF's source-parity and visual layout in GitHub artifact; obtain official creator provenance without unsafe execution, then present exact PDF/ZIP/rights and disclosure checklist for entrant approval. No Devpost submit without approval.

## First regenerated source verified; visual regression found (2026-10-24 KST)
- Source 76cdefec3647f0cc734a4c2039220d43714480f8 completed 204/204 offline tests PASS in CI 40080095791, Round1 PDF/ZIP manifest/source-disclosures audit PASS in CI 40080095846; master progress and handoff CI also PASS.
- Downloaded new real artifact ID 12554751949 and rendered PDF. It is readable and includes all four canonical disclosures, but now has **2 pages**, with only dataflow and source text on page 2. This is an actual aesthetic QA issue despite valid PDF and byte hashes. Final quality acceptance is withheld.
- Minimal typography correction pending: shrink vertical paragraph spacing/leading without changing answer text, disclosures or font sizes. New visual inspection and CI must pass. Mandatory official creator-use provenance and license/entrant review are independent OPEN gates.

## Final G11 verified release-preview evidence (2026-10-24 KST)
- Source SHA **e1fa58f4f64c99135861490f009ea93bc0c798c6**. Offline GitHub CI 40080489057 **204/204 PASS**, bundle/release-gate CI 40080489067 **PASS**, master CI 40080489060 PASS, handoff CI 40080489079 PASS.
- Corrected font-preserving paragraph spacing eliminates first attempt's wasteful second PDF page. Downloaded actual latest artifact **12554029301** (expires Oct31 09:04:21 UTC), SHA checked ZIP/PDF/member hashes to manifest. New PDF 5038 bytes **exactly one page**, 351/500 substantive answers, four exact canonical declarations fully preserved, manually rendered image visual QA PASS (no overlap, cut-off or unnecessary second page). Skill ZIP 6562 bytes/four direct-linked Markdown members.
- No source/claim implying actual official creator use; official UGOS tool installed use remains **NOT_EVIDENCED** and prevents final eligibility approval until proof. Separate official checker execution not mandated at Round1, finalist NAS not required. Participant/source/license/editorial approvals and actual Devpost submission remain OPEN/NOT_SUBMITTED.
- This update is factual handoff only; original master D16/D17 stays PARTIAL, 2 DONE/12 PARTIAL/3 BLOCKED/7 NOT_STARTED; Oct24 finite scheduled scope 100%/0 hours allocated remaining, developer hours not measured.
