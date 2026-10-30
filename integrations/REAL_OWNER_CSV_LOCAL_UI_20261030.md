# FlowPilot 3.0 — Real owner CSV local workflow

The Windows one-click UI has three clearly differentiated local capabilities:
(1) generated synthetic OS file-metadata demo, (2) owner-selected trusted
local folder metadata-only checklist and redacted report, and (3) owner-selected
trusted local CSV files for actual content aggregation into a new CSV with
SQLite audit.

**Owner CSV content processing is opt-in**: the user first explicitly allows
metadata preflight (absolute local folder, 1–5 baseline CSV names and new
non-overwriting output filename). A separate consent + one-time approval token
is required before reading the CSV file contents, creating the new output
file in the chosen LOCAL directory or recording the temporary SQLite audit.
No network upload, NAS, Uliya, HAE/LA, SOVIA or DBVORA execution occurs.
The source-checking layer refuses symlinks/UNC roots, and existing CSV engine
bounds per-file bytes and total rows, validates grouping keys and Decimal
amounts and checks source content SHA during aggregation.

The output itself contains owner-selected data and is downloadable only
after approval; the HTTP result carries **counts and SHA only**, no paths,
original filenames or owner row data. Changes in source metadata between
preview and execution refuse execution; the output is exclusively created
(no overwrite). One approval can execute only once; new workflow needs app
restart after a write attempt. Audit database is confined to temporary
local app storage, and is removed on app shutdown.

This is not a UGREEN NAS runtime proof or official creator submission.
Full NAS/Uliya gate remains HOLD.
