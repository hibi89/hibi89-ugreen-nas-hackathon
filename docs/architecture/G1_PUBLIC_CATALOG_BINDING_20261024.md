# G1 — binding a provisional Skill to public Uliya catalog facts (2026-10-24 KST)

## Grounded evidence
- Official Uliya public creation-tool ZIP `uliya-skill-kit-0.7.3-en.zip`, SHA256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`, from https://ai.ugreen.com/pages/hackathon-starter-kit .
- GitHub Actions `40072315390` SUCCESS extracted exactly nine selected catalog action names/parameter key types and required flags. GitHub Actions `40072315400` 163/163 PASS, handoff CI `40072315343` PASS, commit `e06f3a2b3ec4a3f6ad2300c5f7505bcb4b6e819a`.
- Public catalog: documented `ug-filesystem` file-agent and `ug-document` document-agent; all nine checked entries are `effect=read`, `approval=none`, but **permissions.knowledgeStatus=unknown**. Description/source examples were not copied. `file` is an optional repeatable parameter for document operations; optional does not equal approved global browse. `ls/find` both require `path`; `qa/extract` require `query`. Listing `limit` by itself does not prove completeness or cursor contract.
- New Skill reference `skill/projectready-nas/references/catalog-actions.md` lists verified catalog input schema, safe read-only scope and explicit limitations. Source is only a provisional Markdown candidate. `tools/sdk_parameter_matrix.py` and Python tests stay outside official Round 1 ZIP.

## Design choice
A: Guess CLI command flags and imply first-party approval from `approval=none` — rejected (wrong and unsafe).
B: Include only checked catalog action/parameter labels as **possibilities** and require actual installed Agent, user permission, output semantics and full-list evidence before calling — selected. Safe default is NOT_CHECKED/NEEDS_REVIEW, not a fictitious READY.
C: Bind exact CLI and official check only after private/authorized installed SDK evidence or official support (still future).

## Remaining blocked
- Actual registered Agent/runtime invocation syntax/return structure and effective NAS permissions;
- SDK checker safety/license; static scanner flagged network-related string/pattern, no script run;
- Real authorized NAS run, privacy guarantees and official Skill validation/Devpost submission.

Calendar-day effort: 2026-10-24 fixed original deliverables DONE 100%, 0h assigned remainder. This G1 activity is separate advance, real labor hours NOT_MEASURED. 2026-10-25 planned G1 1.5h plus separate 1.5h reserve (not an ETA). Incremental spend 0 KRW.
