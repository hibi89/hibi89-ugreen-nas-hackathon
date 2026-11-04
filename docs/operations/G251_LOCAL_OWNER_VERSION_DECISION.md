# G251 Local owner decision receipt — READ-only evidence / CREATE-only decision

This standalone Python 3.11 off-NAS tool completes the previously missing
**manual owner-review step** after a G249/G250 privacy-redacted version conflict
report. It does not call Uliya Expert, open original file bodies, choose
an authoritative version, or declare any release READY.

## Designs
- A: mutate/rename the "latest" source on the NAS, rejected: unsupported
  runtime rights, destructive risks and automatic authority guessing.
- B (selected): bind a manual owner choice to a redacted source-evidence SHA
  using independent read and create-only decision approvals. Zero external API
  spend and no need to store sensitive filenames.

## Runbook (trusted synthetic local only)
The input must be an exact G249-shaped .json report containing **one required
file and one alternative candidate**, where the finding is VERSION_REVIEW.

```bash
python tools/flowpilot_g251_owner_decision.py --evidence "/ABSOLUTE/LOCAL/flowpilot-local-version-evidence.json"
# read-only inspect and hash evidence, still no output:
python tools/flowpilot_g251_owner_decision.py --evidence "/ABSOLUTE/LOCAL/flowpilot-local-version-evidence.json" --approve-read-evidence
# explicit owner decision 'hold', 'primary' or 'alternative':
python tools/flowpilot_g251_owner_decision.py --evidence "/ABSOLUTE/LOCAL/flowpilot-local-version-evidence.json" --output "/ABSOLUTE/LOCAL/owner-choice-new.json" --owner-choice hold --approve-read-evidence --approve-save-decision
```

No write occurs without both flags. Existing outputs are never overwritten.
The saved statement binds to a digest of the exact evidence bytes and its
salted scope hash, and contains only one opaque choice code. A hash does not
authenticate the evidence's origin, and the G249 format does not preserve
which real NAS file a selected code represents. The user must interpret the
choice externally and separately confirm any actual file action. Even the
"primary"/"alternative" choice remains NOT_NAS/NOT_READY.

Tests: 13 synthetic local Python negative/positive tests, no real data or
third-party invocation. Windows filesystem race/reparse behavior is not
independently proven by these Linux tests.
