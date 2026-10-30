# Read-only preview without DBVORA, separate execution guard — 2026-10-30

HAE and SOVIA exact Git checkout readiness is sufficient to run the local
1–3-intent approval preview, because it never calls the private DBVORA reader
or performs synthetic SQLite writes. For approved disposable execution,
the operator UI now rechecks all **three** source identities before calling
the runner. If DBVORA is absent or not pinned, the one-time challenge is
consumed and no writes begin.

The source doctor's JSON separately reports preview readiness vs execution
readiness. No NAS/Uliya or customer data access occurs. This is a developer
workflow improvement, not evidence of real vendor integration.
