# G115 — bounded NL task compiler + two real disposable-fixture tests (2026-10-31 KST)

## Existing components, options and decision
- Existing verified G114 CSV builder/test/guide remains unchanged. Existing G62 local metadata inspector already supports explicit scope, permission, symlink and restricted-path checks.
- Option A: build a separate arbitrary-code workflow engine with guessed NAS/Uliya SDK — high complexity, wrong privileges and untestable external contract; rejected.
- Option B **selected**: one small typed intermediate representation selecting allowlisted CSV aggregation and read-only required-file checks; reuse existing tested local engines behind **disposable fixture only**. Lower cost/risk, incremental extension path.
- Real HAE/Lightning Azent module reuse deferred until exact SHA, licensing, callable contract and need are verified. No private source copied into this public repository.

## Code/contract
`tools/flowpilot_task_compiler.py` exports `compile_goal(goal)` and `run_compiled(goal)`. Contract `flowpilot-typed-workflow-v1`; output graph contains typed nodes, ordered edges, read / new-file-write / compute access classification, and separate real-data consent flags. It never grants actual owner access.
Supported exact natural-language tasks: existing bounded customer revenue CSV phrases and `필수 파일 확인해줘` / `누락 파일 확인해줘` / `check required files` / `check for missing files`. All arbitrary or compound, mutation, scheduling, export tasks WAITING_USER_UNSUPPORTED_WORKFLOW with no execution.

CSV test uses G114 pre-existing malformed disposable CSV → corrective fixture replacement → approved local report → hash/SQLite/duplicate guard. Required-file test uses **actual OS lstat** on an automatically deleted temporary folder: explicit local metadata permission preview, missing required `release/final.pdf` blocks, add fixture only, recheck both PRESENT and original test source intact. Neither path uses owner's NAS or folder, nor proves vendor Expert/UGOS availability. No standalone NAS scheduler or production deploy.

## Safe invocation
`python tools/flowpilot_task_compiler.py --goal "필수 파일 확인해줘" --compile-only`
`python tools/flowpilot_task_compiler.py --goal "필수 파일 확인해줘"`
`python tools/flowpilot_task_compiler.py --goal "고객별 매출 보고서 만들어줘"`

CLI JSON is ASCII-safe for Windows PowerShell. Produces typed workflow graph, executed synthetic test receipts, and actionable Markdown user runbook. Never call it against real NAS data.

## Verification / limitations
Focused `python -m unittest discover -s tests -p 'test_flowpilot_task_compiler.py' -v`; GitHub Action exact SHA required for PASS claims. No vendor kit calls, no official G103 checker, no real Uliya/NAS/Creator, no Devpost. The original canonical `skill/flowpilot-nas/SKILL.md`, private G103 candidate, user documents, HAE/LA repos, and 24-day master are untouched. G113 wider product acceptance goal remains to create and validate user-selected workflows, NOT just inspect files; this G115 proves two bounded existing templates, not general synthesis.

## Next
Extend typed node IR with typed input/output contracts and a safe template selection UI; add explicit test-case-driven build repair for templates, capability discovery adapter and a separate owner-approved real NAS gate when supported. Official 0.7.3 G103 first-party Checker and exact-file release rights remain independent P0 blocks. Real NAS 3h trial requires separate owner approval. Round 1 deadline: 2026-11-16 16:45 KST.
