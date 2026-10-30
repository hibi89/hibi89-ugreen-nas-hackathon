# Exact Git source readiness — UGREEN local only

Run: powershell -NoProfile -File tools/run_four_source_doctor.ps1

The diagnostic checks each exact pinned HAE, SOVIA and DBVORA Git checkout
without importing private code, opening customer files or invoking NAS.
It returns only redacted source status/error codes and expected SHA references.
READY_FOR_LOCAL_SYNTHETIC_PREVIEW means Git source readiness, not actual
four-source execution success, NAS/Uliya access or official release approval.
Explicit synthetic execution remains a separate owner action.
