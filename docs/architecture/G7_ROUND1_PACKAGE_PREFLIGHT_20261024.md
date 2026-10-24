# G7 — Round 1 Markdown-package preflight and attribution (2026-10-24 KST)

Status: OFFLINE_PREFLIGHT_ONLY. Official Skill Creation Tool validator NOT_RUN, NAS NOT_RUN, Devpost NOT_SUBMITTED.

## Official requirements
UGREEN Official Rules: https://ugreenhackathon.devpost.com/rules . Pre-test ZIP must contain SKILL.md and directly linked Markdown references only. Maximum ZIP and uncompressed size 10MB each, per-file 1MB, no more than 100 files, frontmatter 2–64-char lowercase-hyphen name and description no longer than 1024 chars. AI tool, component and data-flow attribution must not be omitted. The official tool still takes precedence over this offline approximation.

Starter Kit: https://ai.ugreen.com/pages/hackathon-starter-kit . Public guidance names Files/Documents capabilities but not the exact registered Expert Agent CLI, input/output, permissions or license text. Previously obtained official ZIP metadata is not equivalent to verified CLI internals. G1 remains BLOCKED.

## This advance
- Added developer-only tools/round1_package_audit.py. It validates package shape, required frontmatter, reference links, size/cap, forbidden scripts, symlinks, plaintext credential patterns and unfinished markers. It can generate reproducible local ZIP on explicit --output, but is NOT an official validator or release instruction.
- Added tests/test_round1_package_audit.py with 14 offline positive/negative scenarios.
- Added references/attribution.md and a direct SKILL.md link. It describes AI assistance, no bundled third-party code, platform dependency, unresolved SDK licensing and external-data uncertainty.
- Existing test_skill_candidate.py checks are updated to expect both directly linked Markdown references.
- This is a preparation task pulled forward from Nov 7–9 package inspection. It does not advance or clear the G1 official SDK gate, package freeze, PDF, NAS testing or Devpost submission.

Options comparison: strict offline static preflight (zero incremental cost, deterministic, catches ZIP mistakes) vs immediate supposed official SDK integration without exact evidence (unsupported and misleading). First is selected without treating it as official compliance. Third option after package access is the actual Uliya validator; required for final approval.

Daily accounting: Oct 24 fixed delivered work 100%, 0 scheduled hours remaining; this G7 completed independent scope is additional without double-counting. Real active time NOT_MEASURED. Oct 25 G1 scheduled 1.5h plus separate 1.5h reserve; completion ETA cannot be promised.
