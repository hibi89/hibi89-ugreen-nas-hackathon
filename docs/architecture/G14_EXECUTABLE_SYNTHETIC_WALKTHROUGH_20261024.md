# G14 — Executable synthetic evidence walkthrough (2026-10-24 KST)

## Why
The submission Skill contains a clearly labeled hypothetical report, but the five underlying Python core behaviors were previously scattered across unit tests. Reviewers need a reproducible **actual execution of the local prototype logic**, distinct from an invented mock output. This G14 task uses the existing `src/projectready` engine unchanged and exports two human-readable/structured artifacts from five fixed simulated cases.

## Implementation, strictly offline
- `tools/offline_demo_walkthrough.py`: imports `projectready.combined_report.assemble`, `presence`, `readiness`, `policy_guard`; no filesystem scan, network, shell, NAS, credentials or SDK execution. Writes only two local files to an explicitly given output directory: `demo_report.json` + `demo_report.md`.
- `tests/test_offline_demo_walkthrough.py`: asserts all-present-but-not-READY, simulated truly-missing BLOCKED, truncated scan `NOT_CHECKED` (not false MISSING), denied permission `NOT_CHECKED`, competing version candidates `CANDIDATES_REVIEW` with no auto-confirmed version. Also verifies provenance labels, stable report and privacy gate `NOT_CHECKED`.
- `.github/workflows/offline-demo.yml`: tests and generates an **independent non-submission artifact** from GitHub CI, short retention 7 days. Does not place synthetic evidence inside the Devpost Markdown Skill ZIP and does not alter the canonical PDF.
- The existing core **expects `EvidenceOrigin.SDK_VERIFIED` and adapter-verified booleans for the hypothetical complete-scan branches**; here they are deliberate ***fictional premises***, not an implementation claim. Every output says SYNTHETIC, source refs start `synthetic-proof-`, and every case has `is_real_nas_validation=false`. Official NAS runtime, official SDK Agent, licensing and real dataflow remain unknown/NOT_RUN. Do not confuse exercise of a code branch with proof of UGREEN integration.

## Five case contract
| Case | Expected brief | Expected handoff | Overall | Why |
| --- | --- | --- | --- | --- |
| `all_present` | PASS | PASS | NEEDS_REVIEW | independent privacy/version gates cannot be certified |
| `confirmed_missing` | PASS | FAIL | BLOCKED | hypothetical complete scan truly lacks handoff |
| `partial_listing` | PASS | NOT_CHECKED | NEEDS_REVIEW | truncated scan cannot prove absence |
| `permission_denied` | NOT_CHECKED | NOT_CHECKED | NEEDS_REVIEW | no access/real evidence |
| `version_ambiguity` | PASS | PASS | NEEDS_REVIEW | versions require independent human approval |

## Scope and alternatives
**Selected**: deterministic artifact from existing engine plus meaningful contract tests. **Rejected**: rewriting the same G2/G5 decision logic as another mock service; faking an official Uliya Skill Creation Tool; adding an unsupported NAS integration; making a demo video a Round1 release condition. All increase cost/overclaim risk. Generated files are **supplemental proof only**, not extra required official submission files.

## Verification and status
- **Source CI PENDING until new GitHub run is observed**; previously G13 source 1b3e0c6 had 205/205 offline unit tests PASS, one-page PDF and 4-Markdown ZIP DRAFT; no change to official eligible artifact content from G14.
- Owner-managed official Creator use remains **NOT_EVIDENCED** (see `docs/submission/G12_OFFICIAL_CREATOR_CODEX_RUNBOOK.md`), official checker/NAS `NOT_RUN`, third-party rights/editorial/signoff `PENDING`, Devpost `NOT_SUBMITTED`. The demo's static `SDK_VERIFIED` hypothetical flag cannot satisfy the first-party tool use condition.
- Calendar mapping: UGR-D12 (combined orchestration offline demo) and UGR-D13 (CORE/EDGE synthetic demonstration); remain `PARTIAL` until original official runtime and end-to-end acceptance criteria verified. 24-day DONE 2/PARTIAL 12/BLOCKED 3/NOT_STARTED 7 (unchanged). Oct24 original committed finite-day 100% and 0h assigned remainder; actual labor unmeasured. Oct25 SDK G1 budget 1.5h base +1.5h separately reserved; real completion ETA unknown. Additional spend 0.

## Next
Observe new GitHub offline-demo artifact and test output; diagnose any failures, record exact workflow ID/source SHA. Official Creator operation in owner-controlled Codex is still the next external prerequisite for Round1 and should not be postponed for further purely synthetic test counting.
