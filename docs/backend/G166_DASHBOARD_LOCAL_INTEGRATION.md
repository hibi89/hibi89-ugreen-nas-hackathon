# G166 — token-safe local dashboard integration (UGREEN trial NOT STARTED)

## Goal and implementation

G166 now contains a real locally served HTML/CSS/JavaScript dashboard bound to the existing G161–G165 Python stdlib HTTP + SQLite backend. It is **not** the Uliya vendor dashboard, a registered Expert, a public production app, or evidence of a successful NAS session.

- `GET /dashboard`, `GET /dashboard.js`, `GET /dashboard.css` load static repository-owned assets from the same loopback HTTP server. These three routes intentionally do not require bearer auth because an unauthenticated browser navigation cannot add an Authorization header. They have **no embedded secrets**, strict Host/Origin gate, no-store, no-referrer, frame denial, nosniff and restrictive CSP (`default-src 'none'`, same-origin script/style/connect). The normal `/v1/*` API still requires the 32+ character bearer token.
- Browser token is entered manually only after launch, cleared from password field, retained **in ephemeral JavaScript memory** and never appended to query strings, cookies, localStorage/sessionStorage or dashboard assets. Browser refresh requires reentry. `credentials: 'omit'` (double-quoted in actual JS) is enforced.
- Existing exact allowlisted goals only. Dashboard keeps the workflow plan SHA from a verified `/plan` response, shows states, requires `TESTED` + separate checked consent before sending `APPROVE_SYNTHETIC_ONLY`. It never silently executes a real NAS task; `/run` is only available for `APPROVED_SYNTHETIC` local fixture state.
- Review display: list/load recent IDs, plan, council test, approve, execute, audit, G163 evidence, G164 CSV. The CSV uses authenticated `fetch`, checks response content type and SHA-256 using WebCrypto **before** generating the temporary browser download link. No bearer token in the download URL.
- Optional G165: a checklist of 1–20 relative paths is submitted to `/v1/local-metadata/preview`, then raw textarea is cleared. One-use inspection requires a second explicit checkbox and backend SHA-linked `APPROVE_LOCAL_METADATA_READ_ONLY`. Cancel and status are separate; output contains item indexes/states, not filenames. The root must be operator-chosen at server startup, must not be any NAS share, and is never received from browser requests.
- Explicit `/recover` does not replay interrupted G119. Errors and lack of connection fail closed. All displayed backend JSON is rendered with textContent, not innerHTML.

## Architecture alternatives and decision

A. Standalone web app on another port or public host: needs CORS, separate credential distribution, additional deployment and API attack surface; **rejected**.
B. Serve zero-dependency static dashboard from the exact existing 127.0.0.1 backend, enter token on the same origin and keep it in memory; **selected** for lowest cost, source reuse and minimal maintenance. No external JavaScript libraries, cookies, web build tools, paid APIs or Vercel deployment.

## Windows operator start (only after cloning trusted source)

Requires Python 3.11, an **existing private parent directory** outside the checkout for the new SQLite file, and an actual local, non-NAS optional metadata root. For a new DB:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_g166_local.ps1 -Db "C:\private\flowpilot-g166.sqlite" -InitNewDb -MetadataRoot "C:\private\g166-disposable-folder"
```

To resume the same DB, remove `-InitNewDb`. To disable file-metadata access, omit `-MetadataRoot` completely. The script prints a fresh token **only to the operator's terminal** and a local URL (`http://127.0.0.1:8766/dashboard`); it does not upload/save the token. The terminal output is sensitive and should not be recorded or posted. Ctrl+C stops the server; back up the private SQLite DB only after shutdown. Existing owner DBs from before G164 must not be silently migrated.

No command in this file activates or registers the 3-hour UGOS Pro trial.

## Regression evidence classification

**Source now added:**
- `tests/test_flowpilot_g166_dashboard.py`: real localhost HTTP test of asset bytes/CSP/Host/Origin/no-auth API, plus optional Node syntax and simulated-DOM client over a real temporary HTTP/SQLite server.
- `tests/g166_browser_client_smoke.cjs`: browser-event simulation uses Node built-ins (no npm install), runs create/plan/test/approve/run/audit/evidence/CSV verified download/list/load and G165 preview/cancel/approve/status on the real temporary Python server. This tests DOM event wiring, **not actual Chrome/Firefox rendering**.
- A separate direct V8 mocked-DOM execution through development orchestration succeeded for 12 HTTP call paths; **responses were mocked**, not real server responses. V8 syntax parse of JS and Node .cjs succeeded. This limited test does not replace full CI.

**Not yet confirmed for this SHA:** GitHub Actions Linux/Windows full test status, Node+real HTTP E2E from the checked out commit, real Chrome/Firefox DOM/console/network, restart with owner's private DB, vendor Kit/Checker, official registered Uliya Expert, real NAS trial or Devpost acceptance. Mark these **PENDING / NOT_VERIFIED** until exact results are captured. Historical G165 CI remains valid for G165 only.

Target commands in trusted local checkout:

```bash
python -m unittest discover -s tests -p 'test_flowpilot_g166_dashboard.py' -v
python -m unittest discover -s tests -p 'test_*.py'
```

Windows full: `powershell.exe -ExecutionPolicy Bypass -File .\verify_local.ps1 -Mode full`. Observe a real browser at `/dashboard` and inspect DevTools Console/Network, API refusal, request headers, failed-token state and CSV hash; capture only redacted evidence.

## Remaining before any 180-minute trial

1. Confirm exact-source G166 full Linux/Windows CI and actual browser E2E, fix any failing implementation; freeze code and a reproducible local test script.
2. Confirm official current 3-hour demo terms and capabilities: start clock, permitted actions, Uliya Skill/registered Expert, data location/retention. **Unknown means UNAVAILABLE/NOT_VERIFIED**; no assumed NAS API.
3. Freeze owner-review PDF + Markdown-only Skill ZIP candidate without changing original G147/G157/G158 bytes; obtain original work/AI usage/rights and release approval separately.
4. Prepare read-only disposable fixtures, manual clock, evidence log/stop conditions. After all these gates, **ask for separate owner approval** before opening/activating the limited 3-hour trial.

## Release gates

Trial: **NOT STARTED**. Live NAS: **NOT VERIFIED**. Uliya registered Expert: **NOT RUN**. Official Kit/Checker: **NOT RUN**. Source completion: **PARTIAL PENDING CI**. Public production/Vercel: **NOT APPLICABLE**. Devpost: **NOT SUBMITTED**. Overall completion: prior 90% is a historical subjective estimate, not a measured validated rate. **Release HOLD**.

New source paths: `tools/flowpilot_g166_dashboard.{html,css,js}`, `tools/start_g166_local.ps1`; backend change `tools/flowpilot_local_backend.py`; tests in `tests/test_flowpilot_g166_dashboard.py` and `tests/g166_browser_client_smoke.cjs`. Keep their SHA/branch in HANDOFF/STATUS current after actual verification. No private PDFs, tokens or local owner data added to GitHub.
