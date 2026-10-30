# G84 owner-local native backend acceptance (2026-10-31 KST)

Status: PASS for synthetic owner-local HAE -> Lightning Azent -> SQLite; NAS hardware and Uliya not verified. This records the user's PowerShell output, not an independent remote runner execution.

- HAE branch feature/axflow-mvp SHA: a6dcd41a3728399b8a64fc71a2436eb62c37a14a
- LA branch feature/lightning-azent SHA: 9cba6424dadf3fadb0ccd6ed10040e322c4a62fa
- UGREEN G83 verifier code SHA: 45e09ae506b5ffed11b143f1e0387a4e7bfc303a (temporary detached checkout only)
- HAE G82 web Git blob: ef093554750e28c0be7967d3a49e48649878d448
- Temporary packaged HAE+LA zipapp SHA256: b4135d61e3608835927dad62bc1532dd908a644932fe94e42a94f09116daa388
- Acceptance output status: G84_GENUINE_HAE_LA_SQLITE_E2E_PASS; exit code 0.
- Verified: approval bound to pending run ID, wrong ID and decline blocked, 2 exact SQLite CSV rows with source hash, LA audit persisted after restart, read-only recovery without duplicate writes.
- Original binary not replaced; temporary synthetic fixtures only. No actual NAS, Uliya, customer data, external provider or submission verification.

Owner-local path: C:\\Users\\haein\\OneDrive\\Desktop\\3개의 해커톤\\유그린 해커톤\\_g84_local. G84 runner resides at HAE/tools/g84_verify_ugreen_native.py. Its UGREEN checkout must be detached to G83 code SHA (runner currently pins that SHA, not later documentation commit). The original UGREEN checkout is unaffected.

Next: correct overly strict G83 SHA pin to allow verified descendant documentation commits while preserving immutable verifier source integrity; retain repeatable owner-local regression; prioritize backend and hardware-bound integration evidence before design/submission.
