# FlowPilot Universal — isolated offline P50 candidate

This is a separate local-only product: NOT the UGREEN competition Skill. There is no Uliya/NAS Expert invocation, network code, or original source import. The original lead/ugreen branch and official submission are untouched.

## Input contract (schema v1)

The operator explicitly selects an authorized PC/USB/OS-mounted SMB directory. A UTF-8 manifest has schema_version 1 and non-empty expected_files list: [{"path":"contracts/agreement.pdf"},{"path":"release/source.zip","sha256":"<replace with actual 64-char hex>"}]. Optional limits are max_files up to 20,000 and max_bytes up to 8 GiB. Paths use forward slashes; no wildcards or parent traversal. Manifest can be produced with any text editor; the user must approve scope.

## Run: Python 3.11+, standard library only

From products/flowpilot_universal:

    python -m flowpilot_universal --root /path/to/authorized-folder --manifest requirements.json --json ../new-report.json --html ../new-report.html
    python -m unittest discover -s tests -p 'test_*.py' -v

Report parent directory must already exist OUTSIDE scanned folder, and both report paths must be new (no overwrite). READY exit 0 only for complete best-effort scans satisfying all specified requirements with no issue; BLOCKED, NEEDS_REVIEW, INCOMPLETE, invalid input/output all exit 2. Reports list local filenames/hashes and may contain sensitive customer metadata: do not upload without authorization.

P50 engineering scope: strict JSON input, bounded read-only recursive scan, SHA-256 per regular file with stat-before/open/after checks, required missing/hash mismatch, duplicate contents, version candidate signals, symlink/reparse/special entry fail-closed, case-collision detection, escaped HTML and JSON create-only reports, CLI, synthetic regression. No source mutation or network calls.

NOT VERIFIED or implemented: physical Win10/11 USB/UNC/SMB, Windows junction and directory-race hardening, interrupt/resume, high-volume benchmarks/SQLite histories, GUI, polished PDF, EXE/package/signature, customer trials, license review, commercial sale. READY does NOT mean customer acceptance, an immutable filesystem snapshot or guaranteed universal NAS support. Official final-blueprint completion remains UNASSESSED until all user-approved weights and independent evidence are checked; P50 is only an engineering gate. RELEASE HOLD.
