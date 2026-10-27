# G53 — Official Uliya Creator provenance gate (FlowPilot only)

Date: 2026-10-27 KST. **Status: genuine Creator generation NOT_EVIDENCED; no Devpost submission.**

## Why the remaining gate matters
UGREEN's [official rules](https://ugreenhackathon.devpost.com/rules) require an entrant's *newly made* contest Skill to be developed using the **official UGOS Skill Creation Tool**. [Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) describes a supported assistant (Codex, Claude, WorkBuddy), installing `uliya-skill-kit` and following feasibility, **creation**, and review/check steps. A first-party static checker run is **not proof of the assistant-driven creation process**. No working NAS is needed for Round 1; Round 2 is separate.

This repo independently has a valid FlowPilot source SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` and first-party Uliya static-checker 0 errors/warnings/info: [verified workflow 40505339535](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40505339535). Its 10-question owner-review PDF/ZIP was independently verified at G52. **The 2026-10-24 ProjectReady Codex Creator history is NOT FlowPilot Creator history.**

## G53 engineering deliverable and limitations
`tools/g53_flowpilot_creator_gate.py` and `tests/test_g53_flowpilot_creator_gate.py` add a *fail-closed* local provenance audit. The CLI accepts only `--generated-skill` and `--operator-receipt` for a regular UTF-8 `flowpilot-nas/SKILL.md`. Hashes must bind the exact generated file, reported checker result and pinned vendor kit identity. A differing source returns `GENERATED_SOURCE_DIFFERS_REVIEW_REQUIRED`; any missing or outdated checker data returns a specific HOLD status. A fully matched operator declaration returns `SOURCE_MATCHED_OPERATOR_ATTESTATION_ONLY`, **not** independently verified Creator execution and **never** release approval. CI with no receipt explicitly expects `CREATOR_NOT_EVIDENCED`/HOLD. A self-reported JSON record is not a reliable trace of which actual assistant invoked the tool.

## Future one-time supported-Codex run, only when owner intentionally uses the official kit
1. In the entrant's own supported Codex desktop/workspace environment, retrieve the official archive **from the official Starter Kit link**, inspect the applicable policies, version and archive hash. Historical official `uliya-skill-kit-0.7.3-en.zip` SHA256 is `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`; if the official kit is newer, log the real version and require separate audit rather than rewriting its hash.
2. Install it locally in the supported assistant's skills directory following official instructions. Do NOT publish official vendor code or install unknown scripts blindly; never put vendor code in the contest ZIP.
3. Copy the original entrant-owned current `skill/flowpilot-nas/SKILL.md` and read `docs/architecture/UGREEN_NAS_NATURAL_LANGUAGE_WORKFLOW_OWNER_VISION_20261027.md`; treat these as requirements/specification, not pre-approved Creator output. Keep originals and G36/G37/G46 immutable.
4. Invoke **the actual discovered vendor Creator Skill** in Codex, first asking it to verify the idea's support. Require official Creator to generate a *new FlowPilot* Skill in a separate local scratch folder using those requirements. Never claim that merely reviewing/checking the old file fulfilled creation.
5. Ask the official tool to review/check the generated output. Compare exact source SHA, catalog-supported Expert Agent calls and permissions, guardrails, disclosure and any official diagnostics. Even if generated output is syntactically valid, owner signoff is required for behavioral differences.
6. Return **redacted** evidence of tool discovery, official creation, official check, input specification identity, output SHA and actual exported generated Markdown. No raw private transcripts, SDK code, credentials, personal paths or customer files.
7. Run `python tools/g53_flowpilot_creator_gate.py --generated-skill <local-generated-skill-file> --operator-receipt <sanitized-json>` for bounded hash comparison. Any result is only a *local source review*. Actual Creator invocation must be evidenced separately by the supported assistant and accepted by the entrant. If new generated source differs, review and formally adopt it, re-run exact-source official checker, redo all PDF/ZIP build checks and record new SHA; never substitute automatically.

### Ready-to-paste official Codex task
```text
Use the installed, genuine UGREEN official "uliya-skill-kit" Skill Creation Tool from the Hackathon Starter Kit, NOT a generic Skill builder. Show the actual discovered kit name, source/version and official invocation before touching source. If it is not available, stop and say TOOL_NOT_AVAILABLE.

Project: hibi89/hibi89-ugreen-nas-hackathon branch lead/ugreen. Read skill/flowpilot-nas/SKILL.md and docs/architecture/UGREEN_NAS_NATURAL_LANGUAGE_WORKFLOW_OWNER_VISION_20261027.md as an entrant-authored behavior specification. Do not copy old ProjectReady as generated FlowPilot output. First conduct the official feasibility/capability check; then have the official Creator CREATE a newly authored flowpilot-nas SKILL.md in a separate local scratch folder. Do not alter canonical source or historical deliverables yet.

Behavior: owner-authorized scoped NAS read-only natural-language intent planner for handoff, required file check, ambiguous version review and separately consented document summary; exact folder, checklist and owner consent; only supported registered Uliya file-agent and document-agent with actual observable return refs; zero fabrication for denied/partial/empty evidence; NO arbitrary scripts, filesystem writes, external SaaS, private credentials or unsupported NAS commands.

Use the official Creator's documented CHECK/review and fix only actual findings. Retain honest NOT_VERIFIED for real NAS, effective Agent permissions, data-processing location and owner release. Report tool discovery/generation/check steps actually performed, version+archive SHA, output file SHA256, source diff, warnings, and whether the generated output is safe to adopt. Preserve entrant ownership and AI/tool/license disclosures. Do NOT push, publish, submit, start a NAS trial or claim official Creator success if only a static checker was executed. Return a sanitized record, no vendor source or personal data.
```

## Sanitized operator receipt shape (local only; not auto-issued by CI)
```json
{
  "kit_sha256": "cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3",
  "official_tool_loaded": false,
  "generation_performed": false,
  "generated_skill_sha256": "<actual-generated-SKILL.md-sha256>",
  "checker_skill_sha256": "<exact-file-sha256-verified-by-official-checker>",
  "checker_status": "NOT_RUN",
  "checker_errors": -1,
  "checker_warnings": -1,
  "checker_info": -1
}
```
Those fields are **placeholders until the real supported assistant generates them**. A fake declaration cannot establish compliance. The gate deliberately refuses release even when values report a PASS.

## Current acceptance / next stage
- G53 source + 9 negative/positive synthetic tests: CI PENDING until verified.
- Official Creator generation for FlowPilot: NOT_EVIDENCED.
- Exact existing static checker: PASS on unchanged SHA only.
- Real NAS registered Experts: NOT_RUN; Round1 does not require them.
- Rights/license and entrant exact submitted artifact approval: HOLD.
- Devpost: NOT_SUBMITTED; deadline **2026-11-16 16:45 KST**.

Never infer a product completion percentage or award probability from static/offline tests.
