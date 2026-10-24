# G12 — Official UGOS Skill Creation Tool: Codex first-use execution runbook

Status: **READY_FOR_OWNER_LOCAL_CODEX; NOT EVIDENCED; NOT SUBMITTED**. Date: 2026-10-24 KST.
Owner: hackathon individual entrant. Repository: `hibi89/hibi89-ugreen-nas-hackathon`, authoritative branch `lead/ugreen`.

## Mandatory reason, exact primary sources
- [UGREEN Devpost official rules](https://ugreenhackathon.devpost.com/rules), Project Requirements: create the submission using the **official UGOS Skill Creation Tool** from the [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit), with supported registered expert-agent / Uliya format. This is a Round 1 eligibility condition even though **a live NAS device, runtime verification and demo video are not**.
- The Starter Kit describes installation of an `uliya-skill-kit` folder in a supported assistant (WorkBuddy / Claude / Codex), then explicit feasibility check, generation, and creator-tool check. It recommends repeated review to clear requested changes. It does **not** represent static reading of the public capabilities catalog as official-tool use.
- Codex [Agent Skills documentation](https://learn.chatgpt.com/docs/build-skills) lists `$HOME/.agents/skills` (user) and `$REPO_ROOT/.agents/skills` (repository) as discovery locations. Prefer the **local user directory** for the official third-party kit; do not re-publish the official kit or its scripts into this public repo.
- Previous public v0.7.3 kit archive metadata SHA256: `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3` (public-file identity, **not** license approval or runtime certification). If vendor updates it, retain the real new version/hash; do not force a stale archive.
- Do not assume that installing a kit in THIS ChatGPT chat via pasted files qualifies as a supported Codex tool run; the genuine supported environment and its creator-driven output/check steps must be separately evidenced.

## Exact safe operator procedure (Windows / Codex; no unauthorized action)
1. Open [official Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) and use its own **Download the UGOS Skill Creation Tool** link. Do **not** use random mirrors, a repo-hosted copy, or scripts copied from search results.
2. Extract official archive into a **local** directory; inspect structure/read license and executable scripts before use, and verify archive source plus SHA-256 (PowerShell `Get-FileHash -Algorithm SHA256 <local-zip>`). Do not run setup/install scripts with unknown network or file effects.
3. Put the official `uliya-skill-kit` folder under `$HOME/.agents/skills/` (Windows typically `$env:USERPROFILE\.agents\skills\`), following the vendor's precise layout and the installed Codex version's instructions. Keep any copyrighted kit outside the public GitHub repository.
4. Restart Codex and explicitly invoke the official tool using its **actual** `SKILL.md` name and instructions. Do not guess the invocation keyword. Confirm the tool is discoverable, loaded and can answer the vendor's supported-capabilities questions.
5. Open a **safe local workspace** with the authorized UGREEN `lead/ugreen` source only. Point the tool at the *human-entrant-authored* spec below. Require the **official tool's generation step** to write a fresh Skill in a private scratch folder; mere validation of an independently authored folder may not establish the official creation requirement.
6. Run the **official creation-tool check** over the generated Skill, using the documented invocation only. Never claim checker PASS merely because our offline Python tests pass. Review and repair findings; keep both a redacted evidence summary and the generated Skill diff.
7. Compare generated `SKILL.md`/directly linked `references/*.md` with current `skill/projectready-nas/`. Keep all approved user behavior, exact path authorization, read-only evidence classification, fail-closed missing/partial/denied semantics, prohibited sensitive paths, conservative version handling, no executable files, no fabricated runtime guarantees. Do not silently replace canonical work with a generic template.
8. Record local provenance as described below; share only source/tool names, SHA hashes, safe PASS/WARN results and sanitized paths with the lead. Do **not** commit vendor code, a raw Codex transcript, full user file names, access tokens, SDK internals, proprietary files, or consent data. User approves any substantive behavior change or actual release.
9. The lead integrates only entrant-approved generated Markdown and validates the 10-answer PDF and 4-Markdown ZIP with existing GitHub CI. **No Devpost submission without explicit participant approval.**

## Ready-to-paste Codex task

```text
Use the installed OFFICIAL UGREEN "uliya-skill-kit" creation Skill from the official
UGREEN Hackathon Starter Kit. First show the ACTUAL discovered Skill name,
version/source SHA (if known), and source SKILL.md path. If the official tool
is unavailable, STOP and report NOT_EVIDENCED; do not use a generic skill
creator or invent Uliya CLI syntax to claim compliance.

Open hibi89/hibi89-ugreen-nas-hackathon at the authorized lead/ugreen
branch and read skill/projectready-nas/{SKILL.md,references/*.md},
docs/submission/round1_proposal.json, and
docs/submission/G12_OFFICIAL_CREATOR_CODEX_RUNBOOK.md. No secrets or
private NAS data.

Goal: with the official tool, CREATE a fresh ProjectReady NAS Markdown
Skill in a separate local scratch folder. It checks an owner-authorized
project-delivery directory against an owner-provided required-file
checklist. Report PRESENT only with evidence, MISSING only after complete
authorized enumeration, and NOT_CHECKED for partial/denied/unverified
conditions. Identify version ambiguity without arbitrary final selection.
No write actions, outside-folder exploration, credential or sensitive
path probing, fake Agent calls, network uploads, or unsupported scripts.
Use only supported, verifiable read-only file/document expert agents.
Treat actual installed Agent names, invocation signatures and permissions
as UNKNOWN until official evidence establishes them.

After official-generation output, call the official tool's documented
CHECK/review action and record genuine tool findings (PASS/WARN/BLOCKED).
Do not claim official checker PASS if no official checker ran.

Compare output to the original without changing the original or
publishing official vendor files. Show a concise redacted diff and
a provenance checklist: downloaded archive source/version/SHA,
official tool discovered, tool-driven creation actually performed,
official check actually performed, output Markdown hashes, and
unknown runtime/permission conditions. Leave participant approval,
Devpost submission and NAS test PENDING. Require review before merging.
```

## Evidence to return to the lead (minimum, no raw logs required by contest)
- First-party download URL / actual archive filename/version / SHA-256; tool install location **relative or generic**, not private username.
- Official tool ID visible to Codex, source `SKILL.md` path, and **observed loaded/discovered result**, not a claimed intent.
- Explicit official tool generation result (filename/hashes and a short safe description) plus owner input spec; otherwise mark `NOT_EVIDENCED`.
- Official tool checker result with any unresolved warnings, or `NOT_RUN`.
- Exact Markdown differences and signed-off human entrant decision; external SDK/agent live verification still separately `NOT_RUN`.
- The source PDF/ZIP must be rebuilt *after* any approved changes, with a new SHA-backed candidate and human final review.

## Stop boundaries
- Missing/unsupported official tool; conflicting license/terms; observed disclosure of private NAS names; unknown privileged install/script step; any policy requiring unauthorized data; unexpected CLI writes or remote uploads -> **STOP, retain evidence, require owner review**.
- Falsifying use, license clearance, signed consent, official checker result, or Devpost submission is prohibited.
- A GitHub commit of this runbook is **not** evidence of official tool usage. Creator eligibility remains `NOT_EVIDENCED`.
