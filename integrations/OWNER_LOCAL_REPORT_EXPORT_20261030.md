# UGREEN local file checklist — inspectable per-step report (2026-10-30)

Owner-local Workbench now returns an explicit ordered bounded action plan
before consent and structured per-step states after a real local OS `lstat`
metadata inspection. All items are identified by **numeric index only**,
never filenames or raw filesystem references. Raw result fields are dropped,
and unexpected item states or forged indexes are refused.

The localhost UI displays per-step counts and permits an operator to export
a redacted JSON report after approved inspection. The download is created
entirely in the browser from the safe structured result; no additional file
read or NAS access is performed. Editing any input clears the previous
approval, stage display and download. No data is uploaded.

The user-selected LOCAL folder path must be trusted and non-NAS/non-mounted
network storage. No file bytes, directory enumeration, Uliya NAS or private
HAE/SOVIA/DBVORA invocation is involved in this pilot. Release HOLD.
