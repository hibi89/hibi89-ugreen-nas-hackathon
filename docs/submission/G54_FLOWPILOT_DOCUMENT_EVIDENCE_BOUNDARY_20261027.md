# G54 — FlowPilot selected-document evidence boundary

As of 2026-10-27 KST. Baseline `786cc8af44798abe3f471357351fefe588ef17a3`. G53 prior [376/376 offline CI PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40511850824); **G54 CI pending**.

## Reproduced code-level hazard
The offline planner formerly retained a document-agent step for a mismatched authorized root, or when a selected reference was attributable to one valid observation but the evidence report correctly marked the same file NOT_CHECKED (untrusted duplicate) or VERSION_REVIEW (competing candidate). A dataclass truthy string in permission flags also counted as authorization. None of these establish actual NAS execution.

## Alternatives and chosen minimal fix
- Chosen: reuse the existing evidence classification; allow selected-document plans only for unique, unequivocally PRESENT checklist references; remove document step for wrong-root plans; use exact booleans for inventory flags. No NAS/SDK calls, costs, or historical artifact changes.
- Deferred: wholesale planner/adapter redesign requiring unverified vendor behavior, extra complexity and migration risk.

Six synthetic regression tests now cover untrusted duplicate, competing version, reused cross-path reference, root mismatch, truthy-string planner authorization and truthy-string evidence authorization. Full tests/CI must verify after the code commit; **no success inferred from writing source**.

Original FlowPilot `skill/flowpilot-nas/SKILL.md` source SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b`, its first-party static checker 0/0/0, and G52 PDF/ZIP are unchanged. New official Creator: NOT_EVIDENCED; registered Experts and real NAS: NOT_RUN; rights/exact owner release: HOLD; Devpost: NOT_SUBMITTED. No production deployment or measured time.
