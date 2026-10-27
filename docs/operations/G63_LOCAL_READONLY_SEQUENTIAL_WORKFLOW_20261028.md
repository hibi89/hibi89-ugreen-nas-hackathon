> **2026-10-28 G63 CI VERIFIED:** Code source SHA `7a1c98cbd1113faa7a04b5cf7844576178b7f570`; [GitHub CI run 40537126475](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40537126475) **472/472 full PASS, G63 9/9 PASS**, master 40537126348 SUCCESS, closeout 40537126714 SUCCESS. All are local/offline, not official Uliya/NAS/Creator. Original Skill G49/G52 assets unchanged, rights HOLD, Devpost NOT_SUBMITTED, 3-hour UGOS demo conditional Nov3–5; owner-managed HAE/LA/REA_APP unchanged and work hours unmeasured.

# G63 — sequential owner-local FlowPilot vertical slice (2026-10-28 KST)

This adds a genuinely runnable multi-step workflow composed from the G62 real local folder metadata pilot. Development-only, strictly read-only, NOT an official UGREEN Uliya/NAS/Creator connection, not in the Markdown Skill ZIP.

Recipe (save as scratch/readonly-flow.json):
    {"schema":"flowpilot-local-readonly-v1","steps":[{"goal":"check required files","required":["README.md"]},{"goal":"check handoff deliverables","required":["review.pdf"]}]}

Run ONLY on a trusted disposable LOCAL folder (never mounted NAS or untrusted concurrently modified tree):
    python tools/flowpilot_local_workflow.py --root /absolute/local/test-folder --recipe scratch/readonly-flow.json --approve-local-metadata

Before any owner-folder metadata access the full recipe passes path/intent/checklist/consent validation. Max 8 steps/100 unique exact names, stop on missing/blocked/error, preserve NOT_CHECKED. No content of selected folder opened, no recursive scan, arbitrary script, API call, network, uploads or mutation. Recipe JSON itself is explicitly opened and max 16 KiB. Redacted JSON output never echoes owner path or filenames, cannot report NAS verified. All present remains NEEDS_REVIEW, not product released. 9 focused regression tests cover real local OS observation, blocked stop, preflight refusals and CLI E2E.

Exact-source GitHub CI is PENDING at commit preparation; update truth after checking workflows. Official FlowPilot Creator and genuine registered Expert/NAS remain NOT_RUN, entrant signoff/release HOLD, Devpost NOT_SUBMITTED. Original Skill SHA256 47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b, owner G52 PDF/ZIP, HAE/LA/REA_APP untouched. 3h UGOS trial conditional Nov3–5 KST after capabilities and owner timer approval.
