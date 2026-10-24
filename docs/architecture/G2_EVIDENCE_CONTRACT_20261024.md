# G2 — evidence contract & Missing-files engine, PROVISIONAL / OFFLINE ONLY

Date 2026-10-24 KST (ahead of 10/27 G2 and 10/28-29 G3a). Lead branch \`lead/ugreen\`. **This is not a final Uliya Skill, nor a claim that a supported official adapter exists.**

## Use case and threat model
A freelancer asks whether deliverables in a **user-authorized NAS folder** satisfy an explicit checklist. Return evidence-backed PASS/FAIL/REVIEW/NOT_CHECKED per requirement. A missing file **must not** be declared missing when a search is partial, denied, untrusted, or incompletely paginated. A directory does not satisfy a required file. The software never deletes/moves/reads bytes/shares customer files.

## Provisional typed contract (not actual UGOS command/API)
- \`Requirement(id, relative_path, mandatory)\`: an explicit path under an authorized subtree. No raw NAS absolute path and no path traversal.
- \`ScanEnvelope(authorized_root_ref, scope_prefix, status, evidence_origin, adapter_verified, permission_granted, pagination_exhausted, complete_scope, observations, scan_reference)\`: data structure proposed for a **future official approved registered-agent adapter**. None of these fields has been matched yet to a real Uliya CLI response. A boolean supplied in a synthetic test **is not proof of real authorization**.
- \`FileEvidence(relative_path, evidence_ref, is_file)\`: opaque evidence references; no contents. The real provider must produce immutable/reproducible references if supported; never fabricate them.
- \`PresenceCheck(requirement_id, relative_path, verdict, evidence_refs, explanation)\`: per-file result. \`NOT_CHECKED\` if official adapter, permission, scan/reference or pagination cannot be established; \`FAIL\` only if verified COMPLETE+authorized+fully paginated scan and file absent. Duplicated paths are \`REVIEW\`.
- \`PresenceReport(checks, trusted, limitations)\`: output summary suitable for integration into the earlier offline \`evaluate()\` gate model.
- \`src/projectready/presence.py\` implements that **pure in-memory evaluation contract** without SDK or NAS I/O. \`tests/test_presence.py\` covers path traversal, scope, evidence, completeness and authorization failure.

## Integration restrictions
1. When \`evidence_origin=SYNTHETIC\` or the official agent adapter is not validated, all presence checks are \`NOT_CHECKED\`. **Do not synthesize an official \`SDK_VERIFIED\` assertion in the actual user flow.**
2. Even valid presence checks do **not** alone yield READY: \`version/access/privacy\` gate observations are required. Unsupported privacy analysis must remain \`NOT_CHECKED\`; manual user decision can be requested, not assumed safe.
3. Official [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) publicly allows **files find/browse** and **documents read/extract**, but those are feature categories, not callable CLI signatures; archive schema, permission scopes, pagination and agent registries remain unverified.
4. The shipped Round1 ZIP may contain only compliant \`SKILL.md\` and linked Markdown references; Python is an **engineering prototype** and must NOT be included in the final submission ZIP.
5. Future task before G2 can be marked **FROZEN**: compare this provisional contract with actual official kit, replace only supported fields/conditions, add a faithful adapter, run official checker, then evidence-based regression tests.

## Gate states
| Component | Status on 2026-10-24 |
|---|---|
| User input / evidence schema proposal | DRAFT, offline/provisional |
| Pure missing-files engine and edge tests | CODED, subject to remote CI |
| Official SDK ZIP metadata | VERIFIED (26 entries, SHA in G1 report) |
| Registered expert agent callable I/O / permission mechanism | UNVERIFIED / BLOCKED |
| Real NAS installation and Skill execution | NOT_RUN |
| Feature complete under official Uliya | NO |
| Expense | 0 KRW new cash |

Re-evaluate architecture choice A (read-only file metadata) vs B (content + AI) against first-party documented capability once SDK semantics are validated. No unilateral product narrowing or sensitive external model transmission.
