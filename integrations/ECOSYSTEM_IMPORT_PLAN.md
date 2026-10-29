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
- [x] Created isolated integration branch.
- [x] Located source repositories and HAE README architecture boundaries.
- [ ] Review source-level interfaces and license compatibility.
- [ ] Implement independent UGREEN adapters with mocked contract tests.
- [ ] Connect approved real interfaces and run cross-project E2E.
- [ ] Verify actual NAS runtime only with owner authorization.

**Completion:** staging created; no source import or E2E completion is claimed.
