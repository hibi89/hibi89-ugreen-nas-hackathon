# Owner-local printable HTML report / approved action timeline

The operator-selected local folder workflow can now export both a redacted JSON
and an offline printable HTML report. Each numbered step shows the *allowlisted*
read-only action, conservative review/block state and counts by state. The
viewer constructs report text only from sanitized server result fields; user
folder paths and original file names are never included. Both downloads are
disabled until an explicitly approved local metadata inspection succeeds,
and invalidated when the operator edits the scope.

No extra OS calls are needed to download or view the report. It is a local
metadata audit, NOT a NAS/Uliya execution claim or official Creator proof.
