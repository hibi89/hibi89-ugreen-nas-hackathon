# FlowPilot ecosystem integration staging

Branch: `feature/flowpilot-ecosystem-integration` (based on `lead/ugreen`).

## Verified source locations
- `hibi89/HAE` (PRIVATE): `tools/rea-app/` is the REA_APP development analysis tool; `apps/ax-flow/` is the HAE app; `feature/lightning-azent` and `feature/axflow-mvp` exist. Do not assume REA_APP findings have already been incorporated into LA.
- `hibi89/SOVIA_sovereign` (PUBLIC): separate agent behavior/risk auditing product.
- `hibi89/DBVORA` (PRIVATE): separate database observability/backup product.
- `hibi89/hibi89-ugreen-nas-hackathon` (PUBLIC): original Skill and submission artifacts stay untouched.

## Integration boundaries
1. Inspect the exact source files, interfaces, licenses, tests and dependency versions before importing any code.
2. Never copy private repository source, secrets, credentials, proprietary datasets or non-public design artifacts into this public repository without explicit owner approval for the specific files. Prefer clean-room, UGREEN-specific adapters based on approved interfaces.
3. Preserve explicit owner consent before NAS data access. Read-only scoped metadata is the default. Actual UGOS/Uliya Expert calls require verified permissions and separate owner activation approval.
4. HAE: bounded natural-language intent / plan. LA: validation and deterministic execution. SOVIA: optional audit findings. DBVORA: optional database metadata. REA_APP: development analysis only, never a runtime dependency.
5. No cross-repository merges, vendoring, git submodules pointing to private sources, live NAS calls, external submissions or paid services in this staging phase.

## Work status (2026-10-30)
- [x] Created isolated UGREEN integration branch, preserving the original `lead/ugreen` source.
- [x] Reviewed actual HAE `LAExecutor` interfaces (`preflight`, `audit`, `capabilities`, `execute`) and versioned `azent.api.v0` contract.
- [x] Implemented independent UGREEN consent gates, LA read-only adapter, capability fail-closed guard, and actual FlowPilot natural-goal preview composition.
- [x] Added offline contract and orchestration tests on public UGREEN feature branch; isolated adapter CI at `374dd990`, `dc5b97d5`, and `54db9746` passed.
- [ ] Verify latest natural-goal integration CI run (`4383ae00`) before claiming its new tests pass.
- [ ] Run **real** LA package cross-repository E2E. An isolated **private HAE** verification branch (`verify/ugreen-la-bridge-20261030`) was created without altering HAE's `feature/lightning-azent`; workflow #40906163642 failed before usable test steps/logs, so evidence is **NOT_RUN/UNVERIFIED**.
- [ ] Verify UGREEN registered Uliya/NAS runtime and processing location only with owner authorization.
- [ ] Review separate SOVIA and DBVORA interfaces before proposing any actual adapter; no private-source imports.

**Release truth:** UGREEN submission Skill/PDF/ZIP unchanged, no NAS or registered expert execution, no actual LA runtime integration success yet. The 14/24 master ledger measures **calendar work items**, not product completion. The private HAE verification branch contains a CI-only workflow; no private HAE code is moved to this public repo.
