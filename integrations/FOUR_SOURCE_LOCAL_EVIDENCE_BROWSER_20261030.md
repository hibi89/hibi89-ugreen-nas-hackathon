# UGREEN local operator evidence browser, 2026-10-30

The operator UI now exposes only a fixed allowlist of generated synthetic
artifacts via /evidence/index.html, /evidence/proof-{1,2,3}.html,
/evidence/proof-{1,2,3}.json, and /evidence/manifest.json.

Evidence routes return 404 until the approved local 1–3 intent suite reports
a completed sanitized output bundle. Arbitrary paths, traversal, symlinks and
large evidence files are refused; each HTML/JSON proof SHA-256 must match
the manifest. A modified report is not served. Browser offers a report link
only after an approved execution with an output directory.

These artifacts are still operator-generated synthetic claims, NOT cryptographic
attestation of actual private sources or real NAS/Uliya execution. No customer
files are read and the release gate remains HOLD. The loopback server does
not implement real NAS or official Creator submission.
