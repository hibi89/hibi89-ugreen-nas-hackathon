# G265 — bind operator notes to one source-and-scope-specific offline plan

Date: 2026-11-05 KST. **No registered Uliya Expert, native NAS, external API, trial activation, or SkillHub upload was invoked.** This is a local code-owned evidence-normalization feature, not a vendor authorization.

## Problem / decision
G257 `summarize_operator_notes` checks allowed stage labels and note shape, but cannot establish that the notes belong to the *same current* G226/Kit/owner-scope plan. A downstream report could mix prior session notes with current trial preparation.

A) Reuse an unsigned operator status or accept a matching stage label as real NAS proof: unsafe, rejected.
B) Keep G257 unchanged, introduce a strict source-and-scope identity for each reported note set, and refuse stale/mixed plans while always labeling operator evidence **NOT DEVICE PROOF**: selected. No new network or runtime dependencies.

## Added functionality
- `tools/flowpilot_g265_bound_operator_notes.py` consumes two small user-local JSON files: a complete current G257 offline readiness packet with G261 redacted `operator_scope`, and a G265 note packet.
- Canonical SHA256 of the **whole plan** + explicit original G226/official Kit hashes + scope request digest binds the note packet to the correct stage order, owner-declared checklist scope, and current guarded instruction digests.
- Unmatched plan/scope, removed owner scope, missing consent-declaration metadata, changed stage coverage, untrusted source/Kit hashes, duplicated operator case, unknown fields, private raw paths in notes, or false `nas_verified` all refuse exit 2 with a nonrevealing error.
- Read-only, no ordinary file content beyond the two explicitly supplied JSON inputs, no provider invocation. Output includes only case counts, SHA256 fingerprints and **`registered_expert_invocation_verified=false`, `nas_verified=false`, `release_gate=HOLD`**.
- The new digest is *not an authentication signature*: an attacker can forge both unsigned inputs. This prevents accidental or unsophisticated cross-plan mixing but cannot establish live-trace authenticity.

Example after G257 has independently generated a real original-source-bound plan and current owner scope:

```bash
python tools/flowpilot_g265_bound_operator_notes.py --plan /owner-local/readiness.json --notes /owner-local/operator-notes.json
```

Notes input must have exactly `schema`, `plan_sha256`, `scope_sha256`, `notes`. Each note must contain only a stage `case_id`, allowed `outcome`, `reason_code` and optional 64-hex `trace_sha256`. Operator must use the plan/scope digests from the very same plan; no automatic live run or implicit consent.

## Verified execution
Local Python 3.13: `python -m unittest discover -s tests -p 'test_flowpilot_g265*.py' -q`: **12 tests PASS, 0 FAIL, 0 SKIP**. Valid synthetic current-plan shape, deterministic digest, stale plan, scope swap, missing scope, wrong source/Kit, claimed real NAS/Creator, duplicate note, private field injection, and CLI acceptance/refusal tested. No genuine G257 plan or vendor response was submitted here; these tests validate **local contract behavior only**.

Exact local Git blob == GitHub file for code:
`92359836846d6c2794c200762cd8702120d2f9e4`
and synthetic tests:
`d0f45bf960929e7fc7a4e8478d06cbaef9c6a81c`.
GitHub Actions full Windows/Linux for new source SHA are **NOT VERIFIED** through the connected PR-only actions query. Older G261 CI is not G265 proof.

## Score, exclusions, and rollback
The fixed six local product categories are already full **60/60**. G265 is a genuine new operator feature, but earns **zero** extra whole-product score until a distinct *unevaluated native or official* milestone is met. Overall remains **70/100**; missing official Creator/rights 5, actual registered Expert/NAS 20, owner release/submission 5. NAS NO-GO / RELEASE HOLD unchanged.

Canonical Skill Markdown, owner-private G221/G226 ZIP/PDF, original first-party Kit and any credentials/customer data were not changed. Backout is an ordinary Git revert of the two additive source/test commits (and this documentation), no force or history rewrite.
