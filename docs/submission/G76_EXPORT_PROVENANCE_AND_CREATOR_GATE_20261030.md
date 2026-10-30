> **G76 detached-PDF export hazard (verified again after chat attachment):** Exposing an extracted PDF directly as a sandbox download resulted in that *detached working copy* being transformed from 5,137 bytes into 30,098 bytes; the mechanism is not established. The immutable **archive member** retained the exact CI SHA. The recommended verified user deliverable is **one ZIP only**, `/mnt/data/UGREEN_G76_CI_EXACT_BYTES_ONLY.zip`, constructed directly *in memory* from previously downloaded CI archive members, with the original five verified files plus a separate G76 provenance JSON. It was checked byte-for-byte **after** creation and again after export: outer ZIP SHA256 `b36d172707e1f8278063fd6ce4f3439ae63be10b3534b361a6f3dbff5db12409`, inside PDF SHA256 `1ca7c52761ce3764ee5feaf8092eaeb12d85f670069ea51289482e7a794cc6d8`, size 5,137, inside Skill ZIP SHA256 `06127d6da75a958d57524ac1c39294f4f7f366bba925af187280891df9d76bce`. **Do not give individual extracted PDF as an exact official CI byte copy without rehashing it after surfacing.** Earlier failed attempt to package the already-surfaced local PDF was rejected by the hash check and must not be distributed. Creator/rights/Devpost still HOLD.\n\n# G76 — Exact G75 artifact export and official Creator release gate

**Date:** 2026-10-30 KST. **Status:** Offline artifact-byte and regression proof complete; **official Creator and entrant release are not verified**. This document does not license, replace, publish, or submit a Skill.

## Concrete G75 export discrepancy

The actual [G75 CI run 41073132653](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41073132653) artifact **12985507108** contained a PDF of **5,137 bytes**, SHA256 **`1ca7c52761ce3764ee5feaf8092eaeb12d85f670069ea51289482e7a794cc6d8`**. During G76, previously supplied detached local files named similarly had been transformed into **30,098-byte PDFs** with **different** hashes. They are **not exact copies** of the reviewed G75 CI PDF and **must not be used as provenance-matched submission artifacts**. Exact mechanism of the later modification is not verified.

