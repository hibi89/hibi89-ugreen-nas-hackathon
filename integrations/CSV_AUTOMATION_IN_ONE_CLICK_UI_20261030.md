# One-click actual generated CSV automation

The one-click local UI now offers real generated-only CSV aggregation and
SQLite audit recording. Source: two small synthetic monthly sales CSVs
in an auto-created temporary folder. User selects the bounded output name,
previews the deterministic workflow, then separately approves a write into
the *temporary* folder. The output is downloadable only after the audit
receipt and output SHA-256 match. No user file paths or customer data accepted.

This invokes the existing real public FlowPilot CSV engine; it does NOT
invoke HAE/LA/SOVIA/DBVORA, NAS, Uliya or the official Creator. Release HOLD.
