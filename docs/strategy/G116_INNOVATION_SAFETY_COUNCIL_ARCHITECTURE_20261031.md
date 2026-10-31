# G116 — UGREEN FlowPilot 3.0 safety-gated innovation design (2026-10-31 KST)

## Owner's updated product vision
Natural-language NAS workflow designer, verified builder and step-by-step guide. Three suggested innovations: (1) isolated sandbox and bounded self-repair, (2) proactive local monitoring/suggestions, (3) role-separated Architect / Coder / Security / QA council. Core candidate: **1+3**, with **2** as optional read-only, consented add-on.

## Decision table
| Candidate | Demo payoff | Support reality | Cost/security | Decision |
|---|---|---|---|---|
| A: three independent AI products/services | Three separate demos, difficult-to-explain cohesion | Requires three LLMs, persistent NAS watchers and privileged Docker | Higher failure/rate/permission complexity | Reject for current contest milestone |
| B: one bounded template builder with layered reviews and optional sandbox backend | Strong input→design→fail→repair→test→guide evidence | Existing G114/G115 typed IR and temporary fixtures can be verified now | Zero paid services; no privilege expansion | **Selected safe incremental baseline** |
| C: arbitrary LLM-generated scripts and background Docker/NAS control | Visually flashy | No verified official Uliya Expert support; forbidden to bundle scripts in contest Skill ZIP | High data loss, escape and rights exposure | Do not implement without exact external contract and owner approval |

## Target architecture (NOT all implemented)
User intent/constraints → Architect (typed DAG + capability map) → Security (allowed operations, owner scope, resource budget, prohibitions) → Builder (trusted template + version pin) → **genuinely isolated** ephemeral execution runner → QA (expected output + adversarial tests + receipts) → bounded correction (max attempts, only proven failures) → final step-by-step user runbook → **separate human NAS consent/approval** → platform adapter → real result readback/audit.

A proactive observer, if authorized and platform-supported, would be read-only, opt-in, rate limited, isolated from execution rights and send a suggestion only; it must not automatically modify files or launch containers.

## G116 code actually implemented
- \`tools/flowpilot_code_council.py\` provides *deterministic, role-separated* Architect, Security, Builder and QA reviews. These are NOT four LLM calls, genuine self-coding, or a Docker sandbox.
- Reuses existing G115 exact-intent compiler and disposable fixtures. A **test-only injected missing graph edge** produces an actual rejection; a tightly bounded repair function restores **only** a missing canonical template edge (never arbitrary code), then reviewers and real local fixture tests rerun. Max repairs=1; cannot authorize paths, commands, privilege expansion, mixed/unknown tasks, new template or release.
- JSON trace records role outcomes and evidence. CLI: \`python tools/flowpilot_code_council.py --goal "필수 파일 확인해줘" --inject-test-fault\`; \`python tools/flowpilot_code_council.py --goal "고객별 매출 보고서 만들어줘"\`.
- This is the review/recovery **foundation**, not "self-healing sandbox" shipped. \`docker_isolation_verified=false\`, \`container_sandbox_executed=false\`, \`actual_nas_verified=false\`, \`production_applied=false\`; release HOLD always.

## Real sandbox prerequisites and boundaries (not yet verified or deployed)
- A genuine container runner must be confirmed available/allowed on intended NAS, verified via official supported Skill capability and explicit user authorization. The developer runtime used here lacks Docker; no verified container execution is possible.
- Only tightly allowlisted, version-pinned operations; avoid executing arbitrary model-proposed scripts until an independently validated isolation architecture exists. If ever implemented: non-root uid, drop all capabilities, no host Docker socket, no host NAS mount or credentials, network disabled by default, read-only image plus dedicated writable disposable scratch, pids/memory/CPU/time quotas, seccomp/no-new-privileges, no privileged container, immutable inputs/outputs, fail-closed cleanup, code/image integrity and test receipt hashes.
- Passing a container test is NOT a security guarantee, NAS integration or production success. Prohibit reports of "safe production applied" until supported live platform operation and actual readback verification.
- Need validate pricing, runtime availability, unsupported native operations, owners' consent, official Uliya Skill 0.7.3 Checker and Rule-compliant Markdown-only ZIP separately. Do not embed Docker Compose, scripts or binaries inside official ZIP.

## Next priorities
1. Finish G115 and G116 exact-source Linux/Windows full regression, and preserve original G103 Skill/PDF and release hold.
2. Implement a **separate, optional sandbox contract probe** that requires exact platform Docker availability/security limits before enabling runner. If no supported Docker, retain local fixture demonstration and disclose limitation rather than fake it.
3. Add template-specific deterministic diagnostics/recovery cases (not arbitrary code execution); a visual timeline can show diagnosis, repair, QA and manually blocked NAS-apply gate.
4. Formal Uliya Skill capability/Creator and real NAS adapter permissions require owner trial activation approval. Official Round1 2026-11-16 16:45 KST remains Markdown-only PDF+ZIP; no demo video required for Round1.

## Exact approval boundaries
No authorizations for paid models, always-on NAS monitoring, Docker privileged service, NAS writes, public private source upload, force push, official submission, or external API transmission. The owner endorses the innovation concept; this checkpoint implements safe local non-privileged prototypes only.
