# G249 — create-only scoped local version evidence (not NAS)

Supports a distinct owner-consented deliverable after the G248 metadata-only
version comparison. This utility runs outside the official Markdown Skill ZIP.
It never opens source contents, selects a winning version, modifies a source,
uploads data, invokes a registered Uliya Expert or starts an NAS trial.

## Two alternatives

A. Save a raw owner-path inventory or add a new SQLite persistent endpoint:
easier to browse later but stores identifiers and expands access/recovery risk.
B. Selected: existing G165 scoped, single-use, owner-approved local lstat;
a **second independent approval** creates only a new, bounded JSON report with
numbered states and a salted scope hash. No new API or persistent database.

## Reproducible disposable fixture

Create a trusted LOCAL (non-NAS) folder containing `final.pdf` and
`final_v2.pdf`, then execute from repository root:

```bash
python tools/flowpilot_g249_version_export.py --root "/ABSOLUTE/DISPOSABLE" --required "final.pdf" --candidate "final.pdf=final_v2.pdf" --output "/ABSOLUTE/NEW_REPORT.json"
```

Without approvals this returns `WAITING_LOCAL_METADATA_APPROVAL` and neither
inspects the folder nor creates a file. Repeat the command with only
`--approve-local-metadata` to receive indexed states without writing a
report. For a NEW create-only report, repeat with **both**
`--approve-local-metadata --approve-create-report`. The output must be an
absolute `.json` path; an existing destination is refused, never overwritten.
The CLI keeps no approval token between processes; approvals are scoped to
each invocation. For a real owner file, a separate owner authorization and
trust in the local folder are essential.

Evidence `VERSION_REVIEW` means manual selection is required; it is never
automatically marked final. Output excludes original file names, paths and
contents. `sha256` is a digest of newly created report bytes, **not** a
trusted provenance signature or NAS proof.

## Limits

Local filesystem symlink/reparse checks are not atomic. Mapped drives may
actually be NAS and are NOT proven local. Do not use on untrusted mutable
paths, real NAS mounts or external provider data without separate permission.
No Vercel deployment; official Creator/Checker, Expert and live NAS NOT_RUN.
Release gate HOLD. Rollback is ordinary Git revert of the feature commit.
