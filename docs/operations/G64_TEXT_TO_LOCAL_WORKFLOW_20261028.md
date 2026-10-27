> **2026-10-28 G64 VERIFIED:** Code SHA ef4f45bcabea198e97c41bbfb6983f16bf4eda77, [FlowPilot CI 40539218786](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40539218786) **486/486 full Python PASS; G64 14/14 PASS**; master 40539218779, closeout 40539218725, readiness 40539218783 all SUCCESS. Only deterministic Korean/English text-to-local metadata workflow; NOT official Uliya/NAS/Creator, release HOLD, Devpost NOT_SUBMITTED, hours NOT_MEASURED, owner separate HAE/LA/REA_APP and original Skill/G52 artifacts unchanged. 3h UGOS Nov3–5 conditional access and owner timer activation.

# G64 — Korean/English bounded text workflow (2026-10-28 KST)

Goal: remove JSON recipe authoring from the existing G63 **real local file-metadata** vertical slice. Parse a strictly documented tiny language into the same guarded G63 engine. This is deliberately not unrestricted natural-language understanding, ML, a NAS agent or a production-ready orchestration platform.

Comparison (performance/cost/maintenance):
- **A (chosen):** deterministic standard-library Korean/English labeled instructions, 0 external calls, bounded, reproducible and testable; handles only named phrases.
- **B (deferred):** remote LLM extracts arbitrary user intent, potentially flexible but adds runtime costs, non-determinism, external transmission and mandatory untrusted-JSON revalidation. Not authorized for the current zero-cash read-only development slice.

Use only a disposable and stable owner LOCAL directory (not mapped NAS):

    python tools/flowpilot_text_workflow.py --root /absolute/local/test-folder --instructions "파일 확인: README.md; 버전 비교: final.pdf => final_v2.pdf" --approve-local-metadata

Supported explicit labels:
- check files / check required files / 파일 확인 / 필수 파일 확인 / 누락 확인 : comma-separated exact relative names
- compare versions / review versions / 버전 비교 / 최종본 비교 : one exact base => one or more comma-separated exact candidate names
- check handoff / handoff audit / 납품 확인 / 인계 확인 : comma-separated exact relative names
- Separate up to eight clauses with semicolons or newlines.

No filename guessing; unsupported free language, write/transfer intent, missing boundaries, unknown actions, path traversal or secret-bearing paths are refused. G63 validates all steps before touching the root; explicit CLI consent is required for each invocation. Missing/ambiguous/unknown files remain BLOCKED/NEEDS_REVIEW, and outputs have no path or filename disclosure. Selected folder **file contents are never read**, with no network, subprocess delegation or filesystem mutation. This CLI is entirely outside official Round1 Skill ZIP.

Acceptance: 14 G64 focused tests, real temporary-file 2-step and Korean CLI E2E, no-consent and before-read refusal, output redaction, bounded input, missing-step fail-close. Verify exact GitHub CI; do not infer live official Uliya SDK, registered agent, NAS, Creator or Devpost. Original Skill SHA256 47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b; G52 preview PDF/ZIP preserved. 3h UGOS trial Nov3–5 remains conditional on documented access and owner approval.
