# G15 — Real first-party tool distribution -> owner Codex preparation (2026-10-24)

## Verified official facts and safety boundary
- The [official UGREEN Hackathon Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) §§2–5 says the **official UGOS Skill Creation Tool** supports **Codex, Claude and WorkBuddy**, is installed by placing the entire `uliya-skill-kit` folder in the assistant's skills directory, then **restarting** the assistant. The assistant must use the official tool to *generate* a Skill and then *check* it. GitHub code execution of an independent Python prototype is not proof of creation by that tool.
- [Official Devpost rules](https://ugreenhackathon.devpost.com/rules) §4 require that tool for Round 1. No actual NAS runtime or demo is necessary in Round 1; no independent custom executables allowed in the submitted Skill. The official tool archive itself should **not** be redistributed into public source or submission ZIP.
- Exact official archive URL is pinned from the official vendor Starter Kit §3: `https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898`. This specific public ZIP had previously been downloaded and hashed using vendor-only read-only GitHub runner (metadata CI 40064613266): SHA256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`. **This identity does not prove license terms, live Agent permissions, SDK executable safety, compatibility, or eligibility.**

## Meaningful new artifact and test
- `tools/prepare_ugos_codex_kit.ps1`: owner-side PowerShell first-party archive preparation and **opt-in** copying of the official `uliya-skill-kit` directory to `~/.agents/skills/uliya-skill-kit` for Codex, without running any vendor code, installing an executable, reading actual customer NAS files, calling registered Agents, authoring a Skill, or transmitting owner data.
  - Downloads only from the pinned *official* CDN if no private archive was supplied; verifies **exact known SHA256 before any extraction**. Fail closed on an updated archive until official identity is re-reviewed; never accept a random web mirror.
  - ZIP preflight checks for traversal, absolute, backslash or colon path, case collisions, symlink, oversized member, too many entries or ZIP bomb before extraction; finds exactly one candidate kit `SKILL.md`, fails on ambiguous layout.
  - Default mode is preparation only, **no Codex install**. `-InstallForCodex` opt-in copies files only. **Refuses to overwrite any existing kit install**, and cleans ephemeral private staging. Original ZIP retained in private directory unless the operator manages it; no vendor archive committed or uploaded.
- `.github/workflows/ugos-kit-codex-prep.yml`: isolated ephemeral first-party archive smoke test to **copy only** the official Skill folder into a temporary CI Codex skills location and reject overwrite. No Codex agent is launched, no `.mjs` files executed, no official checker claims. Deletes vendor archive/folder from CI scratch at end and publishes **no SDK artifacts**.
- This is a distinct installation usability/handoff validation, not another unsupported CLI catalog scan or synthetic test count expansion. Local entrant-owned Codex activation and creation still require the user to invoke them.

## Exact local owner commands
1. Review the official [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit), linked agreements, and pinned version/SHA. Use Windows PowerShell from a local trusted clone of this repository on `lead/ugreen`. The script does not modify tracked GitHub files.
2. From repository root, **prepare and copy** only after informed review:
   ```powershell
   .\tools\prepare_ugos_codex_kit.ps1 -InstallForCodex
   ```
   For inspection without installing, omit `-InstallForCodex`. For offline archive use, supply the separately verified `-ArchivePath` path; if its hash differs, stop and inspect changed official archive.
3. Restart Codex. Check that authentic official `uliya-skill-kit` is detected, invoke actual **feasibility check**, then ask the tool to **CREATE a fresh ProjectReady NAS Skill** from the existing repository's owner-authored idea, and afterward run its documented **CHECK** process. Use the detailed `docs/submission/G12_OFFICIAL_CREATOR_CODEX_RUNBOOK.md` first-party tool prompt. The tool's original instructions, not our hardcoded guessed flags, determine invocation.
4. Share with lead ONLY redacted evidence summary: official tool discovered, official creation actually happened, generated Markdown file SHA, checker PASS/WARN/NOT_RUN, any license and runtime uncertainties. Never publish vendor archive/source, raw chat logs, NAS names, data, tokens or SDK implementation internals.
5. The human entrant must separately review originality/IP/license disclosures and final PDF/ZIP, approve release explicitly, and receive a real Devpost submission receipt. GitHub Actions passing this smoke check is not any of those.

## Alternatives
- **A SELECTED**: pinned official ZIP, safe preflight, manual owner opt-in installation into standard Codex Skill discovery path, ephemeral smoke test. Improves actual next-step execution while preserving legal and security constraints; zero new monetary expense.
- **B REJECTED**: commit/rehost vendor ZIP or hidden internal SDK files to public GitHub to make future ChatGPT sessions run them; redistributes uncertain-license material and does not prove Codex official use.
- **C REJECTED**: mark the official Creator as used simply because an automated installer copied it or because our Python tests passed. False contest-provenance claim.
- **D DEFERRED**: vendor script execution, install to live NAS, or Devpost submission. Requires actual creator availability, authorized owner actions and consent; unnecessary for Round 1 to run NAS.

## Status & master accounting
This changes only developer-side preparations outside the official four-Markdown ZIP, not the 351-word PDF, package or submission. Until owner-side authentic creation, record `OFFICIAL_CREATOR_NOT_EVIDENCED`, `OFFICIAL_CHECKER_NOT_RUN`, `NAS_NOT_RUN`, `LICENSE_NOT_CLEARED`, `NOT_SUBMITTED`. Map to G1 UGR-D02/D03 BLOCKED and D16/D17 PARTIAL, without marking any day complete. Original Oct24 finite-day 100% /0 scheduled remaining; 10/25 G1 1.5h base + separate 1.5h reserve, real completion ETA unknown. Real working hours NOT_MEASURED, incremental spend 0.
