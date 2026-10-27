# G56 — FlowPilot mutation/transfer inflection rejection (offline only)

2026-10-27 KST · Baseline `c0400c05fd7849205fad11f867ead28e73150229` · `lead/ugreen`.

## Code-level issue
The existing read-only goal classifier detected bare English mutation commands like `delete`, `send`, `copy`, `download` but not common derived forms like `deleting`, `renaming`, `sharing`, `downloading`, `transferring`, `emailing`. As a result, a request such as “check files before deleting old copies” could enter the read-only plan path. Several Korean conjugations such as `지우고`, `옮겨줘`, and `지웁니다` were also not captured. No external runtime/NAS was invoked.

## Chosen low-risk fix vs alternatives
- Chosen: add explicit bounded inflections to the existing deny-first classifier before intent selection, with Unicode-safe word boundaries on English and minimal additions for Korean. Four new regression functions cover twelve English mutation cases, Korean inflections, five valid read-only cases, and no-scope denial. Scope stays in the offline Python planner.
- Deferred: replace the offline deterministic parser with a live LLM, machine translation, or a broad natural-language semantic engine. Those would add cost/privacy exposure and still cannot establish actual Uliya permissions. Explicitly do not claim exhaustive linguistic coverage.

## Verification and approval
Previous G55 [388/388 full offline tests PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40517777852) and seven source CI jobs passed. **G56 CI PENDING until observed after commit.** Existing `skill/flowpilot-nas/SKILL.md` and G52 owner-preview PDF/ZIP are unchanged; reviewed original Skill SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` remains the only static-checker evidence. Official Creator specifically for FlowPilot NOT_EVIDENCED; registered Expert Agents/actual NAS NOT_RUN; entrant exact-artifact release HOLD; Devpost NOT_SUBMITTED. 24-day plan 14 DONE/3 BLOCKED/7 NOT_STARTED. No payments, external data processing, or measured labor time.

Next: verify G56 CI and no source/ZIP drift. The highest-value external blocker remains authentic official Uliya Creator creation in a supported entrant-controlled Codex/Claude/WorkBuddy environment; separately review generated source and obtain entrant approval before any Devpost action.
