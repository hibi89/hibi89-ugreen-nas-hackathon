# FlowPilot 3.0 — G117 approved target architecture and implementation gates
As of 2026-10-31 KST; this document supersedes the roadmap portion of G116, not the original security/ownership evidence.

## A. Product promise and demo narrative
A NAS owner says "make this workflow" in natural language. FlowPilot (1) captures bounded requirements and consent, (2) compiles an inspectable DAG and checks real Expert capabilities, (3) builds a template-backed implementation, (4) runs disposable synthetic tests in a separate local test runtime, (5) for a supported platform, runs a restricted container with limited defect repair, (6) shows step-by-step user instructions and recovery, (7) only after user authorization can run an officially supported NAS action, and (8) can suggest future improvements based on separately opted-in read-only telemetry. **Never claim NAS success based on a fixture or container smoke receipt.**

## B. Architecture layers and trust boundaries
1. **Intent / dialogue:** Parse exact or explicitly confirmed intent and collect source, schema, destination, schedules, allowable operations and maximum cost. Do not infer access rights or claim unlimited natural language support.
2. **Architect:** A typed, versioned DAG with action categories (READ / COMPUTE / WRITE_NEW), input/output contracts, idempotency keys, error/rollback semantics and source provenance. G115 provides only two bounded templates.
3. **Security Council:** Re-derive canonical plan independently, deny unapproved folder/writes/transfers, symlinks, private file reads and unknown operations. G116 deterministic reviews are implemented; independent AI model council is not yet available.
4. **Builder:** Reuse pinned HAE / Lightning Azent or fully checked local templates where their exact interfaces and licenses are verified. The private modules are not copied to the public repo or official Skill ZIP.
5. **Sandbox:** Two-tier verification: existing disposable Python file fixtures *now* and **optional genuine Docker** only after an approved local runtime is present and a pinned, trusted image is locally available. Docker smoke test MUST be non-root, immutable rootfs, no network, no volumes, no Docker socket, no image pull, resource limits, no new privileges and a bounded timeout. A container smoke passing does **not** prove arbitrary workflows have been executed in a container nor prove host isolation fully.
6. **QA + repair:** Validate exact expected outputs, source immutability, sensitive input filtering, permissions, retries/idempotency, timeout and evidence receipts. Existing G116 repair is only a canonical missing-edge correction; general LLM error diagnosis/code repair and repeated container execution are roadmap work. Cap retries and always fail closed.
7. **Stepwise operator guide:** Show source/target mapping, test dataset, commands, exact supported NAS capability and permissions, how to confirm outputs, rollback, and separately labeled synthetic vs real evidence. Unverified actions must be explicitly marked.
8. **Uliya registered Expert adapter:** Only APIs genuinely supported by official Starter Kit / registered Expert capabilities; minimum permissions; no direct arbitrary runtime, shell or custom script inside official Skill. Native Uliya permissions/response formats NOT VERIFIED.
9. **Proactive intelligence:** Separate opt-in, read-only and narrowly scoped sensor layer; timestamp, provenance, sampling/rate limit, debounce and notification cap; proposals only, no automatic change. G117 implements deterministic alert evaluation of *caller supplied synthetic telemetry*, not a live monitor.
10. **Audit and recovery:** Event/receipt journal tied to exact template and execution SHA, unique run/approval ID, read-back status, customer-data protection, rollback. Completion label requires real platform confirmation for production.

## C. Alternatives and cost/quality
| Design | Complexity / cost | Demo quality | Security / maintainability | Decision |
|---|---|---|---|---|
| Arbitrary scripts in submitted Skill, Docker control through invented Uliya API | Appears fast but cannot meet documented contest contracts | Misleading | Ineligible and unsafe | Reject |
| Generic off-NAS server+LLM with always-on privileged Docker and watchers | High model/API/ops spend; difficult in limited trial | High potential but brittle | Broad attack surface and auth risk | Defer pending permission/product authorization |
| Modular typed workflow + deterministic council + temporary test data, optional pinned Docker adapter, opt-in suggestions | Zero new paid APIs today, staged cost | Evidence-driven fail/repair/guide demo | Inspectable, reusable, fail-closed | **Approved implementation strategy** |

## D. G117 actually added
- \`tools/flowpilot_isolation_contract.py\` creates a local Docker smoke-test plan for an exact allowlisted goal and a locally available **digest-pinned** \`python@sha256:...\` image. Default does **not** invoke Docker. Optional explicit \`--approve-local-docker-smoke\` performs only a fixed Python environment smoke check with no mounts/pulls/network and strict resource/security flags. It never runs arbitrary scripts, actual workflow DAG or NAS; these functions remain unverified until a real authorized environment supports them.
- \`tools/flowpilot_proactive_advisor.py\` consumes **caller-supplied synthetic** disk-use %, repeated-error count and backup age to propose human-reviewed improvements. Default disabled, never scans NAS or background runs. Rejects unrecognized private fields and out-of-range telemetry.
- New regression tests focus on denied unsafe requests, no permission=no Docker call, pinned image, fixed no-network argv, receipt spoofing, subprocess timeouts, explicit opt-in and strict suggestion-only behavior. Exact source CI is the acceptance gate; a mocked subprocess is NOT evidence of Docker actually running.

## E. Official 2026 hackathon vs hardware Docker
UGREEN's official hackathon rules require \`SKILL.md\` plus permitted Markdown references in ZIP; custom scripts, executable runtimes and unauthorized NAS resources are unsupported. Official PDF has 10 required substantive answers within 500 English words, ZIP maximum 10 MB. Round1 NAS evidence not required. Official deadline Nov 15 2026 23:45 PST = **Nov 16 2026 16:45 KST**. Finalists get assigned remote NAS testing day.
Official UGOS documentation says some consumer NAS models support Docker, but this does **not** establish whether the hackathon's registered Uliya Expert API can create/run containers. The Skill must not claim Docker execution without an actually documented supported Expert contract.

Official sources (for human review):
- https://ugreenhackathon.devpost.com/rules
- https://ai.ugreen.com/pages/hackathon-starter-kit
- https://ai.ugreen.com/blogs/knowledge/docker-docker-compose-ugreen-nas
- https://support.ugnas.com/detail/article/en-US/236

## F. Implementation stages / acceptance
| Phase | Measurable result | State |
|---|---|---|
| G114 natural-language customer CSV → local execution→test→guide | 953 Linux total and Windows full regression, 0 FAIL | VERIFIED |
| G115 two typed templates with disposable fixture execution | 964 Linux total and Windows full regression | VERIFIED |
| G116 deterministic Architect/Security/Builder/QA with bounded graph correction | 975 Linux total and Windows full regression | VERIFIED |
| G117 pinned Docker smoke contract + opt-in synthetic signal advisor | New tests; verify exact new source SHA and CI | IMPLEMENTED, CI pending until checked |
| G118 controlled containerized *workflow* test with strict fixtures and evidence | Must really execute in a trusted container; no mocks counted as actual | NOT VERIFIED |
| G119 true input/output repairs, persistent consent + separate trusted telemetry watcher | Idempotency/recovery and actual supplied event attestations | NOT IMPLEMENTED |
| Genuine Uliya Expert/NAS + first-party G103 check | Exact owner/private skills, current vendor kit, authorization, real result readback | NOT_RUN / RELEASE HOLD |
| Round1 submit | Entrant rights, PDF/ZIP exact-byte signoff, explicit submission instruction | NOT_SUBMITTED |

Never alter G103 owner-private bytes, canonical older Skill, official ZIP/PDF, or begin 3h NAS activation without separate authorization.
