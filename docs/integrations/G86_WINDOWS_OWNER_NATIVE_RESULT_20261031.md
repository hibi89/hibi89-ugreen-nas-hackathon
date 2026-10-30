## FINAL UPDATE — owner Windows G86 regressions now ALL PASS (2026-10-31 KST)

User PowerShell after fast-forward of UGREEN from `21d34bf` to `832fd821` ran the corrected `tests/test_g86_native_backend_integrity.py`: **14 tests in 9.495 s, OK; process exit code 0**. This definitively resolves the previous 13/14 test failure caused by the double-escaped non-ASCII fixture. The previous owner Windows G86 native backend acceptance had already returned `G85_UGREEN_NATIVE_BACKEND_E2E_PASS`, `private_runner_integrity=G86_REVIEWED_GIT_BLOBS_MATCH`, exit 0. As no native production source was modified by this final test-only fix, G86 local acceptance gate is **PASS** on the verified pinned sources.

Latest GitHub full regression workflow `41101831695` on test-fix code `e587665fceb6f2c996d58585f0c18251d77b0682` is QUEUED on the check and NOT certified green. Real NAS/Uliya/Devpost/production remain NOT_RUN. Evidence is the owner's Windows execution output and prior G86 owner record below, not CI-native HAE execution.

# G86 Windows owner-native execution and regression fixture fix (2026-10-31 KST)

Evidence: user-supplied Windows PowerShell console. G86 native E2E from updated UGREEN repository was successful; separate G86 unit regression suite was not fully successful.

## Actual owner Windows output
- G86 private-runner/integrated native result: `status=G85_UGREEN_NATIVE_BACKEND_E2E_PASS`, `native_verified=true`, `private_runner_integrity=G86_REVIEWED_GIT_BLOBS_MATCH`, exit code `0`.
- Nested `G84_GENUINE_HAE_LA_SQLITE_E2E_PASS`; independent synthetic SQLite provenance verified, 2 business rows, HAE preview pending ID bound to user approval, persisted LA audit after restart, safe read-only recovery no duplicate.
- Temporary archive sha256: `4e8dd434818a7d80fa486be9dbaa82088a21b7e6797eaf477e497fec63aa068d`.
- Original HAE distribution not replaced, and NAS/Uliya/Devpost not run.
- Prior CP949 Windows Unicode decoding failure was not reproduced in this user-local native execution.

## Distinct unit test failure
- `Ran 14 tests in 10.437s`, **1 failure**, `test_non_ascii_git_gate_output_fails_closed`: expected `IntegrityRefused` absent.
- Root proven from GitHub source: test fixture constructed `b"\\xed\\x95\\x9c"` which is ASCII text containing literal backslashes, not UTF-8 Hangul bytes. Hence `decode("ascii")` succeeded, correctly not raising.
- Test-only fix (no source product behavior changed): `stdout=bytes([0xED,0x95,0x9C])`; commit `e587665fceb6f2c996d58585f0c18251d77b0682`. Independent byte-level probe confirmed `UnicodeDecodeError` for that byte vector; full corrected suite and exact-SHA CI still pending at evidence checkpoint.
- Do not classify 14/14 as PASS until the corrected test has executed. No need to rerun native synthetic HAE/LA/SQLite after a test-only fixture correction; native source remains unchanged.

## Next verification
- Update only the owner UGREEN checkout via `git pull --ff-only`; run the isolated G86 unit test script once. A result `Ran 14 tests ... OK` plus code-SHA matched public CI closes this one regression gate.
- Hardware NAS, official registered Uliya Expert, devpost release and production remain unverified; device/access/cost approval required for real NAS.

