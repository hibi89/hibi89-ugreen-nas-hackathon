# G167 — Local HTTP acceptance and real browser gate (3-hour NAS trial reserved)

## Scope / owner lock

No UGREEN/UGOS trial signup, login, activation, NAS or registered Uliya Expert usage may be performed here. G167 extends G166 with repeatable **disposable local** acceptance, optional real Chromium browser testing, and stricter startup path safety. Original G147/G157/G158 owner-only PDF/Skill ZIP and private data remain unmodified. Public GitHub stores no credentials or customer data. Release HOLD.

## Design choice

- **Option A:** Activate the 3-hour demo or use actual owner data to test the new dashboard. REJECTED: consumes scarce trial before readiness; may not allow Uliya Skills; risk of external transfer and unverified rights.
- **Option B (selected):** Test exact localhost service with newly created temporary SQLite and synthetic root, explicitly denied authentication and replay, verify actual CSV SHA; then run optional installed Chromium browser. Separate all NAS/Expert permissions until owner authorizes after final readiness.

### Implementation

- `tools/flowpilot_g167_local_preflight.py` — Python 3.11 stdlib, temporary new DB and root, `127.0.0.1` HTTP, random local token never printed. Auth/origin denial; unauthenticated localhost dashboard assets; health HOLD; workflow plan/test/exact synthetic approval/run replay; G119 audit/evidence; G164 CSV byte SHA; G165 preview, wrong consent, one-use local metadata and replay denial; file unchanged; shutdown then SQLite restart readback. JSON lists individual checks and always says `real_browser_verified=false`, `real_nas_verified=false`, `trial_started=false`.
- `tests/test_flowpilot_g167_local_preflight.py` — executed through normal unittest discovery; verifies each acceptance flag and critical denial; Windows-only PowerShell 5.1 child-process negative test refuses DB creation inside repo without generating the token. Non-Windows environments skip Windows-only invocation explicitly.
- `tools/flowpilot_g167_browser_acceptance.py` — OPTIONAL real Playwright Chromium browser on local 127.0.0.1 server; launches only if a compatible Playwright/browser already exists; **never auto-installs**, accesses vendor systems, uploads screenshots or starts a demo. Asserts real DOM navigation and click wiring, required approvals, auth expiry, four-role synthetic execution, G119 audit, CSV downloaded and SHA checked, G165 one-use metadata and denied reauth; collects Console/Network/JS errors without printing a token. Missing browser means `REAL_BROWSER_NOT_VERIFIED`; actual failure `REAL_BROWSER_E2E_FAILED`; host-policy restriction `REAL_BROWSER_E2E_BLOCKED_BY_ENVIRONMENT`.
- `tools/start_g166_local.ps1` — refuses any private SQLite path inside *anywhere* under public Git checkout, requires existing parent, rejects UNC and network mapped metadata roots with PowerShell 5.1 DriveInfo checks. Does not create data folders, issue vendor credentials, start NAS trial or migrate old DB.
- `tools/flowpilot_local_backend.py` — adds loopback Host/Origin-guarded `GET /favicon.ico` returning empty 204 so normal browser favicon fetch does not produce a misleading 403/404 Console error. No API auth relaxation: `/v1/*` remains bearer-protected.

## How to reproduce (trusted checkout only)

```powershell
# From repository root; no real NAS or trial and no external data:
python tools/flowpilot_g167_local_preflight.py
python -m unittest discover -s tests -p 'test_flowpilot_g167_local_preflight.py' -v
powershell.exe -ExecutionPolicy Bypass -File .\verify_local.ps1 -Mode full

# Optional, if Playwright + a local compatible Chromium are ALREADY installed:
python tools/flowpilot_g167_browser_acceptance.py
```

Do not confuse the optional browser test with an automatic prerequisite download. The browser test creates a new disposable local DB and leaves private owner DBs untouched. If browser navigation is blocked by host policy, classify **BLOCKED** and do not blame NAS, backend, or browser JavaScript without additional evidence.

## Status on 2026-11-01 KST

- G166 previous V8 mocked browser/12 local API paths: PASS (mocked, not real HTTP).
- G167 safety source and reproducible new Python/Node/optional Chromium tests: **COMMITTED / EXACT SOURCE FULL CI PENDING**. Local Python syntax compiled for a development draft of the preflight and Chromium harness; GitHub exact-source CI, PowerShell 5.1 and actual browser end-to-end **NOT_VERIFIED** in this session.
- Environment limitations: GitHub clone from the working container cannot resolve github.com; local Chromium navigation to local HTTP is blocked by `ERR_BLOCKED_BY_ADMINISTRATOR`. This is a blocked verification environment, **not evidence the app failed**. Tests have been staged for trustworthy owner/CI checkout; don't claim pass without execution.
- Official UGREEN feature page currently advertises **a 3-hour free UGOS Pro demo account**: https://ai-au.ugreen.com/pages/ugreen-ai-nas-feature-introduction . This verifies the advertised duration only, **not** applicant entitlement, login start time, permissions or Uliya Skill availability. Separate hackathon finalist NAS allocation is governed by https://ugreenhackathon.devpost.com/rules . Neither session was used.
- Trial signup/activation, Uliya official Creator/Checker, actual registered Experts, real NAS data, Devpost submission, Production Vercel: **NOT RUN / NOT APPROVED**, release **HOLD**. Historical subjective 90% progress estimate retained, **not** measurable local/NAS completion.

## Next gate

1. Confirm exact source HEAD CI Linux/Windows full and G167 preflight output; fix specific failing tests only. Verify real browser in an allowed sandbox; document Console/Network errors and CSV download.
2. Verify final candidate PDF/Skill Markdown ZIP exact SHA, genuine official Creator/Checker evidence if permitted, rights/AI disclosure and owner artifact review.
3. Verify the 3-hour trial's actual terms, capability flags and timer **without starting it**, and freeze the 180-minute matrix.
4. Only then request separate explicit owner authorization before external account creation, demo activation, vendor code, registered Expert, NAS actions, uploading content or Devpost submission.
