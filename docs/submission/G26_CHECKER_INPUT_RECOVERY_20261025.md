# G26 — Official checker INPUT recovery (2026-10-25 KST)

**Result:** Exact original G22 candidate bytes independently retrieved and delivered by ChatGPT. **Official first-party checker NOT_RUN**, no official result JSON, no NAS, no Devpost submission and no IP/license/entrant clearance.

## Attempt / failure evidence
User relayed participant Codex finding: installed checker at `C:\Users\haein\.agents\skills\uliya-skill-kit\scripts\check-skill.mjs`. GitHub Actions artifact ID `12560941466` could not be downloaded on their Windows PC: PowerShell DNS resolution failed and browser blocked the download. This is an **input acquisition failure**, not a checker pass/fail. Neither target SKILL.md SHA nor YAML name was locally checked; no errors/warnings count or checker JSON was generated.

## Independent recovery and byte verification
- GitHub-authenticated `download_workflow_artifact` returned the real G22 [workflow 40096040369](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40096040369) ZIP. Wrapper: **16,109 bytes**, SHA256 `a05f5d404572a221fe93cbb963702c5e8edd8b7a4919a4101d74b213ac869941`.
- Extracted `ProjectReady_Creator_Skill_DRAFT.zip`: **4,893 bytes**, SHA256 `3885182cb337fdeb66c6424ffb2ff242971b6bb75a1b55319ba2a7e53dbfd947`. ZIP contains exactly `projectready-nas/SKILL.md`.
- Exact extracted Skill: **12,397 bytes**, SHA256 `770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169`; YAML `name: projectready-nas` verified.
- Exact existing PDF from wrapper: **5,183 bytes**, SHA256 `df071504716c6121e7606cc1178ba7a3fdaa38856c3482b1b0864fc554088f80`.
- Independently reconstructed the candidate from pinned original `review/ugreen-official-creator@7af2cb750b37826fb02a00e2d45cb73f3a85c239` plus unchanged G22 disclosure builder. Git object SHA-1 of reconstructed content equals `315dcb9d2efa35ef8466927fe0c2d8c9b553ca6e`, independently computed for actual extracted artifact member. **No release source was modified.**

## Permanent exact checker input (not final release)
A new, isolated copy of the **same bytes** resides in [`docs/submission/checker_inputs/G22_20261024/projectready-nas/SKILL.md`](checker_inputs/G22_20261024/projectready-nas/SKILL.md). This GitHub snapshot remains after the workflow artifact expiry (2026-10-31 21:57 KST). Exact Skill and inner ZIP were also provided as downloadable attachments in the ChatGPT recovery turn to bypass GitHub DNS/browser restrictions. Attachments are not permanent storage; GitHub remains the durable authority.

This file is **not** a newly created Skill by the official Creator, not a checker-pass, and not a final approved ZIP. It is a byte-for-byte snapshot of already published G22 preview. Prior checker JSON with `static-pass` concerns **different** SHA `164e84fe...`, so it cannot validate `770e08c6...`.

## Next action and acceptance
1. Participant downloads ChatGPT's `UGREEN_G22_Checker_Exact_SKILL.md` (or inner ZIP) and places it as `projectready-nas/SKILL.md`, verifies SHA256 `770e08c6...`. Do not retry failed GitHub artifact route.
2. In already-installed official Codex Uliya kit, request **“Help me check this skill”** for that exact path, without changing the file. Avoid speculative `check-skill.mjs` command-line flags or installing anything.
3. Return official output including target SHA, errors/warnings/info status and actual JSON if produced. If official tool cannot run, remain `NOT_RUN` with blocker evidence. No reuse of the old SHA result.
4. After a genuine same-SHA check, review Article 2.5 synthetic example risk, owner IP/licenses, disclosures, data locality and PDF, then secure separate explicit user approval for Devpost submission.

## Boundaries and scheduling
No live NAS, sensitive folders, credentials, vendor redistribution, payments, extra user permissions, deployment or Devpost actions. G1 official runtime/permissions remains BLOCKED. Round1 needs English PDF and initial Skill ZIP; full NAS run is not a Round1 requirement. Daily October 24 baseline remains 100% delivered with **actual hours NOT_MEASURED**. Master unchanged at **2 DONE/12 PARTIAL/3 BLOCKED/7 NOT_STARTED**. October 25 G1 original budget remains **1.5h base +1.5h separate reserve**; real completion ETA UNKNOWN. This recovery is an input-delivery fix, not product progress.
