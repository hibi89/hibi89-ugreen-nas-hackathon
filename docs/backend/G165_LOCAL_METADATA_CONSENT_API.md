# G165 — consent-scoped local metadata HTTP API (NOT UGREEN NAS)

## Design
A: arbitrary browser-supplied root directory, rejected due to broad privileges and private data exposure.
B: choose local non-NAS root once at backend startup, preview exact relative checklist without a root stat, require separate one-use scope SHA approval, then use existing local lstat inspector. B implemented, no new paid APIs or filesystem writes.

## Launch
Use Python 3.11 from trusted checkout. Set FLOWPILOT_LOCAL_API_TOKEN as 32+ random characters in process environment. Start with a NEW private SQLite outside repo (omit --init-db on restart):

    python tools/flowpilot_local_backend.py --db ABS_LOCAL_DB.sqlite --init-db --metadata-root ABS_DISPOSABLE_LOCAL_FOLDER --port 8766

Leave --metadata-root out to disable the local metadata API. Never supply an NAS mount, Windows mapped remote drive, cloud share or customer folder without explicit owner permission. The root is never accepted in HTTP JSON or returned in API replies. All routes enforce Authorization: Bearer LOCAL_TOKEN and loopback Host/Origin checks, no CORS.

## API contract
- POST /v1/local-metadata/preview JSON {"goal":"check required files","required":["README.md","release/final.pdf"]} returns a random review_id, salted scope_sha256, required_count, status WAITING_APPROVAL, inspection_result null. Only 1-20 canonical relative paths, exact goal. No root or child stat/lstat occurs.
- POST /v1/local-metadata/approve JSON {"review_id":"rev_...","scope_sha256":"...","acknowledgement":"APPROVE_LOCAL_METADATA_READ_ONLY"}. Exact match needed. Ticket consumed BEFORE first root lstat. Returns LOCAL_METADATA_FINDINGS_READY or LOCAL_METADATA_BLOCKED or INSPECTION_REFUSED, each sanitized to numbered item state only, never raw names or file contents.
- GET /v1/local-metadata/reviews/REV_ID retrieves cached sanitized state, never reruns a local read.
- POST /v1/local-metadata/cancel JSON {"review_id":"rev_..."} cancels pending plan with NO read.

Ticket expiry: 600 seconds; at most 32 active reviews, no background watcher. Process restart discards all consent tokens and findings. Unapproved requests do not touch operator filesystem. On cancel/approve, raw filenames are discarded from memory, while exact required_count remains visible. No DB schema changes.

## Limits and evidence
G62 owner_local_audit.py uses nonrecursive read-only lstat, no customer file content, hash, uploads or execution. It rejects symlinks/reparse roots and child links, but cannot guarantee safety on concurrent directory mutation or prove a Windows mapped volume is not remote. This is not a registered Uliya Expert, genuine NAS, user-prod proof, signature notarization or official contest Checker. Do not treat synthetic local CI as certification.

Tests: python -m unittest discover -s tests -p test_flowpilot_g165_local_metadata_api.py -v; full Python unittest discover and Windows verify_local.ps1 -Mode full.

Final feature source SHA 90d4446c0b5dc322632cb274935cc0a75211aa8f. CI https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41287360947 Linux 1351 PASS/0 FAIL/14 SKIP, Windows full PASS. No Vercel/production URL; release HOLD.
