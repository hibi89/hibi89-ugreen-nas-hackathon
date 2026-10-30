# Four-source execution evidence dashboard

This isolated static HTML viewer turns **only** the bounded counters and flags from `tools/verify_four_source_synthetic.py` into a five-stage operator display. It never reads source files, other folders, NAS or user content referenced by input. Unrecognized or forged statuses fail closed; no arbitrary JSON fields are shown. Even PASS is clearly **self-reported local synthetic** and **not** official Uliya/NAS execution evidence.

```powershell
py -3.11 tools/verify_four_source_synthetic.py --hae-root ..\HAE --sovia-root ..\SOVIA_sovereign --dbvora-root ..\DBVORA > disposable-preview.json
py -3.11 tools/flowpilot_four_source_dashboard.py --input disposable-preview.json --output disposable-preview.html
```

For approved synthetic-only execution, add `--approve-disposable-synthetic` to the first command. Review stdout and local checkout SHA proofs separately; this renderer does not authenticate a JSON source or independently verify private checkouts. The HTML can be opened locally, but must not be published as an actual vendor integration test.
