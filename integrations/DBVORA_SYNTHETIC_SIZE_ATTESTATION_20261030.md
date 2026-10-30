# DBVORA disposable SQLite size-attestation guard — 2026-10-30

Evidence-critical correction: after the injected DBVORA P0 reader completes,
the UGREEN bridge now compares the report's exact integer `size_bytes` to
the same disposable business.sqlite file's locally observed `st_size`.
This blocks a reader that returns a different database's size or a forged
size value while otherwise satisfying the expected metadata contract.

Two negative synthetic tests cover incorrect byte counts and boolean-like
size claims. The pre/post identity, mtime and SHA-256 checks remain separate.
No private DBVORA source was copied into UGREEN. The check is about an
isolated generated SQLite, not a guarantee against a malicious filesystem
race and not evidence that real NAS/Uliya has been executed.
