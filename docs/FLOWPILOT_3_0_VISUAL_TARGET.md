# NAS FlowPilot 3.0 — Visual Target (UGREEN submission)

Date: 2026-10-29
Status: **Design reference only — not proof of implemented functionality or submitted deliverables**
Owner-approved direction: dark-mode engineering Command Center, top E2E pipeline and bottom submission-package cards.

## Desktop layout

- Header: UGREEN AI NAS Hackathon / NAS FlowPilot 3.0 — Natural Language to NAS Automation.
- Top: five horizontally connected cards with clear, readable type.
  1. **Natural Language Request** — Uliya AI chat; user asks to combine sales CSVs into a monthly customer report.
  2. **HAE Interactive Dialogue** — 1–2 turn slot filling: authorized source folder, grouping key, output location, cadence.
  3. **LA Workflow Generation & User Approval** — workflow graph/JSON preview; Reject and Approve & Run; explicit approval required. Describe LA-derived lightweight runner accurately, not as full n8n runtime unless proven.
  4. **Execution & Report Generation** — bounded read-only source CSV scan/merge/group, allowed output report, task trace and success/failure.
  5. **Audit & Safety Report** — SQLite execution ID, timestamp, node trace, source/output evidence, risk decision. Display SOVIA-branded scores ONLY after actual SOVIA adapter is integrated and tested. Sample project score 88% is *illustrative*, not a measured product metric.
- Bottom: four cards.
  1. **Skill Package (ZIP)** — show *actual official-compatible* Skill ZIP contents, not hypothetical `main.py`/`requirements.txt` if unsupported.
  2. **Executive Summary PDF** — English, <=500 words and <=1 MB per repository requirements.
  3. **Demo Video** — 2–3 minute E2E capture as optional/conditional until official Round 1 submission form is checked.
  4. **Devpost Submission Form** — title, short description, supported links and artifacts; do not claim submitted until confirmed.

## Visual design tokens
- 16:9 widescreen, dark navy/near-black canvas, blue/cyan workflow accents, green verified completion, amber approval gates, red blocked/failed actions.
- Large legible labels, restrained glow, high contrast, distinct execution states.
- The workflow graph and actual output/evidence should be most prominent.
- Keep bottom submission packaging visually separate from application runtime.
- No fake execution timestamps, fake official checker pass, fake risk scores, or fake Devpost submission confirmation in actual screenshots.
- For official submission use real product captures and actual test outputs; concept mockups must be labeled as such.

## Engineering acceptance criteria
- Natural language -> missing-slot clarification -> authorized NAS CSV schema -> workflow preview -> explicit approval -> real bounded CSV report -> SQLite trace.
- Validate reject path, unauthorized paths, source-file immutability, output location and failure trace.
- Separate LA generator provenance from Python runner; separate SOVIA/DBVORA adapters from generic SQLite.
- Actual Uliya/UGOS compatibility must be verified; local-only demonstration cannot be represented as NAS runtime proof.
- Preserve existing G68 implementation and canonical Skill; never overwrite submission artifacts without verification/owner approval.

Related: `docs/FLOWPILOT_3_0_ARCHITECTURE_DECISION_20261029.md`.

## Concept image
The 2026-10-29 ChatGPT-generated concept image is the visual reference for this specification. **The PNG is not yet committed to GitHub**; upload it separately to `docs/assets/flowpilot-3-command-center-concept.png` when binary upload is available.
