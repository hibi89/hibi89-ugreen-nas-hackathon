# G120 — Pinned Uliya Expert contract bridge (NO EXECUTION) · 2026-10-31 KST

The UGREEN Official Starter Kit (https://ai.ugreen.com/pages/hackathon-starter-kit) states that files/documents/knowledge agents support bounded workflows. Official Devpost 2026 rules disallow custom executable scripts and arbitrary runtimes in the Skill and require registered Expert-supported capabilities. Catalog action labels **are not proof** of runtime tool signature, registration or NAS permissions.

## Actual implementation
`tools/flowpilot_native_expert_bridge.py` reuses:
- G115 exact natural-language goal compiler (`required_file_metadata_v1` only);
- G95 `preflight_trial` and SHA-pinned first-party Uliya Kit catalog (`ug-filesystem find` selection, parameter identifiers only, permission/consent bound);
- G87 `evaluate_multi_read` for operator-normalized receipts, path scoping, duplicate refs, incomplete list behavior and contradictions.

It maps Korean/English exact *file inspection* goals to the read-only official *catalog label*, never an actual SDK command or fabricated arguments. For customer revenue CSV, Docker, schedules, writes and arbitrary instructions it returns a blocked state and explicitly points to the verified LOCAL-only G115–G119 fallback. It never claims that a runtime agent is installed or that synthetic observations are genuine NAS proof.

## Gates and evidence
Without metadata consent or processing route confirmation: WAITING_APPROVAL. With consent+proper official pinned catalog: AWAITING_REAL_REGISTERED_EXPERT_AND_RESULT_SCHEMA; output includes a safe five-stage operator checklist with zero owner paths/references. Optional operator-normalized synthetic receipts can be evaluated only after consent, and yield review-required/not-checked/missing as provisional findings, never READY/LIVE_NAS_VERIFIED.

Exact official public archive SHA-256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3` is already pinned in `sdk_semantic_index.py`; G120 test fixtures use their own *test-only* SHA overrides and mark themselves SYNTHETIC_CATALOG_TEST_ONLY. The official archive and third-party documentation have NOT been committed or republished.

Tests `python -m unittest discover -s tests -p 'test_flowpilot_native_expert_bridge.py' -v`, then exact-source Linux+Windows GitHub Actions. There is no real Uliya Agent SDK call, first-party Checker, NAS/Creator, third-party API, Docker or Devpost submission in this feature. Private G103 candidates/canonical public Skill left untouched.

## Pending requirements before a live-capability adapter
1. Owner-authorized vendor runtime and exact registered Expert executable interface, with actual request/response schema and version.
2. Real permission prompts, scoped read-only test folder and evidence provenance (not operator-self-attested).
3. Fail-closed for false/incomplete listing, stale replies, missing schema or timeout; no unapproved read/write.
4. Exact real NAS readback and session audit, then separate approval for any irreversible or recurring action.
5. Official G103 Checker run and submission artifact signoff independently.

Official URLs: https://ugreenhackathon.devpost.com/rules ; https://ai.ugreen.com/pages/hackathon-starter-kit .
