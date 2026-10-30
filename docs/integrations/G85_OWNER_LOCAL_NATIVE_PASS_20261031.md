# G85 owner-local genuine HAE + Lightning Azent + SQLite backend acceptance
Date: 2026-10-31 KST. Evidence type: user-provided Windows PowerShell stdout, reviewed in chat; not a GitHub Actions native engine result.

## Actual outcomes
- Private G85 Git fixture regression test: `Ran 5 tests in 5.513s`, `OK` (5 passed).
- UGREEN-main native acceptance: `G85_UGREEN_NATIVE_BACKEND_E2E_PASS`, `native_verified: true`, exit code `0`.
- Private runner nested acceptance: `G84_GENUINE_HAE_LA_SQLITE_E2E_PASS`.
- Private engine's reviewed web Git blob: `ef093554750e28c0be7967d3a49e48649878d448`.
- LA source commit: `9cba6424dadf3fadb0ccd6ed10040e322c4a62fa`.
- UGREEN public verifier baseline commit: `45e09ae506b5ffed11b143f1e0387a4e7bfc303a`.
- Disposable zipapp SHA256 reported: `2697c20cfebdcb52ae660e534b0a644b0e3ec47c3947cb77bce720eecb9d3fcb`.
- Verified checks: G82 pending_run_id bound to explicit approval; declined/wrong-ID write refusal; independent SQLite exact synthetic CSV payload/provenance and two rows; persisted LA audit after server restart; read-only reconciliation without duplicate writes. Original distribution binary not replaced.
- Distinct public repository CI at G85 code commit `7e0f48b278ef559e52960e1c50e8a3429db94a0e`: functional regression run 41097309612 SUCCESS; offline readiness run 41097309367 SUCCESS. Both public CI workflows are NOT the private native E2E.
- No actual NAS hardware or Uliya expert execution, Devpost submission, hosted production, or real customer data. All remain unverified/not done.

## Reproduce (owner-authorized, on existing checked-out sources)
From clean updated private HAE checkout run `python tools/test_g85_native_integrity.py`.
From UGREEN main checkout run `python tools/run_g85_native_backend.py --hae-root <HAE_CHECKOUT> --la-package <LA_CHECKOUT>/packages/lightning-azent --execute-synthetic-only`.
Explicit consent and private source access are required. No private source archive may be committed to this public repository.

## Next
Native local backend G85 integration gate COMPLETE for pinned sources; isolate the next backend external integration tasks, but never treat local synthetic PASS as actual NAS/Uliya PASS. Owner authorization is required for official Expert/NAS actions.
