# G98 — Official Round 1 rules + independent owner-artifact acceptance — 2026-10-31 KST

## 1. Goal / confirmed architecture
NAS FlowPilot 3.0 is a Uliya Markdown-only registered-expert Skill for owner-scoped project handoff audit, missing required files, versions, and separately authorized document summaries. The HAE / Lightning Azent / SQLite Python integration is an existing **development-only local backend**, not a Uliya executable or a component of the Round 1 Skill ZIP. Preserve both.

## 2. Official rules rechecked (2026-10-31)
- Official rules: https://ugreenhackathon.devpost.com/rules
- First-round deadline: 2026-11-15 23:45 Pacific Standard Time = **2026-11-16 16:45 KST**.
- Round 1 requires an initial Markdown-only Uliya Skill ZIP and an English PDF answering ten prompts with at most **500 substantive words**, PDF no more than **1MB**, ZIP no more than **10MB**. Supporting ZIP Markdown references only; no executable Python/JS, manifest, credentials, or binaries.
- **Round 1 explicitly does not require NAS runtime evidence, repository link, or a demo video.** Official remote NAS access is allocated only to invited finalists (invitations November 21, assigned NAS testing November 22–28, 2026). This supersedes the mistaken implication that a three-hour NAS trial is required before first-round release. Any separately available three-hour trial remains an independent owner-approved optional access mechanism, not a verified event requirement.
- Real registered Uliya Expert/native-result-schema and actual NAS execution are still unverified, but are **not standalone grounds to block a truthful Round 1 pretest proposal**. Creator tool provenance, IP/rights, exact package acceptance and human authorization remain independent required review gates.

## 3. Actual owner-artifact QA executed
- Owner-provided file `SKILL(2).md` SHA-256 `2ac1b6c656c57443c63ee71b0d03b81a286845da230e9bdf068066d08f16dac7` (8174 bytes), previously captured as G79/G80 creator-reported candidate `flowpilot-3`. **Official Creator execution is only owner-reported**, not independently replayed.
- Independently opened previously supplied `UGREEN_G80_FLOWPILOT3_CREATOR_PAIRED_QA_FIXED.zip` in a local isolated container. Checked nested ZIP `NAS_FlowPilot3_Creator_R1_OWNER_REVIEW.zip`: exactly one member `flowpilot-3/SKILL.md`; CRC PASS; uncompressed SKILL bytes match supplied source SHA and manifest. Nested ZIP 3337 bytes; SHA-256 `cb2697051346c453f0e6c2c6ed06fed4d35248ea6f55c62320b6f4d3f336c89d`.
- Checked nested PDF `NAS_FlowPilot3_Creator_R1_OWNER_REVIEW.pdf`: 5179 bytes; SHA-256 `e64960480c3d6ccfc3273a70186d51122d68dd7a61969dcd73a6c8942da18809`; pypdf extracted Q1..Q10 in exact sequence; 1 page, visually rendered and inspected with no clipping observed; G80 proposal source manifest counts **345 substantive English words** (builder count, independently checked hash, not an independent re-tokenization).
- PDF explicitly says NOT SUBMITTED and discloses owner-reported static validation warning.

## 4. Exact checker / native gate
Owner-reported official Checker: `static-pass-needs-target-validation`, 0 errors, **1 warning `DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE`**. This checker execution was NOT independently rerun this session because the official public kit download failed in the independent environment. Do NOT upgrade that owner report to a zero-warning first-party result or claim actual registered Agent / NAS / Creator replay. A SHA-pinned public catalog provides read-action identifiers, not native expert invocation/return schema.

## 5. Architecture and implementation comparison
A. Guess live Uliya command syntax and pretend permission from catalog labels: fastest-looking but unsafe, unverifiable and breaks contest assurance; REJECT.
B. Keep verified read-only candidate and independently checked PDF/ZIP, resolve documented static warning via genuine supported Creator/Checker with real target binding (owner-led), then exact-source rights and release review: no incremental API cost, preserves design, fits Round 1 rules; SELECT.
Existing Python G97 source and tests remain untouched (source SHA `c8f808c674626a9199c8e70f6a89e1a3bf6c5370`).

## 6. Verification / failures
G97 at exact code SHA: https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41185305168 Linux 888 total / 883 PASS / 0 FAIL / 5 SKIP and Windows actual PowerShell full PASS. Related readiness/master/closeout all success at G97 SHA. G98 local artifact QA structural/hash/visual PASS; official Checker rerun NOT_RUN; native NAS NOT_RUN. No further full backend CI was necessary for documentation-only G98.

## 7. Remaining / release hold
**ROUND1_ARTIFACT_STRUCTURAL_QA_PASS; RELEASE_HOLD**. Entrant ownership/originality and third-party rights, Creator provenance / exact checker issue, third-party disclosure acceptance, exact final ZIP/PDF decision, and authorized Devpost submission are still pending. Do not silently overwrite G49 `skill/flowpilot-nas/SKILL.md` with the G80 `flowpilot-3` candidate (names differ); do not change originals or publish without explicit entrant approval. No actual user NAS access, external upload or payment performed.

## 8. Repo / branch / backup
`hibi89/hibi89-ugreen-nas-hackathon@lead/ugreen`. G97 code `c8f808c`; G97 docs-only `1d739d2`. Full git history acts as backup. Old canonical Skill and G52 originals unchanged; G80 supplied archive was inspected separately without publication or embedding in the repository. No Vercel production URL (NOT_APPLICABLE).

## 9. Priority / acceptance
P0: independently resolve the specific delegation warning using supported official Creator/Checker tooling, without invented SDK interface. P0: get explicit owner rights and exact-package approval for the **pretest** ZIP/PDF; use Devpost only after authorization. P1: optional native expert and NAS work when genuine, authorized access becomes available, in particular if selected for November 22–28 finalist testing. Avoid redundant synthetic backend expansion.

## 10. Status provenance
2026-10-31 KST. This G98 record is a new compact authoritative checkpoint because root `HANDOFF.md` (~185k chars) and `STATUS.md` (~78k chars) are oversized historical append-only documents; an earlier attempted bulk update was blocked by GitHub connector safety validation. The root documents still begin with G96, while `docs/roles/lead/G97_HANDOFF_20261031.md` remains the last verified source-code closeout. Read this G98 checkpoint and G97 checkpoint together before next edits. GitHub commit SHA for this document is the enclosing commit, not a preselected hash.
