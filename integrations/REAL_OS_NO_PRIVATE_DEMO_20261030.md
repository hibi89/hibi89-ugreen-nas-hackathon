# FlowPilot 3.0 one-click actual OS metadata demo — 2026-10-30

Previously the local UI could do nothing without exact privately checked-out
HAE and DBVORA repositories. The new primary browser button uses the **real
public FlowPilot parser, bounded workflow and OS lstat metadata path** on five
fresh generated disposable folders: required-file success, handoff success,
three-intent version review, missing-file block, missing version candidate.

It calls the existing source-backed `flowpilot_goal_preview.process_goal`
twice per scenario: a no-read preview and a separate metadata-consented run.
The demo never accepts or scans owner-selected paths and returns only safe
state counts. It is *not* private LA execution, SOVIA evaluation, DBVORA
inspection, NAS or Uliya Expert invocation. These are separately labeled
`false`, and release remains HOLD.

Run from Windows/Linux via:
`python tools/flowpilot_real_os_demo.py`
or launch `tools/flowpilot_four_source_local_ui.py` and click the first
"Run 1–3 intent real OS demo" button. No HAE/SOVIA/DBVORA checkout is needed
for this button. All temporary files are automatically disposed before the
safe result is returned.

Added six actual-OS regression tests plus a localhost HTTP endpoint test.
The feature branch remains independent of official G49/G52 contest files.
