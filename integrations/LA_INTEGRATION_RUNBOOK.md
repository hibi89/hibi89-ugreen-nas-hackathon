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
python tools/verify_la_runtime_bridge.py --la-package-root "C:\path\to\HAE\packages\lightning-azent"
```

The last command requires the owner to have independently checked out the actual LA package; no private code is fetched or copied by UGREEN. It exercises synthetic local plan preflight, a literal-only run, and read-only audit in a temporary directory. Runtime test PASS does **not** establish NAS access, Uliya Agent registration, document access, real customer safety, or external connector execution.

## Separation and release gates
- REA_APP is HAE's developer analysis workbench; **not** a runtime dependency.
- LA is a deterministic local engine; its current supported operations are not a NAS file-agent replacement.
- SOVIA and DBVORA are separately owned and are not embedded or claimed integrated.
- UGREEN official Skill and original submission artifacts remain unchanged.
- Until live registered Uliya Experts, effective permissions, processing location, and owner authorization are verified: `NOT_CHECKED`, not `READY`.
- No customer information, credentials, access tokens, or private-source copies may be committed to this public repository.
- The overall day-ledger metric 14/24 covers planned milestones, **not product or official submission completion**.
