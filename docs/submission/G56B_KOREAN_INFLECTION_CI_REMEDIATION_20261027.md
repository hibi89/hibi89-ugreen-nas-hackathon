# G56b — Actual CI failure remediation (Korean irregular mutation verb)

Date: 2026-10-27 KST. Source failure SHA `11fc00f19e75bb468f37a6e0d0cc29fbc14bf3b1` on `lead/ugreen`.

## Failed evidence
[G56 FlowPilot CI run 40522317143](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40522317143) failed in `test_korean_uncovered_mutation_requests_fail_closed` with `버전 비교하고 옮겨줘`: `READY_FOR_ADAPTER_CHECK` was returned instead of `BLOCKED`. The previous deny regex checked `옮기` only; irregularly conjugated `옮겨` did not contain that substring. The official-checker workflow failed at the **offline safety tests before the first-party checker step**: do not call G56 an official-checker PASS. G56's PDF owner-preview/readiness jobs failed for the same preceding gate; draft ZIP generation and master/closeout integrity jobs succeeded. No release or NAS execution.

## Minimal remedy and regression
Retain existing English write/transfer inflection patterns. Add only the Korean surface forms `옮겨` and `옮겼` to the pre-plan blocklist and add `옮겼어` to the existing focused regression loop. Avoid weakening tests or changing the canonical contest `SKILL.md`.

## Acceptance
Re-run exact-source Python test discovery (previous verified G55 total 388, G56 adds 4 tests -> expected 392), FlowPilot preview, first-party static checker, closeout and master workflows on corrected commit. **G56b CI unverified until a successful matching run is observed**. Canonical FlowPilot Skill SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` and G52 PDF/ZIP are unchanged. Official FlowPilot Creator NOT_EVIDENCED, real registered Experts/NAS NOT_RUN, rights owner review HOLD, Devpost NOT_SUBMITTED.
