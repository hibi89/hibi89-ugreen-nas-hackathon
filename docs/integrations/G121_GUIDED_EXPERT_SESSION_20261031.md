# G121 guided NAS file-inspection session (2026-10-31 KST)

## Purpose and choice
A user states a bounded natural-language NAS task; the assistant collects an exact folder and mandatory checklist, displays a redacted plan, obtains two separate explicit consents, then checks official catalog metadata and optionally runs synthetic QA. The result is a user-readable eight-step guide, not a real NAS operation.

- Rewriting a free-form LLM workflow agent with invented Uliya SDK arguments would be costly, error prone and unsafe.
- Selected: reuse G115 exact-intent compiler, existing G2 planner scope checks, G120 SHA-pinned no-execute Expert catalog bridge, G87 normalized receipt assessment, and G116 code-owned fixture QA. The existing G68/G69 guided CLI is specifically for owner LOCAL file metadata; G121 is NAS-PLAN only, never reads a NAS directory.
- Function: tools/flowpilot_guided_expert_session.py, run_guided_expert(goal, ask, emit, kit_loader, normalized_receipts, ...).
- Tests: tests/test_flowpilot_guided_expert_session.py (13 focused).
- Example: python tools/flowpilot_guided_expert_session.py --goal "필수 파일 확인해줘".
- Optional owner-provided public official archive: --official-kit-zip <LOCAL_OFFICIAL_ZIP> --local-synthetic-test. The pinned SHA is checked before the G120 bridge; no downloads, owner uploads or real SDK actions occur.
- Exact token APPROVE_METADATA is followed by independent ACK_UNKNOWN_PROCESSING; absent/declined consent never calls the kit loader. Path traversal, restricted files, multi-intent, unsupported CSV-to-native and deletion blocked. No owner root/file names or raw receipt refs are printed.
- Test-only mocked archive SHA bypass marks SYNTHETIC_CATALOG_TEST_ONLY; cannot establish official kit availability, registered Expert/permissions, native request/response schema, real NAS access or release.
- Full acceptance: exact GitHub Linux+Windows regression; canonical skill/owner-private G103 source unchanged; first-party checker, real Uliya Expert, Docker isolation, proactive live monitoring, submission NOT_RUN/HOLD.

Pending live gate: official registered Expert callable signature and native schema, explicit owner-approved scoped test folder, observed readback, official G103 Checker on exact ZIP and entrant release consent. Official deadline 2026-11-16 16:45 KST.
