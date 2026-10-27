# G67 — Creator-origin FlowPilot Round 1 ZIP/PDF review artifacts

Date: 2026-10-28 KST. Branch: codex/ugreen-flowpilot-creator. This is a separate candidate preview, not an update to canonical G49 Skill or earlier G52 ZIP/PDF.

## Correct evidence boundary
- G65 Codex operator reports actual interactive official UGREEN Uliya 0.7.3-en Creator usage. No standalone Creator CLI. Creator execution was not independently replayed in CI.
- G66 independently ran the genuine pinned UGREEN official static Checker on corrected skill/creator-candidate/flowpilot-nas/SKILL.md. Candidate SHA256 f7982feae70e773440486fd8b0bee408fbadc69ced82d96d6e761c686f6131a5. [G66 Actions 40547404706](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40547404706) static-pass, 0 errors/0 warnings/0 info; Python 486/486.
- This is static-only: actual NAS, registered Expert, effective permission and data processing location remain unverified. Prior Creator candidate SHA d04ee09e is not the reviewed G66 content.

## G67 separate owner-review preview
- Exact official ten-question source: docs/submission/flowpilot_round1_qas_G67_owner_review.json. Updates Q8/Q10 and AI/Creator disclosure; 392 substantive answer words. Historical QA unchanged.
- Builder: tools/g67_creator_round1_preview.py. Pins exact G66 SHA, fails closed on drift, creates separate 1-page PDF, one-member Markdown-only ZIP and a JSON manifest with exact hashes. Existing G52 builder is unchanged.
- Tests: tests/test_g67_creator_round1_preview.py. Seven new regressions, total minimum 493, plus ZIP byte-parity, all ten questions, disclosures and release HOLD.
- Workflow: .github/workflows/g67-creator-round1-preview.yml, only on candidate branch. Publishes generated PDF, ZIP, manifest and rendered PNG as review-only GitHub Actions artifact, not as tracked repository files.
- All statements distinguish Codex operator-reported official Creator usage from independently reverified static Checker. No claim of real NAS or Expert operation.
- No customer data, vendor code redistribution, NAS trial activation, external publishing or Devpost submission.

## Remaining release gates
1. Review G65/G66 Skill differences, rights, AI/Creator disclosures and proposed entrant-only license; owner explicitly signs off.
2. Verify successful G67 Actions artifact bytes, PDF page count and visual rendering, ZIP one Markdown SKILL.md and 500-word cap.
3. If explicitly adopted, change canonical skill/flowpilot-nas/SKILL.md separately, rerun genuine first-party Checker on adopted exact SHA, rebuild final submission package and get final signoff. Do not auto-merge PR #1.
4. General 3-hour UGOS trial Nov3–5 conditional on actual entitlement, verified rights/capabilities, and owner timer-activation approval.
5. Release HOLD, Devpost NOT_SUBMITTED, NAS/Expert NOT_RUN.

At time of writing, G67 Actions not yet verified; G66 official static Checker applies to the unchanged candidate SHA above, not PDF or ZIP.
