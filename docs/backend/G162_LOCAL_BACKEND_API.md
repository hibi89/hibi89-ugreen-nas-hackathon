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

## G163 evidence export

`GET /v1/workflows/<workflow_id>/evidence` returns JSON only after a completed, explicitly approved **local synthetic** run. Requires the same local bearer token and strict loopback Host/Origin as all other endpoints. It validates the G162 plan hash, complete ordered approval/execution event history, the actual G119 SQLite journal, PASS terminal, four deterministic council role approvals, and equality between the backend receipt and G119 `final_sha`. The response contains role labels and synthetic PASS, original receipt SHA and report SHA derived from this bounded JSON. Any mismatch returns a refusal and cannot cause a repeat run.

This is an integrity-checked **development fixture evidence JSON** endpoint, not a downloadable CSV report, independent notarization, production execution evidence, or Uliya/NAS attestation. No owner content or paths returned. Test with `python -m unittest discover -s tests -p 'test_flowpilot_local_backend.py' -v`. G163 source SHA `253b78f97ea9c5b0a592d243e290757ed41c79fb` (Linux and Windows CI [41282599589](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41282599589) PASS).

## G164 persisted synthetic report (CSV download)

**Requires a NEW explicitly created owner-local SQLite database**, because the G164 table is added by --init-db only. Existing pre-G164 owner DBs are not migrated or overwritten; their /run route refuses ARTIFACT_SCHEMA_NEEDS_OWNER_MIGRATION. Do not delete or replace an older database to bypass this rule.

After the documented create -> synthetic test -> exact plan SHA + APPROVE_SYNTHETIC_ONLY -> run sequence:

\`GET /v1/workflows/<wf_id>/report\`

With Bearer token and loopback Host check, responds with \`text/csv; charset=utf-8\`, \`Content-Disposition: attachment; filename="flowpilot-synthetic-fixture.csv"\`, \`Cache-Control: no-store\` and \`X-Flowpilot-Content-SHA256\` covering the exact bytes. CSV data is from a **code-generated local disposable fixture**, NOT real owner files or NAS. The supported templates are customer revenue (two sample customers) and required-file metadata initial/after-fixture-repair states. The data is actually stored once in SQLite rather than recomputed on GET. Source receipt SHA and report bytes SHA are checked again when downloaded; missing approval, mismatched receipt, corrupted artifact bytes or interrupted run cause refusal without a retry.

G164 code \`tools/flowpilot_g164_report_artifact.py\`, \`tools/flowpilot_local_backend.py\`, G119 source \`tools/flowpilot_repair_ledger.py\`; tests \`tests/test_flowpilot_g164_report_artifact.py\`. Exact feature commit \`2755aa594365e68297b761ce7327954ff412a2cb\`; Linux+Windows [CI 41285302780](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41285302780) SUCCESS. No genuine Uliya/Expert/NAS/LLM, production deployment or independent audit notarization is claimed.

## G164 final security source SHA (after first artifact implementation)

Current verified feature code is \`778844b02a8fc8e6c54c1901a1ecb8c681ea9439\`. An additional double-field tamper case demonstrated that merely comparing a stored CSV to its own editable SQLite SHA is not sufficient. The downloadable report now also must equal the code-owned reference fixture bytes for its exact template, in addition to its G119 receipt and content SHA checks. Linux 1342 PASS/0 FAIL/14 SKIP, Windows full regression PASS [CI 41285572141](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41285572141). The feature remains synthetic only and no independent cryptographic signing/notarization is claimed.
