# G113 — Owner-reaffirmed NAS FlowPilot 3.0 product goal (2026-10-31 KST)

## Product identity and acceptance priority
The owner explicitly reaffirmed: **A UGREEN NAS end user says in natural language "build X" / "I want to make X"; the agent should design the requested workflow, build a runnable implementation or an accurately constrained implementation plan, test it with prepared fixtures / temporary data, fix demonstrated defects, and guide that user step-by-step through the setup and operation.** The essential deliverable is not just an audit verdict, list of files, or textual generic advice; it is a **reproducibly tested, actionable workflow and personalized operator runbook**.

This is the current **long-range product acceptance goal**. Existing ProjectReady / file integrity / handoff audit are *subsystems and example workflow families*, NOT the product identity or the final product boundary. This clarification does not assert that the entire product currently exists or that the original contest Round 1 read-only Skill permission scope has been changed.

## Intended user-facing vertical slice
1. **Natural-language task:** user describes outcome, e.g. "Every day summarize CSVs arriving in an NAS folder and produce a report." Keep original request and explicit constraints.
2. **Clarify and authorize:** capture the exact approved source folder, input format, expected output and destination, scheduling, processing location/privacy, network requirements, write privileges and irreversible actions; ask only essential unanswered questions. No guessed path/authority.
3. **Capability check and solution design:** check actual supported Uliya/UGOS registered Experts and contracts; choose existing verified HAE / Lightning Azent components only after pinning their versions and callable interface; produce a typed workflow DAG and list unsupported steps explicitly.
4. **Build in a safe test environment:** instantiate a bounded, reproducible workflow implementation or executable local sandbox harness using pre-prepared synthetic fixtures. Preserve original source and customer data. Where native runtime is not available, produce a concrete installation recipe plus mock-bound test results, not a fabricated NAS run.
5. **Execute tests and repair:** verify expected output and edge cases (empty/invalid input, denied permissions, duplicate execution/idempotency, recovery, unsafe paths and privacy). Fix a demonstrated failure and rerun the affected test. Record fixture provenance, commands, exact SHA, PASS/FAIL/SKIP and mock vs actual platform provenance.
6. **Deliver step-by-step operator instructions:** prerequisites, chosen folder/permissions, installation/configuration actions, copyable workflow specification, data examples, how to start/stop/retry, sample vs verified real outputs, rollback and troubleshooting. Minimize user steps but never bypass explicit approval.
7. **Deploy/execute on actual NAS only after separate authorization:** explicit write/access/transfer/scheduling approval, verified supported platform contracts, and user-owned credentials. Record genuine runtime evidence independently of synthetic tests.

## Architecture choices
| Option | Description | Time/cost | Functional fidelity | Main risk |
| --- | --- | --- | --- | --- |
| A. Static read-only Skill + recipes | Explain a limited set of predefined steps; G50-G112 planner/auditor remains main product | Lower complexity / zero API spend | Inadequate for "make it, test it, then guide me" as a general outcome | User still builds/tests most workflows |
| B. Verified composer with test harness (recommended) | NL intake → typed capability-aware DAG → bounded builder → synthetic/local executor → test+repair → detailed user runbook. Uses audited HAE/LA selectively; Uliya Markdown Skill acts as supported front door only | More engineering, no paid services by default | Matches reaffirmed end-to-end goal without assuming arbitrary UGOS execution | Must prove real Expert contracts and keep generated operations in a separate authorized runtime |

**Recommendation:** B, implemented incrementally. The owner's product clarification fixes the goal, but does not by itself approve a scope-widening NAS write action, hidden background execution, external model calls, private source publication, or submission.

## Current truth and gaps (G112 source baseline)
- Existing Python offline planner/evidence and actual owner-local metadata fixture run are **not** a general workflow compiler/executor. ProjectReady evidence audit, review flags, local HAE/LA/SQLite bounded synthetic chain and G104 fixtures provide reusable components, not full arbitrary requested workflow acceptance.
- Exact G111 backend CI: 946 Linux tests / 941 PASS / 5 SKIP and Windows full verification PASS, at feature SHA `df38686025b336135cdd3aef1b44fab62eba0cfe`. G112 exact G103 private bundle recovered in ChatGPT Library; outer and nested ZIP/Skill/PDF digest parity proven. Genuine first-party G103 Checker **NOT_RUN**; live Uliya Experts / NAS **NOT_RUN**; Devpost **NOT_SUBMITTED**; release **HOLD**.
- **Gaps:** explicit typed user-goal-to-workflow IR, per-step verified runtime adapters, safe fixture and workflow test harness, discrepancy-led repair cycle, a genuinely generated user-specific runbook, robust test results traceability and real NAS proof.
- Do not copy HAE/LA private runtime into this public repository or into the official Skill ZIP without a separate verified license/rights and contract review. The official Round 1 ZIP remains Markdown-only; it must not claim bundled Python/Node executors or unsupported Uliya actions.

## Next implementation order (after existing owner design/rights gates)
- P0: select one demonstrable end-to-end example and pin its real inputs/outputs (CSV → derived report and user walkthrough), with explicit dry-run-only test contract. No paid API, no NAS writes.
- P1: build an offline typed task→DAG→fixture execution→assertion→result ledger→Markdown runbook vertical slice in the lead repository, with read vs write distinct, replay protections, and no changes to original Skill ZIP.
- P2: evaluate verified LA/HAE modules via existing interfaces against reinventing an executor; integrate only after exact SHA, data contract and rights checks.
- P3: confirm vendor Uliya 0.7.3 registered-Expert operations / permissions / response schema using legitimate owner-controlled environment. Compare real results with synthetic results; block unsupported steps.
- P4: if owner explicitly approves, run supported user-scoped operations on NAS, retain actual evidence, and separately obtain release/signoff for exact Round 1 Skill/PDF/ZIP.

## Acceptance tests / state discipline
A complete demo must show:
(1) user request -> structured goals/consent, (2) produced *specific* workflow spec, (3) an implemented local test harness with a real executed disposable fixture and expected output, (4) failing-case evidence and bounded correction, (5) readable, personalized step-by-step NAS instructions and recovery, (6) independently labeled real NAS outcome if actually run. **Do not label dry-run/mock success as NAS implemented/tested.** The long-range goal may exceed the 2026-11-16 16:45 KST official Round 1 Markdown-only permitted package; contest eligibility, already agreed license/rights and explicit external approvals still take priority.

## Handoff boundary
This G113 document only updates the product goal/implementation order and architecture comparison. It does **not** change runtime source, official `SKILL.md`, original artifacts or master progress; no new tests were executed, no customer data were accessed and no submission was made. New chat resumes with this clarification plus latest actual GitHub source, HANDOFF/STATUS/AGENTS/REQUIREMENTS. Keep the following separated in all claims: **designed / executable offline / tested synthetic / tested real NAS / released**.
