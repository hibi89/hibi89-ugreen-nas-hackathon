# Owner-local 1–3 intent four-source proof: 2026-10-30

The approved local-only harness supports 1, 2 or 3 distinct natural-language task intents. Every mode generates its own temporary synthetic README and never touches an owner-selected folder or NAS. Triple-intent mode additionally creates a disposable competing-version file and binds `README.md` to `README_final.md` for REVIEW_VERSIONS. The workflow uses the existing FlowPilot observation, LA approval and replay, SOVIA advisory, and optional private DBVORA schema-only inspection.

Run without `-ApproveDisposableSynthetic` for approval preview; invoke with that explicit flag to request temporary synthetic SQLite writes using only exact pinned local HAE, SOVIA and DBVORA checkouts.

```powershell
powershell -NoProfile -File tools/run_four_source_synthetic.ps1 -IntentCount 1
powershell -NoProfile -File tools/run_four_source_synthetic.ps1 -IntentCount 2 -ApproveDisposableSynthetic
powershell -NoProfile -File tools/run_four_source_synthetic.ps1 -IntentCount 3 -ApproveDisposableSynthetic
```

Exact integer counts, SOVIA findings and LA receipts are required for PASS. This is an executable owner-local verifier; public CI uses fakes for HAE and DBVORA. This does NOT verify NAS/Uliya or constitute an entrant release approval. Original Round1 Skill/PDF/ZIP remain unchanged.
