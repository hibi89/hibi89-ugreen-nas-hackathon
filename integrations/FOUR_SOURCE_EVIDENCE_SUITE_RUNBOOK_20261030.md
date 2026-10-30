# Four-source all-intents local evidence bundle (2026-10-30)

One command runs the bounded 1-, 2-, and 3-intent synthetic verifier separately.
Default is preview-only. Explicit -ApproveDisposableSynthetic is required for disposable SQLite writes.
All input fixtures are auto-generated temporary files; no customer content, NAS, Uliya or external API.

Windows commands:

    powershell -NoProfile -File tools/run_four_source_suite.ps1 -OutputDir C:\temp\ugreen-proof-preview-new
    powershell -NoProfile -File tools/run_four_source_suite.ps1 -ApproveDisposableSynthetic -OutputDir C:\temp\ugreen-proof-execution-new

Output: index.html, three HTML evidence pages, three sanitized JSON receipts, and manifest.json
with SHA-256 hashes for the seven other files. The output folder must be a new absolute
path with an existing parent. Existing output is never overwritten.

The bundle labels approved PASS as OPERATOR-REPORTED SYNTHETIC, not an attestation
or proof of actual NAS or Uliya access. Private HAE and DBVORA are not imported by public CI.
No submission, rights clearance or Creator provenance is inferred. Release HOLD.
