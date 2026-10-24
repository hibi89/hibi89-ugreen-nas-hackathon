# G21 — Independent GitHub review of G20 P1 Creator Skill (2026-10-24 KST)

**State:** `P1_DELEGATION_FIX_INDEPENDENTLY_CONFIRMED`; `STATIC_CHECK_REPORT_HASH_CORRELATED`; `RELEASE_PACKAGING_BLOCKED`. This audit reads the exact remote review branch rather than trusting the chat summary. **No merge, no NAS call, no SDK vendor-code copy, no external publication or Devpost submission.**

## Grounded GitHub facts

- Repo: `hibi89/hibi89-ugreen-nas-hackathon`.
- Candidate branch: [`review/ugreen-official-creator`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/review/ugreen-official-creator), HEAD and **user-reported exact commit match** [`7af2cb750b37826fb02a00e2d45cb73f3a85c239`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/commit/7af2cb750b37826fb02a00e2d45cb73f3a85c239).
- GitHub comparison `lead/ugreen...review/ugreen-official-creator`: **ahead 1, behind 0, changed paths precisely 3**, with common parent `6a660075edd1de5f01c10a31e304902fbecafe2c`. Exact paths: `skill/projectready-nas/SKILL.md`, `docs/submission/G20_P1_CHANGE_REPORT.md`, `docs/submission/G20_P1_OFFICIAL_CHECK_RESULT.json`. Original `lead/ugreen` did not receive this code.
- Reviewer recomputed **SHA-256 directly from fetched GitHub UTF-8 content** (with independent test vector `abc` verified against known SHA256), not merely copied participant hashes:
  - Candidate `SKILL.md`: **10,481 bytes**, SHA-256 `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead` — **exact match**; Git blob `fb23b19c9308ca9b52abd5c28407cac4299d601f`.
  - Checker JSON: **420 bytes**, SHA-256 `92a6891b0889a89cd09f16ed960e9f72a4df33f8114ce0ee22b9beefeff50140` — **exact match**; parsed content says `static-pass`, `checkFormatVersion=2.0.0`, `catalog.checkedVersion=2.0.0`, errors/warnings/info **0/0/0**, and points to the same SHA as the observed candidate.
- Checker **actual invocation** remains Codex-reported, not independently rerun on an installed UGREEN tool in this reviewer environment. No GitHub Actions workflow run was returned for this **review** commit; do not label it CI PASS.
- The change report accurately says **original Creator generated Skill was preserved and this P1 was a subsequent manual edit in a review copy**, NOT a new official generation run. Previously independently verified original generated Skill SHA `e1b071666b836cc464147821d7823bc3061c757434697d9a64250d4a9abd5b4a`, with ZIP report [G20](G20_UPLOADED_REVIEW_ZIP_INDEPENDENT_AUDIT_20261024.md).

## Functional and safety review

**G20 P1 FIX VERIFIED BY READING SOURCE:**
- Before each delegation, explicitly construct a **self-contained** `--instruction` from real, validated owner inputs, not parent conversation or unresolved placeholders.
- `file-agent`: exact approved folder, exact required relative paths, each owner-authorized version pattern, and read-only constraints/completeness/error reporting.
- `document-agent`: only actual in-scope file references returned by the first agent, the separately approved per-reference content scope and version candidates, and the exact owner question, with `file`/`query` constraints or **stop**. Synthetic `/demo-handoff` delegates explicitly labeled examples, not real authorization.
- Preserved: no outside-folder operations, restricted file/credential paths redacted and not probed, no write/copy/delete/upload, `PRESENT` with cited observation only, `MISSING` only with verified complete authorized listing, `NOT_CHECKED` otherwise, human `VERSION_REVIEW`, conservative overall outcomes, `completed/failed/cancelled/waiting_user/waiting_approval` handling and unknown local/cloud data flow. No live NAS/Agent outcome fabricated.
- **Residual operational unknowns**: registered Expert Agents, exact permissions/invocation, complete listings, processing location and any claim of local-only privacy. Static document compliance is not runtime performance.

**RELEASE BLOCKER FOUND — must not merge or zip branch directory as-is:**
- The new one-file Creator Skill has **zero direct Markdown references**.
- Its GitHub `skill/projectready-nas/` directory nonetheless **inherits three old files** under `references/catalog-actions.md`, `references/decision-policy.md`, `references/attribution.md`, because only `SKILL.md` was modified in review branch. These are real files independently fetched on review branch.
- Existing `tools/round1_package_audit.py` enforces that **each included reference is directly linked exactly once from SKILL.md**, and also mandates `references/attribution.md` with disclosures. Hence new one-file Skill cannot be packaged by the existing four-file builder unchanged. This is **a packaging-contract mismatch, NOT failure of official single-file static checker**.
- Release resolution: choose either **(A)** isolate official new one-file Skill in its own clean staging directory, with required AI/IP/data-flow disclosures placed in the English proposal or within Skill itself, and adapt independent packaging audit/builder in a separately reviewed change; or **(B)** deliberately link, validate, and approve compatible reference Markdown in a new cohesive multi-file Skill, then rerun official checker on that *exact* candidate. Prefer **A** for minimal independently generated source and fewer stale/contradictory catalog claims, subject to actual Rule structure confirmation and owner's approval.
- Current `round1_proposal.json` Q8 still says **no official validator** executed. If this updated Skill becomes the selected submission candidate, rewrite Q8 to distinguish **user-reported actual official tool creation and static-check PASS** from **NAS/Agent not run**, then regenerate PDF and verify 500-word bound, ZIP format, hashes and consistency. Do NOT submit the old PDF unchanged.
- The public review branch and prior three-file uploaded review ZIP are **not** final submission receipts.

## Evidence/gates to supervisor

`G20_P1_SOURCE_REVIEW=PASS`; `REVIEW_SOURCE_SHA256=VERIFIED`; `ATTACHED_CHECKER_JSON=INTERNALLY_CONSISTENT_0_ERRORS_0_WARNINGS`; `CHECKER_EXECUTION=CODEX_REPORTED`; `RELEASE_BUNDLE=BLOCKED_EXISTING_ORPHAN_REFERENCES_AND_OLD_BUILDER`; `Q8_PDF=STALE`; `RIGHTS_AI_IP_DATAFLOW=REVIEW_PENDING`; `NAS=NOT_RUN`; `USER_RELEASE_APPROVAL=NOT_GIVEN`; `DEVPOST=NOT_SUBMITTED`; `SKILLHUB=NOT_PUBLISHED`.

**Next lead deliverable:** a separate release-package compatibility plan and exact candidate builder/test that stages only the approved generated Skill (do not modify or merge review branch), keeps proper disclosures in the proposal, repairs Q8 and validates rendered PDF / Skill ZIP after owner chooses the source. Explicit source selection and final submission approval remain owner-controlled.

**Original plan:** leave 24-day ledger 2 DONE / 12 PARTIAL / 3 BLOCKED / 7 NOT_STARTED; Oct24 original scheduled deliverables 100%, actual elapsed hours not measured; Oct25 G1 time baseline 1.5h plus separate reserve 1.5h with unknown actual ETA; no incremental paid spend.

Official reference: [UGREEN Rules](https://ugreenhackathon.devpost.com/rules) · [Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit).
