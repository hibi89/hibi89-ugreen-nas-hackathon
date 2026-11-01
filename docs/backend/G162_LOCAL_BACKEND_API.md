# G162 FlowPilot 3.0 — local backend API (not an official NAS server)

**Status:** exact source G162 `b4f59ae749db81abd54bd98f73694974bc579290`, Linux+Windows CI verified. This is a local two-template prototype, not a production backend or genuine registered Uliya Expert. No new fees.

## Local launch
Python 3.11. Run from a trusted checkout, never expose the token or local API on a public interface. Place the DB outside the GitHub checkout in a private local folder that already exists.

Windows PowerShell example:

```powershell
$env:FLOWPILOT_LOCAL_API_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(48))")
python .\tools\flowpilot_local_backend.py --db "C:\private-folder\flowpilot.sqlite" --init-db --port 8766
```

To restart, use the **same token only for live clients** (an old token is not stored) and omit `--init-db` (existing DB never overwritten):

```powershell
python .\tools\flowpilot_local_backend.py --db "C:\private-folder\flowpilot.sqlite" --port 8766
```

Client HTTP headers: `Authorization: Bearer <local-token>`. For POST also `Content-Type: application/json`. Limit POST JSON to 2048 bytes. Server listens only on `127.0.0.1`, with Host/Origin checks; no CORS, remote client, cookie-based session, user-files endpoint, general shell, or Docker/NAS runtime.

## Contract
1. `GET /v1/health`: live local status (still HOLD).
2. `POST /v1/workflows` body `{"goal":"check required files","request_id":"req_demo123456789"}`: one of two exact recognized goal families. Stable workflow ID for same request ID+goal; changed goal reusing ID refused.
3. `GET /v1/workflows`: last 20 opaque workflow IDs; `GET /v1/workflows/<workflow_id>`: stored state, plan hash, event-chain integrity, no customer paths.
4. `GET /v1/workflows/<workflow_id>/plan`: trusted recompiled DAG and independent plan SHA check.
5. `POST /v1/workflows/<workflow_id>/test` body `{}`: deterministic four-role council and disposable synthetic fixtures; no owner data/NAS.
6. `POST /v1/workflows/<workflow_id>/approve`: body `{"plan_sha256":"<hash from preview>","acknowledgement":"APPROVE_SYNTHETIC_ONLY"}`. Only after TESTED; does not grant live NAS permissions.
7. `POST /v1/workflows/<workflow_id>/run` body `{}`: once-only G119 local synthetic QA ledger, SQLite receipt hashes, no production action. Repeats return same completed receipt.
8. `GET /v1/workflows/<workflow_id>/audit`: read-only local event hashes, G119 evidence integrity if run exists; hash chain is NOT notarized.
9. `POST /v1/workflows/<workflow_id>/recover` body `{}`: when a reserved synthetic run was interrupted, reconcile G119 ledger without running it again; missing receipt -> INTERRUPTED_BLOCKED.
10. `POST /v1/advice` body `{"opt_in":true,"telemetry":{"disk_used_percent":95}}`: caller-provided integers, suggestions only. No NAS polling, background job or automatic repair.

## Security and evidence
Unknown goals, mixed paths, extra API fields, missing/incorrect bearer token, remote Host/Origin, symlinked/unknown/pre-existing DB on `--init-db`, replay attempts, SHA drift and unapproved stages are denied. The server does not persist the API token; its storage contains only exact allowlisted goals, workflow IDs, receipt hashes and event metadata. Back up or copy the SQLite database only after stopping the server.

`COMPLETE_LOCAL_SYNTHETIC` means disposable fixture tests succeeded, **never Uliya, live NAS, real customer data, real Docker, generalized LLM generation or official hackathon certification**. Real registered Expert capabilities, remote/auth deployment, full UI integration and real NAS readback are separate unverified phases requiring consent.

## Tests
```bash
python -m unittest discover -s tests -p 'test_flowpilot_local_backend.py' -v
python -m unittest discover -s tests -p 'test_*.py'
```

Windows full owner-equivalent: `powershell.exe -ExecutionPolicy Bypass -File .\verify_local.ps1 -Mode full`. GitHub Actions run [41280521670](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41280521670) checked Linux and Windows. Production URL: NOT_APPLICABLE.
