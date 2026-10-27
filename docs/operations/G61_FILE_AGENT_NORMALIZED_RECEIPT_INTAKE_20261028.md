# G61 — Operator-normalized Uliya File Agent response intake

2026-10-28 KST, `lead/ugreen`.

## Implemented seam
The live NAS is not accessible in this environment. Rather than fabricate its SDK return schema, G61 introduces a very narrow **offline normalization boundary**: a bounded `flowpilot-agent-observation-v1` JSON object that a human can construct **after an official read-only file-agent response actually exists**. It is **not the native vendor JSON**. It checks exact keys, expected agent and documented read-action labels, exact scoped folder/checklist, read-only intent, exact boolean consent/claimed permissions, no unauthorized extra discovered rows, no repeated cross-file refs, file/symlink/containment claims, incomplete enumeration, optional version candidates; then feeds only bounded observation data through existing FlowPilot `evaluate_offline`.

This produces provisional states `PRESENT`, `MISSING`, `NOT_CHECKED` or `VERSION_REVIEW` **only on operator-provided claims**; it never certifies real Uliya invocation or NAS evidence. Output omits actual folder names, file paths, references, document contents, customer material and raw parser errors. Malformed receipts return a generic refusal; input is local only (64 KiB cap, no network). It never changes source Skill, uses tokens, writes to NAS or submits.

## Runnable command
```bash
python tools/flowpilot_agent_result_intake.py --input docs/operations/fixtures/G61_SYNTHETIC_NORMALIZED_FILE_AGENT.json
python -m unittest discover -s tests -p 'test_flowpilot_agent_result_intake.py' -v
```
The included fixture is **fully synthetic**. For later authorized trial: transcribe only sanitized path/ref metadata after the actual official Uliya agent contract is confirmed. Do not copy a raw vendor response or any session credentials into public GitHub; use a private local receipt and do not commit it. A JSON field claiming `registered_adapter_confirmed:true` is not independent proof, even if a complete scan is asserted.

## Acceptance and hard stops
17 new tests: valid case, claimed complete absence, partial scan, denied registered-agent flag, wrong agent/op, root mismatch, out-of-scope, restricted/traversal, non-boolean flags, write-intent block, no metadata consent, version conflict, cross-file ref reuse, unrecognized fields, subprocess CLI and generic error privacy. CI on new G61 exact source **PENDING**. Existing source Skill SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` unchanged. Actual official Uliya Expert/Creator NOT_RUN; NAS NOT_RUN; vendor return schema/effective permissions NOT_VERIFIED; owner rights and Devpost HOLD.

G61 does not replace official Creator generation or NAS integration. To achieve real end-to-end integration we must confirm an actual sanctioned Uliya Agent interface during a separate owner-approved test window, inspect the *real* return shape privately and implement a verified adapter, then rerun an attributable real response; only then assess real NAS operation. HAE/LA/REA_APP remain independent.
