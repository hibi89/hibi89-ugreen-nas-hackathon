# G86 verified-private-helper local backend admission gate — 2026-10-31 KST

Public code commit: `3fb7c11570aeba2cc95ae7b911105eeda673a58d`; latest main branch `lead/ugreen` at checkpoint. Functional CI [41099593530](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41099593530): **810 total / 805 PASS / 0 FAIL / 5 SKIP**. CI executes synthetic git/receipt fixtures, NOT actual private HAE/LA, Uliya or NAS.

## Failure addressed
G85 wrapper forwarded `native_verified=true` on process returncode=0 and a matching PASS string even if private script provenance or SQLite audit proof was absent. An owner-local misconfigured/modified script could misstate runtime verification.

## Checked before private execution
- Git repository root matches the selected HAE checkout; exact tracked HEAD blob and working bytes of `tools/g84_verify_ugreen_native.py` and `tools/package_hae_integrated.py` match reviewed immutable identities. Docs-only private HAE commits remain permitted; a changed helper is rejected.
- Owner explicitly opts into synthetic-only execution. No private sources are copied into the public repository; no external NAS or API calls.
- Process exit code 0; strictly unique JSON keys; no NaN; fixed receipt keys only; exact backend source identities; 64-digit SHA256; type-safe SQLite exactly 2 rows and source-provenance, pending approval and post-restart read-only no-duplicate fields. This checks a trusted local helper's receipt, not cryptographic third-party NAS proof.
- Pass output remains `G85_UGREEN_NATIVE_BACKEND_E2E_PASS` for CLI compatibility, and now adds `private_runner_integrity=G86_REVIEWED_GIT_BLOBS_MATCH`.
- Failures never turn into success; private source hash mismatch produces `G86_PRIVATE_RUNNER_INTEGRITY_REFUSED`.

## Test and evidence boundaries
The intermediate `060a98ba` public regression failed one newly edited fixture test from a double-escaped newline. Fixed in `3fb7c115`, whose full functional CI passed. Previous owner-local G85 real native synthetic HAE→LA→SQLite PASS remains independently documented in `G85_OWNER_LOCAL_NATIVE_PASS_20261031.md`. The modified G86 wrapper has NOT yet been exercised against the owner's actual private executable in this session.

## Next
Owner uses updated UGREEN checkout with existing clean private HAE and LA repositories; one explicit synthetic-only local rerun proves the strengthened entrypoint has not broken real integration. Hardware NAS/Uliya Expert, real provider permission and official submission remain separate, owner-authorized checks. Canonical contest Markdown Skill and original shipped binaries unchanged.
