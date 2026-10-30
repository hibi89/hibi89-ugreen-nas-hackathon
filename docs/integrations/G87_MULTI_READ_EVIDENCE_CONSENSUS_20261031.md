# G87 — Multi-read file-agent evidence consensus (offline backend)

**Source:** `tools/flowpilot_multi_read_intake.py`; tests: `tests/test_flowpilot_multi_read_intake.py`; branch `lead/ugreen`; latest code commit `eb09099b57b8d914e3e9d46b539f7a08812c29b1`. Python 3.11 stdlib, no third-party API, no NAS calls.

## Why this exists

The verified public first-party Uliya capability catalog lists read-only `ug-filesystem ls/find/stat` and a mapped `file-agent`, but it does **not** prove that any registered Expert is installed, that its result fields match a hypothetical Python schema, or that a read has complete pagination or customer permission. Existing G61 safely consumes a single operator-normalized file-agent receipt. G87 combines several separately validated receipts without upgrading untrusted assertions into real-NAS proof.

The approved lower-cost and safer approach is a local **bounded normalized receipt merger**. Direct raw-SDK calls would require an independently verified official runtime contract and separate user approval; they are not implemented here.

## Contract and failure policy

CLI: `python tools/flowpilot_multi_read_intake.py --input path/to/operator-normalized-multi-read.json`.

Input JSON must contain exactly `schema=flowpilot-multi-read-receipts-v1` and `receipts` (1 to 8 G61 `flowpilot-agent-observation-v1` objects). The normalizer requires same owner-approved root, goal, checklist, processing-location consent and version-candidate scopes; each read action must be `ug-filesystem ls/find/stat` with strict read-only receipts. JSON duplicate keys/nonfinite values and oversized inputs (over 128 KiB) are refused. No secrets or file content are accepted as output.

A single *claimed* fully enumerated, authorized `ls/find` establishes only an **offline provisional** absence. `stat`-only or partial listing cannot establish absence. Conflicting full listings, changed references, unexpected supplemental paths, symlink/containment mismatch or denied permissions degrade items to NOT_CHECKED. If owner has not consented or goal asks for mutation, BLOCKED/WAITING_APPROVAL is never upgraded by a conflicting receipt.

Output contains indexed `PRESENT/MISSING/NOT_CHECKED/VERSION_REVIEW` states for operator review, but explicitly `operator_claims_independently_verified=false`, `registered_expert_invocation_verified=false`, `real_nas_verified=false`, `release_gate=HOLD`. No owner paths, raw references or contents are returned; raw files are neither read nor written by this tool. This module is an **engineering-side Python adapter, not part of the Markdown-only official Skill ZIP**.

## Verification

- Initial G87 code `ba9c080b561155f65b0b4e84967018492b8926ef`: [GitHub functional CI 41103745234](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41103745234) SUCCESS — 830 total / 825 PASS / 0 FAIL / 5 SKIP. Latest code adds strict blocked/approval precedence and a 19th test; [latest functional CI 41104026399](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41104026399) was QUEUED at checkpoint, so latest full suite is not claimed PASS.
- The earlier owner genuine native G86 HAE→LA→SQLite acceptance PASS remains true on its unchanged sources. G87 has never called real Uliya/NAS and does not improve hardware-verified status.

## Next external gate

The official Starter Kit and contest rules require registered expert agents, forbid adding generic executable Python into submitted Markdown Skill, and do not require NAS access for Round 1. Before actual Uliya integration, obtain verified installed Agent operation signatures, complete/scoped return fields, owner permission and processing-location disclosure, then separately test on sponsor-authorized device only when eligible. No external calls or permissions changes without user approval.
