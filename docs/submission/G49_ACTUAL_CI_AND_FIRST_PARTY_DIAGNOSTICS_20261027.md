# G49 Root-cause results — observed real GitHub CI, new FlowPilot source

Date 2026-10-27 KST. Branch lead/ugreen. Observed actual logs and not just static workflow YAML.

## Actual remote G48 CI
- G45 first-party official Uliya Skill Kit v0.7.3-en checker run https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40498808367 on old candidate SHA 985713d709aa36ad3e590557aac242be860716834f31eb27ff460bee960184b0. Offline planner/evidence/demo tests: 50/50 PASS. **First-party checker actually executed** in no-network read-only runner but verdict `not-uploadable`, exit 1, errors 6 warnings 2; output JSON produced sanitized artifact 12731742458.
- Diagnostics: DESCRIPTION_TRIGGER_MISSING (warning), DELEGATE_FORMAT_INVALID (error), CAPABILITY_EVIDENCE_MISSING (error), EMPTY_RESULT_HANDLING_MISSING (warning), SKILL_REQUIRED_SECTION_MISSING x4 (errors). No falsely reported static pass.
- Global repo suite run https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40498808477 ran 341 tests, one Python error in test_g42_adversarial_boundaries.G42Adversarial.test_versions_not_authoritative. Caller passed entire requirement tuple `R`, but `detect_version_candidates()` requires one scalar `Requirement`. Corrected the test call `R[0]` without broadening product behaviors. Mirror failure in https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40498808350.

## New distinct G49 candidate
- Source `skill/flowpilot-nas/SKILL.md`, Git blob 22d2b1a418dc0d299661f16ce7038ec16aa829da, SHA256 47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b. Owner-directed FlowPilot four conditional intent selections remain explicit, in addition to the read-only HANDOFF_AUDIT root.
- Regenerated structural format using own earlier ProjectReady G36 first-party accepted headings; it includes # Goal, # Required input, # Generation-time capability evidence, # Orchestration, # Result classification, # Completion and failure, # Safety and disclosure. Defines two guarded, fully scoped `delegate --target ... --instruction` examples and explicit empty/failed/truncated return handling. Document approval remains separate from metadata inspection.
- SDK catalog permissions = unknown and processing location unknown. No confirmation of registered NAS Agent availability. No official Creator run for this NEW FlowPilot candidate. An earlier G36 Creator run and static-pass cannot be inherited.
- Updated first-party checker CI and owner-review PDF ZIP developer builder to pin new candidate sha. Earlier G46 PDF and ZIP remain historical byte-fixed artifacts, not current G49 matching package. Need rerun the exact preview builder before new upload.

## Remaining gates
Read newly triggered G49 CI via GitHub Actions run ID and sanitized logs. If checker still has diagnostics, fix exact source, repin hashes and rerun; never claim success based on plausible layout alone. Then obtain official Creation Tool provenance, execute accepted finalist NAS only if provided, and have entrant review actual English 10-Q PDF + exact Skill ZIP and rights disclosures. No Devpost submission.
