# G122 — Session timeline, synthetic QA evidence, and self-contained HTML (2026-10-31 KST)

## Concrete feature
The G121 interactive NATURAL-LANGUAGE file-check session and G119 SQLite replay-safe synthetic council can now be used in ONE developer-facing workflow. The new tool is tools/flowpilot_session_timeline.py with run_session_timeline(...), render_offline_dashboard(...), and optional explicit create-only HTML export.

Stages: intent classification → exact scope plus two consent gates → official pinned file-agent catalog status → opted-in disposable QA → SHA-256 local evidence verification → owner review and release HOLD. The timeline shows the bounded deterministic Architect/Security/Builder/Repair/QA role statuses and repair count, while never showing owner root/file names, raw receipts, file contents or credentials. All role events require a verified local hash chain first. This is *not* independent audit notarization.

## Choice and risk
- A) Host an always-on dashboard that reaches NAS/SDK/cloud and stores private input. No live Expert permissions and unnecessary external surface/cost; REJECT.
- B) Render a static self-contained HTML report from bounded local G121/G119 results, no JS/CDN/remote URLs, strict CSP, escape all displayed values, and only create a new local HTML file when explicitly supplied; SELECTED.
- Existing G119 run IDs prohibit retry of the same synthetic goal, even if the previous attempt failed; this is **synthetic replay protection**, NOT real Uliya exactly-once or proof of owner scope binding. The CLI demo uses a disposable DB; persistent caller-owned DB required to retain replay protection across CLI invocations. We explicitly do not present ephemeral per-process DB as persistent history.

## Usage
- python tools/flowpilot_session_timeline.py --goal "필수 파일 확인해줘" --run-id run_demo122000 --synthetic-qa
- It asks exact NAS scope and checklist and independent approval tokens; no local NAS metadata inspection, Docker or native Expert invocation occurs. Synthetic tests operate only on disposable code-owned fixture data.
- Optional --inject-test-fault exercises one trusted missing-edge repair, never arbitrary code repair.
- Optional --html-out /absolute/new_report.html writes *new* offline HTML with O_EXCL exclusive-create semantics. Existing files are NEVER overwritten. On Windows select a new local absolute filename, not UNC/network paths.
- Embedded Python function can accept a caller-provided persistent sqlite3.Connection, enabling replay protection across calls; no original user database selected or modified by default.
- Tests: python -m unittest discover -s tests -p 'test_flowpilot_session_timeline.py' -v, plus exact GitHub Linux+Windows full regression.

## Truth / pending
No actual Uliya Expert argument/result schema or registration is verified; official kit first-party G103 Checker NOT_RUN; actual NAS/Docker/native expert never invoked; no live proactive watcher or real production deployment; Devpost NOT_SUBMITTED. ZIP/PDF owner source and canonical Skill left unchanged. All new evidence/status labels include NOT_NAS/HOLD.
