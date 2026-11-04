# G253 — Real local Docker typed-plan failure and bounded copy repair

- Goal: prove a new failure class that G237 did not cover: fixed typed DAG instruction corruption (real container exit 11), followed by exactly one explicitly approved fix of a disposable plan COPY and independently verified real Docker retest (exit 0 and exact G235 report).
- Options: arbitrary agent/LLM plan repair (unbounded, cost/permission risk; rejected) versus fixed code-owned exact plan patch (chosen: deterministic, zero external API, auditable).
- Command on Linux CI with verified local Docker and C compiler: `python3 tools/flowpilot_g253_typed_plan_repair.py --approve-synthetic-typed-plan-repair`.
- Safety: no Docker pulls/network/host mounts, nonroot/readonly/cap-drop resource constraints, random names, scoped cleanup, unchanged CSV and binary, unchanged failed original image; explicitly NOT NAS/registered Uliya Expert/general self healing. Local Python policy tests without Docker do not validate actual isolated execution.
- Whole-product rubric: G252 62/100. VERIFIED new **Local isolation/failure repair/retest** point 8→9, whole-product 63/100 after exact final source `55250b597af6b7be549657f48f9b7d81df076a61` passed G253 real Docker 41871744175, Linux/Windows full 41871744049, readiness 41871744056, master 41871744046 and closeout 41871744014 (5/5 final SUCCESS). Do not repeat G237 CSV decimal correction. RELEASE HOLD / NAS NO-GO; official Creator/Checker and Devpost still outstanding.
- Rollback: ordinary revert of one G253 feature commit, no force push. No change to Skill or owner source.
