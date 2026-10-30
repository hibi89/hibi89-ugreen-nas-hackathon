# UGREEN four-source execution / source-truth checkpoint (2026-10-30)

## Actual development
- A single CLI is present: `tools/verify_four_source_synthetic.py`, plus a Windows wrapper `tools/run_four_source_synthetic.ps1`. It builds a **new, disposable synthetic** README file internally and never takes an owner document or NAS path.
- Default call previews and stops **without SQLite write or private DBVORA call**. The explicit `--approve-disposable-synthetic` mode verifies clean, exact Git SHAs for HAE + SOVIA + DBVORA and the two-intent local SHA-approval chain before using disposable SQLite.
- The result contract additionally refuses stale/missing private source commit identities, unverified public CI claims, forged SHA approval, wrong synthetic DBVORA scope/size and file-content leakage claims. All outputs remain count-only. Such contract testing **cannot substitute for actual private code execution**.

## On an owner-trusted Windows checkout (optional; never against live NAS)
```powershell
powershell -NoProfile -File tools/run_four_source_synthetic.ps1
powershell -NoProfile -File tools/run_four_source_synthetic.ps1 -ApproveDisposableSynthetic
```
The second command explicitly authorizes isolated temporary synthetic SQLite writes. Both commands require the separately present exact pinned Git checkout versions from `tools/verify_private_hae_chain.py` and `tools/verify_local_metadata_la_chain.py`. No automatic cloning or network connection occurs.

## Verification classification
Public GitHub Actions can verify mocked HAE/DBVORA and actual **public** SOVIA local evaluator. Actual **private** HAE/DBVORA E2E must be run by the owner in an authorized trusted local environment. Successful simulation does not prove NAS, Uliya agent invocation, official Creator provenance or submission. All external release gates stay HOLD. CI pending is non-blocking for further development; check the latest SHA run later rather than repeatedly waiting.
