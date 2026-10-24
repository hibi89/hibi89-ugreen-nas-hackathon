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

## Verified G14 source and artifact (2026-10-24)
- GitHub source commit **c02b8d24f57732b99af56280cc430374a8bc212c**: [offline CI 40083630790](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083630790) ran **211/211 PASS**, including official-Skill-folder *offline* preflight PASS (NOT actual UGOS checker). [Demo workflow 40083631042](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083631042) **6/6 PASS** plus strict five-case JSON provenance/status assertions. [Master progress CI 40083630878](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083630878) PASS and [handoff sync CI 40083630804](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083630804) PASS.
- Downloaded exact [synthetic demo artifact 12556421327](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083631042/artifacts/12556421327) (expires 2026-10-31T09:51:49Z), inspected `demo_report.json` **6,835 bytes** and `demo_report.md` **2,234 bytes**. All five scenario outcomes matched the original expectation: all present NEEDS_REVIEW; confirmed missing BLOCKED with FAIL; partial listing NOT_CHECKED; denied NOT_CHECKED; three brief candidates CANDIDATES_REVIEW. All five `is_real_nas_validation=false`. Artifact SHA256 ZIP cdecd886d57b1c86d2d107d919a980e1701ff1d882656ee27d0b8c89c9e4146f, recorded only to identify reviewed bytes.
- This artifact is an **optional supplementary offline Python demonstration**, NOT the Devpost skill ZIP or actual creator output. No live NAS or UGREEN registered-agent / checker execution, original license permission, human signoff or Devpost receipt implied. G1 still BLOCKED/NOT_EVIDENCED; D12 and D13 still PARTIAL, overall 24-day count unchanged.
