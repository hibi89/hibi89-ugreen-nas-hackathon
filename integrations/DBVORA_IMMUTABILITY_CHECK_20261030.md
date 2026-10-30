# DBVORA synthetic ledger immutability verification (2026-10-30)

UGREEN's optional `inspect_disposable_la_ledger` is called only on an already approved, disposable LA-generated `business.sqlite`. The independent P0 reader is supposed to be read-only. Before and after its invocation, the bridge compares the file's identity, size, mtime, and SHA-256 of **only that disposable SQLite file** (bounded at 2 MiB); mutation, replacement or unexpected size fails closed without claiming an integration PASS. Three focused negative tests cover mutation, replacement, and failure cleanup.

This detects normal mistakes but **does not guarantee atomic confinement against a malicious or concurrent replacement**. It cannot prove private DBVORA source execution, NAS authorization, or compliance with official Uliya Creator submission. No external user paths or private DB code are published, no vendor access is invoked, and official submission artifacts remain untouched.
