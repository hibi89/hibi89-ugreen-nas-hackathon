# G25 — User-delivery PDF byte-fidelity correction and official-checker block

**Date:** 2026-10-24 KST. **Disposition:** Actual release artifact untouched; detached download/export error detected and corrected by protected ZIP. No official checker or NAS runtime was executed; no submitted package or final user approval.

## Reproducible issue

The immutable GitHub Actions preview wrapper `12560941466` contains the **actual approved-for-internal-preview-only** PDF `ProjectReady_Creator_Proposal_DRAFT.pdf`, **5,183 B**, SHA256:
`df071504716c6121e7606cc1178ba7a3fdaa38856c3482b1b0864fc554088f80`.

A separate direct PDF attachment named `ProjectReady_Creator_Proposal_DRAFT.pdf`, previously provided in chat, was **30,144 B** with SHA256 `460f5f9adbfc7b7ffe43a5f3ea01459e77ed2917ab91fa8482ae31b164742627`. The direct attachment is one page and has the same extracted question/answer text, but **does not byte-match the verified GitHub CI PDF**. A second attempted direct-PDF export was also observed rewritten to **30,144 B** after file exposure, with yet another SHA `e29b010b07a3d92428c6aed0f5e1ef2e469982c74c59bfd4c58d48d928584615`. Both are unsuitable as evidence of exact original binary identity, notwithstanding readable content and size limits.

**Cause status:** The PDF attachment/export path altered bytes during delivery; precise transformation mechanism NOT_VERIFIED. Do not mistake the exported 30 KB PDF for the G22 5,183 B source or call it corruption without content proof. This does **not** demonstrate an error in the GitHub Actions original artifact or final Devpost package; **none has been submitted**.

## Actual correction, verified

Read the real unchanged PDF bytes from the existing GitHub wrapper and nested them inside a **new ZIP** so the file is not rewritten by direct PDF presentation. Created an offline, local-only distribution ZIP `UGREEN_G22_Original_PDF_ByteVerified.zip` containing:

- `ProjectReady_Creator_Proposal_DRAFT.pdf`: 5,183 B / SHA256 `df071504716c6121e7606cc1178ba7a3fdaa38856c3482b1b0864fc554088f80`
- `PDF_SHA256_MANIFEST.json`: source artifact ID, expected hash and release gate limitations.

Outer ZIP size **4,438 B**, SHA256 `0ef56994107dadc31166df25bafd1ae2c7e8555debe0248eb66c638b39103760`; ZIP integrity check PASS and extraction bytes independently matched the original.

This extra ZIP is a **download/verification transport only, NOT the contest Skill ZIP and NOT part of the Devpost submission**. Preserve the G22 original artifact in GitHub Actions. The correct PDF is still marked draft, not approved. Do not mistake plain PDF filename equality for byte equality.

## Current source of truth and next gate

- GitHub G24 verified actual Skill ZIP SHA256 `3885182cb337fdeb66c6424ffb2ff242971b6bb75a1b55319ba2a7e53dbfd947`, extracted exact `SKILL.md` SHA256 `770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169`.
- Previous Codex reported official-checker PASS only for **different, unaugmented** `SKILL.md` SHA256 `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead`. Current candidate **must** be checked against the new SHA, using existing official `uliya-skill-kit` in entrant-controlled Codex. Do not assume a command line interface without first-party confirmation.
- Public first-party starter kit text was rechecked and documents **“Help me check this skill”** as supported creator checker guidance. This session does not have the entrant-installed official checker runtime. An attempt to retrieve the public vendor ZIP directly in the model's isolated container failed due to unavailable network/DNS, so no tool was executed and no official result asserted. No speculative second retry.
- No external NAS/credential/customer data, new payment or deployment. Keep explicit approval for final exact proposal+Skill ZIP and Devpost.

**Calendar/tracking unchanged:** 2026-10-24 original fixed-day plan 100% / planned remainder 0h; actual labor NOT_MEASURED. 24-day overall 2 DONE / 12 PARTIAL / 3 BLOCKED / 7 NOT_STARTED. 2026-10-25 G1 blocked, 1.5h base plus 1.5h separate reserve. Final operational ETA unknown. Relevant first-party documentation: https://ai.ugreen.com/pages/hackathon-starter-kit (Sections 3, 5, 7).
