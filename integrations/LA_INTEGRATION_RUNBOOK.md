# UGREEN ↔ Lightning Azent v0 integration

This branch stages a **UGREEN-side, read-only compatibility adapter**. It does not bundle HAE code or convert UGREEN's NAS Skill into a local workflow runner.

## Files
- `integrations/ecosystem_contract.py` — owner intent, scope, metadata consent and runtime permission gates
- `integrations/la_bridge.py` — LA `LAExecutor.preflight()` plan preview and `audit()` event/approval counts only
- `tests/test_la_bridge.py` — isolated fake-API contract tests (not live LA proof)
- `tools/verify_la_runtime_bridge.py` — opt-in smoke using an **owner-trusted local HAE checkout** and disposable synthetic SQLite files

## Local checks
From the UGREEN repository root:

```powershell
python -m unittest discover -s tests -p "test_la_bridge.py" -v
python -m unittest discover -s tests -p "test_ecosystem_contract.py" -v
python -m unittest discover -s tests -p "test_verify_la_runtime_bridge.py" -v
python tools/verify_la_runtime_bridge.py --la-package-root "C:\path\to\HAE\packages\lightning-azent"
```

The last command requires the owner to have independently checked out the actual LA package; no private code is fetched or copied by UGREEN. The optional smoke creates only disposable SQLite databases. It checks actual LA plan preflight and capability bounds, a literal read-only run, rejection of unapproved writes *before database creation*, one explicitly approved synthetic SQLite write, an approval-bound audit receipt without workflow values, independent SQLite row counting/integrity, and idempotent replay without duplicate business writes.
A passing **fake-LA smoke-harness test** proves this verifier detects rejected/duplicated writes; it is **not** evidence that the owner-installed private HAE LA package passed. A passing real-package smoke requires its own exact-source execution record. Runtime test PASS does **not** establish NAS access, Uliya Agent registration, document access, real customer safety, or external connector execution.

## Separation and release gates
- REA_APP is HAE's developer analysis workbench; **not** a runtime dependency.
- LA is a deterministic local engine; its current supported operations are not a NAS file-agent replacement.
- SOVIA and DBVORA are separately owned and are not embedded or claimed integrated.
- UGREEN official Skill and original submission artifacts remain unchanged.
- Until live registered Uliya Experts, effective permissions, processing location, and owner authorization are verified: `NOT_CHECKED`, not `READY`.
- No customer information, credentials, access tokens, or private-source copies may be committed to this public repository.
- The overall day-ledger metric 14/24 covers planned milestones, **not product or official submission completion**.


## Evidence classification
- `LOCAL_FAKE_HARNESS_PASS`: UGREEN tests against an explicitly simulated LA API and temporary SQLite; protects the *test harness*, not real HAE compatibility.
- `HAE_LA_SYNTHETIC_PASS`: only after `verify_la_runtime_bridge.py` completes with the actual private HAE package installed by the owner. No NAS or Uliya Agent proof follows.
- `NAS_ULIYA_NOT_TESTED`: remains the correct status until authorized official runtime evidence is obtained.
- A previous private HAE Actions run #40906163642 failed with no runner and no executable steps; it must not be reported as a runtime test failure or PASS.
