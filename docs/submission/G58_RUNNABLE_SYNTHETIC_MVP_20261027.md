> **2026-10-27 G58 2026-10-28 EXECUTABLE MINIMUM VERIFIED:** [code SHA `574b314e`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/commit/574b314ea34559bb5e9dd50e270a134f9451be4d). `python tools/flowpilot_mvp_cli.py` runs owner-visible natural-language goal→guarded plan→synthetic evidence JSON; five fixture cases **5/5 PASS** and 12/12 new CLI tests PASS, total **416/416 repository Python regressions PASS** in [CI 40526183128](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40526183128). All **5/5** source workflows successful: round1 draft PDF/ZIP 40526183224, offline readiness 40526183144, master progress 40526183385, closeout sync 40526183665, FlowPilot 40526183128. These are **offline synthetic only**, NOT actual NAS, registered Agent, official FlowPilot Creator, or submission. Owner independently handles **HAE, Lightning Azent (LA), REA_APP**; no repo changes there. Frontend, UI polish, platform integrations and non-MVP hardening explicitly postponed. Canonical Skill original SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` and G52 PDF/ZIP unchanged. Official Creator NOT_EVIDENCED; real NAS NOT_RUN; rights/release HOLD; Devpost NOT_SUBMITTED. 24-day plan 14 DONE, 3 BLOCKED, 7 NOT_STARTED (not product %), work hours unmeasured. Next: verify actual authorized official Creator output against G57 and prepare entrant-reviewed exact Round1 artifacts; no automatic submission.

# G58 — One-day runnable MVP execution contract

Owner request date: 2026-10-27 KST. **Target: 2026-10-28 KST** for a demonstrable minimum working unit. Owner directly handles **HAE, Lightning Azent (LA) and REA_APP**; they are outside this workstream. Do not mutate their repos/branches.

## Concrete product-first deliverable
A real executable **offline synthetic** text-CLI on top of `src/flowpilot/pipeline.py` and `src/flowpilot/evidence.py`. It must accept a natural-language goal and one of five committed synthetic NAS-like scenarios, construct the bounded expert plan, apply claimed-fixture evidence, and emit deterministic machine-readable JSON with result, planned registered-expert steps, per-file statuses, blockers and strict release HOLD. The CLI uses Python standard library and no frontend or web app.

### Run once, no setup other than Python 3.11
```bash
python tools/flowpilot_mvp_cli.py
python tools/flowpilot_mvp_cli.py --scenario missing_required_synthetic
python tools/flowpilot_mvp_cli.py --scenario conflicting_versions_synthetic
python tools/flowpilot_mvp_cli.py --scenario truncated_or_denied_synthetic
python tools/flowpilot_mvp_cli.py --scenario symlink_unknown_synthetic
python tools/flowpilot_mvp_cli.py --request "납품 파일 확인해줘"
python tools/flowpilot_mvp_cli.py --request "파일 옮겨줘"
```

## MVP acceptance gate
- Five fixed fixtures: complete -> two `PRESENT` with overall `NEEDS_REVIEW` (not NAS ready); missing -> `MISSING`/`BLOCKED`; alternative version -> `VERSION_REVIEW`; denied or truncated -> `NOT_CHECKED`; unknown symlink -> `NOT_CHECKED`.
- English and Korean intent classifier, consent questions, write-mutation denial, no fallback to unsupported experts.
- CLI JSON outputs `actual_nas_verified: false`, `registered_agent_invoked: false`, `official_creator_execution_verified: false`, `release_gate: HOLD` in ALL cases.
- GitHub Actions actual exact-source full test PASS, plus five-case CLI smoke PASS. Frontend, polish, cross-platform packaging and unverified connectors deferred to subsequent stages before submission.
- All existing source Skill, G52 original draft PDF/ZIP and prior hackathon artifacts preserved. No official UGOS Creator tool invoked here. Round 1 can use a Markdown Skill and English proposal only after actual official Creator evidence and entrant release rights. Live NAS belongs to later official finalist testing, not tomorrow's claim.

## Non-goals / independent blockers
This command is deliberately **not** official NAS execution, official Creator proof, Devpost submission, an external production deployment, a reusable n8n workflow runtime, or a frontend. Owner's original long-range n8n-like NAS vision is broader. CLI demo readiness and contest-eligible Skill readiness are different gates. Official Creator output and entrant approval remain independent HOLDs. MVP does not establish a product completion percentage.

### Next iteration after executable MVP
Compare accepted owner blueprint, implement bounded missing functions with working input/output, fix adverse cases from tests; then improve front-end, compatibility and final submission packaging as their gates become relevant. No empty documentation-only work at the expense of an executable test.
