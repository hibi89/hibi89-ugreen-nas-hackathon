# G23 — First-party terms and release-gate audit (2026-10-24 KST)

**Disposition:** READ-ONLY PUBLIC-SOURCE AUDIT COMPLETED; no Skill bytes changed; no official checker executed; NOT_APPROVED_FOR_SUBMISSION.

## Source evidence reviewed

1. [UGREEN Hackathon official rules](https://ugreenhackathon.devpost.com/rules), Round 1 Requirements: initial Skill must be created using official UGOS Skill Creation Tool; submit English 10-question PDF (at most 500 substantive words) and Skill ZIP (at most 10 MB); `SKILL.md` is mandatory; only directly linked Markdown references are optional. Round 1 does not require a live NAS or demo.
2. [UGREEN Hackathon Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit), sections 1, 3, 5 and 7: requires entrant to review User Agreement, Privacy Policy and Skill Content Safety/Publishing Guidelines; recommends checking revised Skill using the official creation tool; only supported capabilities and clear source/approval flow.
3. [UGREEN SkillHub User Agreement](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-user-agreement), Article 7: publishing a Skill on SkillHub requires proper rights and license labels, and grants the platform a limited-purpose worldwide, non-exclusive, royalty-free service license. Article 9 warns not to presume redistribution/commercial rights where no license is supplied. **SkillHub publication is distinct from entering Round 1 via Devpost**; do not silently publish or assume separate SkillHub terms are themselves the entirety of Devpost eligibility.
4. [UGREEN SkillHub Content Submission and Publication Standards](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec), Articles 2.4-2.6, 4.2-4.3, 5.1, 7.1, 11.1-11.4: require accurate declared functions/dependencies/data flows and consent-bound access; forbid misleading certification and sensitive path access; regulate archive safety, placeholders/template examples and attribution of third-party content. Treat as relevant *publication/safety-review guidance*; a textual policy comparison alone is not legal clearance or actual runtime security proof.

## Cross-check against current review artifacts

- Real review source `review/ugreen-official-creator@7af2cb750`: `skill/projectready-nas/SKILL.md` identified in G21 with SHA256 `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead`. G22 CI checked the pinned original SHA and checker JSON, then added disclosures **only to a staging copy**.
- G22 draft `ProjectReady_Creator_Skill_DRAFT.zip` was verified by GitHub Actions [run 40096040369](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40096040369) as exactly one `projectready-nas/SKILL.md` member (4,893-byte ZIP). The accompanied 10-question English PDF was 5,183 bytes, 370 substantive answer words. **The appended disclosures changed the Skill SHA; Codex's prior official checker result does not apply to this edited candidate.**
- The reviewed source has two explicitly labeled **`SYNTHETIC EXAMPLE ONLY`** fully populated delegation examples. They are explanatory examples rather than unresolved placeholders, but the SkillHub standards Article 2.5 forbids *leftover template samples*. **REVIEW RISK / interpretation uncertain**: entrant should assess whether to retain the examples with labels or replace with prose demonstrating parameter injection. Do not treat this as a proven violation; changing any bytes requires a fresh official checker result for the new exact file.
- The staged disclosure names official UGREEN source, OpenAI ChatGPT/Codex assistance, no bundled SDK executable, intended authorized data access, unknown Uliya local/cloud processing, and rights/licensing NOT_CLEARED. This is a **textual disclosure review only**. No real NAS permissions, credential protection under execution, or cloud/local routing were tested.

## Two release approaches compared

- **A — keep existing disclosure-augmented one-file ZIP and recheck exact member (recommended):** preserves the fuller first-party-specified source/AI/dataflow disclosures within `SKILL.md`, 0 new spending, no change to prior candidates; requires participant-supported official checker run and independent SHA comparison of the **same extracted member**.
- **B — submit the unchanged checker-passed P1 Skill with a separate PDF disclosure only:** avoids byte mismatch for that original Skill but risks insufficient in-Skill disclosure per submission guidance; not recommended without documented organizer confirmation and entrant approval.

## Exact remaining gates (no automatic submission)

1. Extract only `projectready-nas/SKILL.md` from G22 **non-submitted** CI artifact ID `12560941466` and run the installed first-party official checker **on those exact bytes** in participant-controlled Codex. Capture checker JSON/result and exact SHA. Do **not** ask for reinstallation, reuploading existing source ZIP, private NAS data, or credentials.
2. Confirm applicable vendor terms, whether Article 2.5 examples need edits, original-work/third-party source obligations and any runtime data locality concerns. Rebuild/recheck if the actual submitted Skill changes again.
3. Obtain entrant editorial/legal/IP review and **explicit approval of the final exact PDF+ZIP**; only then attempt Devpost, and only an actual receipt can establish submission.

**Unchanged:** Master 24-day status DONE 2 / PARTIAL 12 / BLOCKED 3 / NOT_STARTED 7; Oct24 fixed plan 100%, 0 originally assigned hours left; actual work hours NOT_MEASURED. Oct25 G1 remains externally BLOCKED, 1.5h base + 1.5h separate reserve. NAS NOT_RUN; Devpost NOT_SUBMITTED. This G23 audit does not add product functionality or change schedule-completion percentages.
