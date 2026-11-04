# G274 — Candidate dispatch scope hardening and regression proof

Verified 2026-11-05 KST. This fixes two actual G273 contradictions in a separate owner-private Markdown Skill ZIP. The new owner-private G274 candidate SHA256 is `f8774f45dd78d04c0f78bb3609645c63eed85fd15a2d181e2d8e6a4d5635ec78` (18,681 bytes, 5 Markdown files). Source G273 immutable ZIP SHA256 `49bb0a5a865879ef849f0d6b3c151f974afd122d1552e4b5d99951a6967bcd40`; official Uliya Kit ZIP SHA256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`.

## Defects found and corrected
1. In the G273 main `file-agent` delegation instruction, initial discovery allowed `ls, find or stat`, contradicting the new strictly bounded `ug-filesystem find` reference. G274 narrows initial discovery to owner-filtered `find` with verified `max-depth<=5`, `limit<=200`, plus any stricter owner budget. No unbounded `ls` substitute; `stat` only for exact attributable in-scope references after bounded discovery.
2. The G273 evidence reference refused an inventory at exactly **200** results but failed to flag a smaller owner-chosen limit such as 12 or 20 as potentially incomplete. G274 applies the conservative incomplete-coverage rule when result count reaches the **actual chosen limit**, not just 200. `NOT_CHECKED` remains mandatory if completeness cannot be evidenced; no widening or retry.

## Measured verification
- Private patch tool: `g274_private_skill_guard.py` SHA256 `13cd6d270f5bc2f88bfd270f0ccc7f30e8e57134ec2f30b382c52702ebbf9146`; private merger tests SHA256 `77e638afa16b23dbd97e2c72f7dc2142127e070cca35a6de47e60ac4700372ce`. Both are **separately downloadable private artifacts**, not public GitHub source.
- Direct local synthetic patch regression tests **12/12 PASS**. Actual extracted G274 final ZIP was checked with pinned first-party `scripts/check-skill.mjs` **twice**, both exit 0, `static-pass`, **0 errors, 0 warnings, 0 info**; byte-identical checker results SHA256 `558396c7243f152ede60c2139cd5260ee01f5760cb2a4afe8d665c74ec066d09`.
- Three other G269/G273 reference files unchanged **3/3 exact bytes**. No original G269/G272/G273, customer data, credential, NAS device, or vendor Kit modified.
- Additional **public generic offline acceptance guard** in `tools/g274_public_contract_check.py` and four disposable synthetic tests in `tests/test_g274_public_contract_check.py` (local 4/4 PASS). Run it with a private candidate path; never commit a private ZIP. This guard is not a substitute for the official Checker. Exact GitHub CI result and SHA to be reported after commit.
- Private redacted receipt `UGREEN_G274_VERIFICATION_EVIDENCE_PRIVATE.json` SHA256 `3fbcc220e3e4bb1b6486d3b6d8a4f5be9dd54cf04a40500cb24136a52a638ecf`; stored as downloadable conversation output, not public repo.

## Acceptance and rollback
**Total whole-product 73/100, +0%p.** Earlier 60/60 local engineering and 13/15 Skill/Creator source conditions already fully credited; remaining 2 require explicit participant rights/license decision, 20 require registered Expert/NAS live validation and 5 actual owner-authorized exact-artifact release/Devpost submission. An offline correction cannot earn those conditions; a +1 score now would double count or fabricate external evidence. **RELEASE HOLD / NAS NO-GO / NOT_SUBMITTED**, Vercel production N/A. This is a genuine defect correction but fails the owner +1%p per-turn scoring target.

No paid API, external AI provider, Devpost upload, or 3-hour NAS trial invoked. Restore private candidate from immutable G273 ZIP; public repo from parent SHA via normal revert, no force push.

Next priority: confirm the newly committed source-specific Linux and Windows CI, then only after explicit separate owner authorization choose and record entrant rights/license, obtain genuine registered Expert/NAS evidence if access is available, and finalize exact Round1 artifacts before **2026-11-16 16:45 KST**. Do not repeat artificial progress increments for the same static correction.
