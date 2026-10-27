# G48: FlowPilot executable offline NAS evidence demonstration

Date 2026-10-27 KST, lead/ugreen. This feature runs only on synthetic in-memory fixtures, does not read NAS or user files, and does not deploy or contact vendor Agents.

## Executable proof of the current offline logic
`python tools/flowpilot_offline_demo.py` prints deterministic JSON. `python tools/flowpilot_offline_demo.py --output /tmp/g48.json` writes only the developer-selected local QA file; production Skill ZIP DOES NOT include the Python tool.
Five scenarios: all requested files listed and attributable, missing required file after simulated complete authorized enumeration, two conflicting candidate versions, denied or truncated listing, symlink containment unknown. Corresponding states are PRESENT/PRESENT (overall NEEDS_REVIEW as no real NAS), MISSING (BLOCKED), VERSION_REVIEW, NOT_CHECKED and NOT_CHECKED. No arbitrary file content is opened.
Run `python -m unittest discover -s tests -p test_flowpilot_demo.py -v` to validate eight G48 cases. Local G44+G47 evidence and G48 scenario tests total 30/30 PASS in Python 3.13, identical byte sources confirmed by git-blob SHA: demo 3ff02254c83132640cf94de951e1dee4c4e8dc6b and tests aaf3a6ad7f48310a2fd4345bf9b22683e65ca42b.

## CI and unsupported claims
Official checker and preview workflows plus offline workflow updated to include all 18 G43 planning + 16 G44 evidence + 8 G47 adversarial + 8 G48 demo test methods; >=50 discovered required before first-party checker proceeds. A push workflow may or may not run; full 50/50 CI result and first-party Uliya checker receipt are NOT independently observed.
The official Uliya Creator was NOT run on FlowPilot, actual registered Agent delegation NOT observed, NAS runtime NOT_RUN. Do not say 'official checker passed' until actual external job verifies exact Skill SHA. G36/G37 ProjectReady archive, new G46 one-page PDF, ZIP and original FlowPilot SKILL.md preserved. Devpost NOT_SUBMITTED, owner rights/approval HOLD.

## Remaining goal vs original design
Dynamic text task planning is keyword-bound and not a general purpose workflow graph. Evidence output is synthetic demo of policy contract, not actual NAS output. To advance, obtain official Creator-generated source or approved re-generation, registered Agent invocation/permission and real data-flow details, and a human participant-reviewed PDF ZIP with exact receipt. External third-party connectors, native n8n reimplementation and NAS execution remain unimplemented by contest intent.

Next: observe GitHub Actions run IDs with verified logs; run first-party checker on exact SHA; preserve Markdown-only ZIP policy and owner final signoff.
