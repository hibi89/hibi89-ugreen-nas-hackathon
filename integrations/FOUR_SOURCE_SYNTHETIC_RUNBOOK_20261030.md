# Four-source disposable local verification — 2026-10-30

## Goal and safety

One optional **owner-local, source-pinned synthetic** check of FlowPilot's bounded goal → actual private HAE Lightning Azent → public SOVIA → private DBVORA schema reader. No NAS, Uliya, user-selected directory, customer files, or external API. Source code remains in separate checked-out repositories; public GitHub Actions uses mocks and cannot validate the private HAE or DBVORA implementation.

The default command does not approve synthetic SQLite writes. It makes a fresh disposable README fixture and calls local HAE/SOVIA preflight, but refuses DBVORA invocation or SQLite writes. The second command opt-in is an explicit operator action and creates only temporary synthetic SQLite under the script's own temp directory:

```powershell
py -3.11 tools/verify_four_source_synthetic.py --hae-root ..\HAE --sovia-root ..\SOVIA_sovereign --dbvora-root ..\DBVORA
py -3.11 tools/verify_four_source_synthetic.py --hae-root ..\HAE --sovia-root ..\SOVIA_sovereign --dbvora-root ..\DBVORA --approve-disposable-synthetic
```

Both calls verify exact pinned HAE/SOVIA source; the second additionally verifies DBVORA pinned feature SHA. The verifier creates a *new* temp root each call and derives the SHA approval internally from that fresh fixture, then invokes the real injected LA and DBVORA only for two synthetic counts. The returned JSON deliberately contains no source paths, file names, owner data or approval hashes.

The literal `PASS` result must be captured with source commit IDs and terminal exit code before stating actual 4-source integration. This wrapper and public fake tests are **NOT proof** of real source execution. No permission or authority to access live NAS, Uliya, customer file systems or vendor services follows from a synthetic PASS.

## Operational release boundary

As of authoring, **NO new owner-local four-source run occurred**; the previously reported real HAE/SOVIA local results are separate evidence and do not verify DBVORA. Existing official G49 Markdown Skill and G52 PDF/ZIP remain frozen. Round1 must go through official Creator/rights/exact-file review and entrant signoff; no automated Devpost submission.
