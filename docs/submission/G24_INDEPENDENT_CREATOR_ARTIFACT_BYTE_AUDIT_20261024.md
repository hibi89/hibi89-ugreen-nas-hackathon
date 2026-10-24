# G24 — Independent actual G22 artifact byte, PDF and checker-target audit

**Audit date: 2026-10-24 KST; audit scope: existing GitHub Actions artifact only.** No tool/Skill source modified, no reviewer or entrant approval, no NAS call, no official checker rerun and no Devpost submission.

## Acquisition and independent checks

Retrieved **the real** [G22 creator preview CI artifact](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40096040369), artifact ID `12560941466`, name `UGREEN-CREATOR-ONE-FILE-PREVIEW-NOT-SUBMITTED`, via authenticated GitHub artifact download (not by reconstructing filenames or trusting only past status text). Artifact expires 2026-10-31 12:57:04 UTC. Its ZIP wrapper was **16,109 bytes**, actual downloaded SHA-256:

`a05f5d404572a221fe93cbb963702c5e8edd8b7a4919a4101d74b213ac869941`

Opened the actual wrapper and independently inspected the manifest and all five members: `ProjectReady_Creator_Preview_Manifest.json`, `ProjectReady_Creator_Proposal_DRAFT.json`, `ProjectReady_Creator_Proposal_DRAFT.md`, `ProjectReady_Creator_Proposal_DRAFT.pdf`, `ProjectReady_Creator_Skill_DRAFT.zip`.

| Actual file | Actual size | SHA-256 | Evidence |
|---|---:|---|---|
| Inner Skill ZIP | 4,893 B | `3885182cb337fdeb66c6424ffb2ff242971b6bb75a1b55319ba2a7e53dbfd947` | One and only one ZIP member `projectready-nas/SKILL.md` |
| Exact checker TARGET `SKILL.md` (ZIP member) | 12,397 B | `770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169` | Exact raw member bytes recomputed independently |
| English proposal PDF | 5,183 B | `df071504716c6121e7606cc1178ba7a3fdaa38856c3482b1b0864fc554088f80` | One physical page, rendered visually and checked for clipping/overlap; 10 Q/A headings visible |
| Manifest JSON | 1,579 B | `36d912cd0f095ffd93ca84567c99a0a4d7043ca4c972bf6272fc3801e23fd2e6` | Manifest's three content digests agree with independently recomputed bytes |

The PDF was rendered from the **real downloaded PDF** at 125 dpi and manually inspected: one legible portrait page, all ten question headings, Q8 and disclosure footer visible, no visible clipping or text collisions. Preview carries explicit `DRAFT - NOT SUBMITTED` notices and 370/500 answer-word count. A visually legible PDF is **not** an entrant editorial or legal approval.

The exact staged Skill contains **two explicitly marked `SYNTHETIC EXAMPLE ONLY`** expert-delegation examples, along with the provenance/AI/license/dataflow notice appended by the G22 preview builder. No unlinked legacy references, executable/vendor files, or additional ZIP members were observed in the *inner* Skill ZIP.

## IMPORTANT: specific source checker hash mismatch

- G21 originally reviewed and participant-Codex reported checker `static-pass` for **a different** unaugmented Skill SHA `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead`.
- The **exact** Skill intended for G22 preview is SHA **`770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169`**, because mandatory development/provenance disclosures were appended. The original passing checker JSON must be **rejected as evidence** for the staged file.
- This independent hash inspection is **not** official Uliya static checking, not an Agent permission check and not a NAS runtime test. Official `static-pass` for the changed exact bytes remains `NOT_RUN / BLOCKED_EXTERNAL_PARTICIPANT_CODEX`.

## Rule comparison

[UGREEN Round 1 official rules](https://ugreenhackathon.devpost.com/rules) require official tool provenance, an English ten-response PDF and a constrained Skill ZIP; real NAS execution is explicitly not required in Round 1. The [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) section 7 recommends rechecking after changes and tells supported assistant users to request “Help me check this skill.” Its [first-party SkillHub Publication Standards Article 2.5](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec) disallows **leftover unreplaced placeholders, template samples, or self-contradictory instructions**. These **explicitly synthetic and fully populated** safety examples may or may not meet the narrower notion of leftover template samples; **risk requires editorial assessment, not a finding of rule violation**. The publication standards and Devpost entry checklist are different processes; evaluate the more relevant obligation without conflating them.

## Next one action: exact-content official checker handoff

1. In a trusted participant-controlled environment, use **the existing G22 preview artifact**, not the earlier review Skill. Extract `projectready-nas/SKILL.md` from `ProjectReady_Creator_Skill_DRAFT.zip`, then compute SHA-256 of the extracted file. It **must equal `770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169`**.
2. Open the already-installed official `uliya-skill-kit` in the supported Codex environment and ask it to **check (not rewrite or publish) this exact file** using the official checker. Provide exact file path and request report/json showing the scanned file's SHA, errors/warnings. Avoid fake or assumed CLI invocations, do not install again, and do not read/upload any private NAS/customer files.
3. Return/check checker output and exact target hash. **A `static-pass` against any other SHA is NOT a pass for this file**. If a change is required, keep this checked artifact unchanged; create a separate revised candidate and repeat the check for its new SHA.
4. Then perform participant review of PDF text, IP/third-party/license rights, data locality statements, and the two marked examples, followed by explicit approval of the exact final PDF+ZIP. Only then submit on Devpost with an actual receipt. Do not request owner PC action until they can access the installed Codex environment.

## Disposition

**G24 artifact identity, manifest, ZIP member, PDF page-level visual and independent SHA checks PASS.** Official checker on `770e...` **NOT_RUN**, legal/IP rights **NOT_CLEARED**, NAS **NOT_RUN**, Devpost **NOT_SUBMITTED**, no spending/credentials/private data. Oct24 fixed daily plan remains 100% / originally assigned 0h remaining (actual labor NOT_MEASURED). 24-day master stays DONE2/PARTIAL12/BLOCKED3/NOT_STARTED7; Oct25 G1 base 1.5h + separate 1.5h reserve, real end ETA unknown. No external-dependency progress percentages were inflated.