Recovered exact files **without overwriting** the older detached copies, from the already downloaded CI archive `/mnt/data/UGREEN_G75_FlowPilot3_R1_REVIEW_FINAL.zip` into `/mnt/data/UGREEN_G76_exact_original/` (model workspace is temporary, not a persistent repository). Independently recomputed:
- PDF: 5,137 bytes, SHA256 `1ca7c52761ce3764ee5feaf8092eaeb12d85f670069ea51289482e7a794cc6d8`; 1 page, 10 official responses, 360/500 English substantive words according to exact CI manifest.
- Skill ZIP: 6,466 bytes, SHA256 `06127d6da75a958d57524ac1c39294f4f7f366bba925af187280891df9d76bce`; exactly `flowpilot-nas/SKILL.md`.
- Unpacked entrant Skill: SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b`, same canonical source pinned in public CI.
- G75 2x PNG: SHA256 `c5e08b74167b8a070a433b388c83872a27a4c83edf82856a9c6262f7b053b16b`; G75 geometry CI passed. This is a technical bound-check, **not entrant visual/editorial signoff**.
- Creator invocation **NOT_EVIDENCED**; registered Uliya Expert and real NAS **NOT_RUN**; Devpost **NOT_SUBMITTED**; owner rights/release **HOLD**.

## Durable safeguard and executed verification

Added `tools/flowpilot3_export_integrity.py` with **default pinned G75 hashes**. To audit a downloaded **unmodified G75 Actions archive**, run:

```powershell
python tools/flowpilot3_export_integrity.py --archive ".\G75-actual-ci-artifact.zip" --pdf-copy ".\NAS_FlowPilot_3_Round1_OWNER_REVIEW.pdf" --skill-zip-copy ".\NAS_FlowPilot_3_Round1_OWNER_REVIEW.zip"
```

It checks five actual archive members (PDF, Skill ZIP, manifest JSON, rendered preview PNG, visual QA JSON), exact file SHA, metadata and hold state, inner Skill bytes, and optional detached-copy byte identity. Unexpected scripts/extra/duplicate members, symlinks, changed PDF, changed ZIP, altered approval or Creator claims **block**. Nonzero exit `2` and path-redacted status `BLOCKED_EXPORTED_ARTIFACT_INTEGRITY`; successful exit `0` means **only source bytes verified**, not Creator or legal release. The archive is available as a GitHub workflow run artifact with short retention; keep an owner-local backed-up copy. The test suite generates only synthetic ZIP/PDF fixture data; it does not turn a fake PDF into first-party Creator/NAS evidence.

New `tests/test_flowpilot3_export_integrity.py`: 11 unit regressions. Exact feature SHA `77e1c2ac41abd1c4cf996315be2c6963d75820af`, [G76 full FlowPilot CI run 41074501317](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41074501317): **723 executed, 719 PASS, 0 FAIL, 4 SKIP**. This is an offline public CI proof; no private engine, NAS or Creator is installed there. Original PDF, ZIP, Skill and G52 artifacts were not modified by this work.

## Authoritative external requirements rechecked on 2026-10-30

Official [Devpost rules](https://ugreenhackathon.devpost.com/rules) and [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) state:
- **Round 1 closes November 15, 2026 at 11:45 p.m. Pacific = November 16, 2026 at 16:45 KST**. Requires a separate English PDF with ten substantive responses totaling <=500 English words, PDF <=1 MB, and a restricted Markdown-only initial Skill ZIP <=10 MB. **Real NAS, public demo, video, and repository link are not Round 1 requirements.**
- Required official **UGOS Skill Creation Tool** must actually **create** this contest Skill through a supported assistant (currently Codex, Claude or WorkBuddy); a Uliya first-party static checker PASS of an existing source cannot stand in for actual Creator invocation. Our tool inventory does **not** contain that official installed assistant Skill; cannot independently assert the step was completed.
- Entrant originality, developer-tool/vendor source and applicable third-party component rights, AI use and planned external data flows must be truthfully represented. Earlier [G50 support clarification](G50_SUPPORT_LICENSE_AND_ZIP_AUDIT_20261027.md) reported no separate applicable standalone kit license and a permitted option to choose an open-source license for *entrant-authored* text; this does **not** automatically grant license/redistribution rights over the UGREEN kit. Entrant selection of MIT and external release remain **unapproved**.
- **Finalists, if selected Nov21, receive an assigned NAS testing day and credentials from UGREEN**; do not treat the earlier speculative 2h/3h owner trial notes as the official guaranteed access window. Actual expiry/permissions follow future official instructions. Real-NAS use requires the entrant's separate approval.

## Single genuine Creator decision point (cannot be faked with another mock)

The pinned public Skill can be provided as a **reference specification**, not disguised as a Creator-generated output. In an **owner-authorized supported Codex/Claude/WorkBuddy installation**, use the **vendor-provided official kit** (not a generic builder) to: inspect feasibility; generate a newly authored `flowpilot-nas/SKILL.md` in an isolated scratch folder; run the vendor's checker; retain exact sanitized tool/kit version, output SHA, command/check outcome, and source-diff evidence. **Never copy vendor-kit source to public GitHub or include Python/JS/kit assets in the contest ZIP.**

Feed the result through already implemented `tools/g57_flowpilot_creator_candidate_intake.py` and `tools/g53_flowpilot_creator_gate.py` to inspect structure and record *attestation only*. If the generated Skill differs from pinned `SKILL.md`, preserve the original; perform entrant behavioral/legal review, exact-source first-party checker and **fresh** PDF/ZIP generation, verification and new hashes. **No automatically submitted or approved version is created by G76**.

**Owner decisions before release:** review exact current PDF content; confirm entrant ownership/originality and license selection, actual new-FlowPilot official Creator use, third-party source and dataflow declarations; approve exact final SHA/Devpost action. Release stays `HOLD`; no NAS trial/Devpost action may run without that approval.
