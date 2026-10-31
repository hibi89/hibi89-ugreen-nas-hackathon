# G119 — deterministic replay-safe evidence + consent-gated proactive proposals (2026-10-31 KST)

G119 is an **offline-only** developer feature. It neither reads owner NAS nor schedules a daemon. It reuses G116's tested Architect/Security/Builder/QA council and G117's opt-in numeric signal evaluator.

## Code added
- `tools/flowpilot_repair_ledger.py`: caller-provided SQLite connection; atomic run-ID reservation before calling the bounded existing fixture test; duplicate run and conflicting goal key refuse replay; limited event chain records role PASS/REJECTED, exact fixed template, terminal PASS/BLOCKED. Chain digests detect naive local mutations but are **not remotely anchored or cryptographically notarized**. Unknown tasks and unsafe IDs never execute. Exceptions sanitized. CLI stores only in a temporary SQLite DB; future owner-local persistence would require separate scope approval.
- `tools/flowpilot_proactive_policy.py`: pure state-in/state-out evaluation over unverified operator-provided numeric fields; no consent → no proposals; at most 2 proposals/tick, 3/hour, deduplicated IDs, refuses backwards timestamps/unknown state. No NAS telemetry source, no watcher, no email/notifications, no autonomous fixes.

## Demonstration
`python tools/flowpilot_repair_ledger.py --goal "필수 파일 확인해줘" --run-id run_G119demo1234 --inject-test-fault` proves missing synthetic graph edge rejected then repaired with one canonical fix and QA, while journal checks integrity. `python tools/flowpilot_proactive_policy.py --telemetry-json '{"disk_used_percent":96,"repeated_error_count":4}' --now 1000 --opt-in` proposes human-reviewed alerts only.

## Security and truth
No private G103 release files or original Skill changed; no Docker, Uliya registered Expert, customer data, live NAS or external API calls. The real NAS integration and verified Docker isolation gates remain independent and are NOT_RUN. Tests: `python -m unittest discover -s tests -p 'test_flowpilot_repair_ledger.py' -v` and `test_flowpilot_proactive_policy.py` and the full GitHub Actions Linux+Windows suite at exact source SHA.

## Next
Use trusted platform operation IDs and signed/anchored receipts only after actual official Expert adapter/authorization; integrate capped proposer state in an opt-in service with real provenance, storage and revocation (not enabled here). Obtain official G103 checker and owner submission permission separately.
