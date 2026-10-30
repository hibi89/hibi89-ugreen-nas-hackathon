# G94 — Owner-local metadata → redacted review backend (NOT NAS)

This engineering-only Python module links the already-tested G62 exact-path local `lstat` reader to an indexed review decision contract. It does **not** translate local filesystem observations into a fabricated G61/G87 registered `file-agent` receipt and does not modify the Markdown-only contest Skill.

- Command: `python tools/flowpilot_local_review.py --root ABSOLUTE_LOCAL_FOLDER --required README.md --required release/output.pdf --approve-local-metadata`.
- Without explicit `--approve-local-metadata`, preflight returns WAITING_APPROVAL and does not inspect owner folder metadata. The bounded read-only planner refuses mutation goals. No file content opens, uploads or writes; local only. G62's existing caveat remains: platform directory mutation races, Windows junctions and mapped remote drives are not independently proven absent.
- Output: redacted `review_queue` with checklist indices, PRESENT/MISSING/NOT_CHECKED/VERSION_REVIEW states, reason codes, counts, `decision=HOLD`, and explicit false flags for registered Uliya Expert, real NAS, official Creator and Devpost. Source is exact local metadata, NOT simulated vendor evidence.
- Compared (A) forging local observations as official Uliya agent data vs (B) retaining source-provenance separation. Selected B to avoid unsupported permission claims, lower maintenance burden and eliminate hidden network/API cost.
- Regression file: `tests/test_flowpilot_local_review.py`, including disposable real local-folder metadata, consent/no-root-read, traversal rejection, redacted CLI output, missing/version review and symlink refusal.
- Official Expert adapter implementation is gated on verified installed operation signatures, actual result shape, local-only processing permission and owner approval. Round1 release remains HOLD and original SKILL.md / PDF / ZIP untouched.

Verification and exact-SHA CI outcome are recorded in HANDOFF.md and STATUS.md once inspected.
