> **2026-10-28 G60 CODE + TRIAL RESCHEDULE VERIFIED:** [source commit ecaef27](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/commit/ecaef27c46fe3c16f8eb7ffbea5359249d58a1da) — [full Python offline test CI 40530986782](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40530986782) **429/429 PASS**, including 13/13 G60 tests; real OS `lstat` on disposable synthetic local files, **5/5 CLI scenarios PASS**. All exact-source GitHub Actions **4/4 SUCCESS**: offline MVP 40530986782, readiness 40530986838, master 40530986766, closeout 40530986899. The new local metadata operation is **not** NAS, Uliya registered Expert, Creator or customer-data proof. User agreed NAS 3h demo window **Nov 3–5 KST, conditional on preflight and owner activation approval**; earlier only when evidence gates pass. Creator for new FlowPilot NOT_EVIDENCED, real NAS/Agents NOT_RUN, 3h demo account issuance UNVERIFIED, entrant rights/release HOLD, Devpost NOT_SUBMITTED. Existing Skill exact SHA256 `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b` and draft PDF/ZIP unchanged. HAE, LA, REA_APP owner work untouched. Time actually spent not measured; 24-day plan 14 DONE/3 BLOCKED/7 NOT_STARTED refers schedule only.

# G60 — executable local synthetic filesystem MVP & NAS demo timing

2026-10-28 KST. **User agreed:** prioritize functionality and may accelerate if ready; plan to use general **3-hour UGOS demo Nov 3–5** rather than blindly activating Oct30. This is a conditional target, **not a booked appointment or guaranteed entitlement**.

## New implemented product slice
Run `python tools/flowpilot_local_file_mvp.py`. It creates an ephemeral sandbox of five synthetic scenarios, performs actual host-OS `lstat` metadata queries on *only exact specified relative paths* and feeds returned evidence through the existing FlowPilot planner→evidence pipeline. It rejects symlinks and path escapes; never reads document contents, never takes a user filesystem root, never contacts NAS or the Uliya SDK; output stays `HOLD` regardless of result. Scenarios: two files present, one file missing, competing final versions, explicitly **simulated** denial/truncation, actual disposable symlink target. It can demonstrate a genuine local metadata operation before spending the demo coupon, **not a NAS runtime result**.

## Existing sequence / no coupling
HAE and LA owner development can continue independently. **Do not copy or embed LA's Python runtime in the UGREEN Markdown Skill ZIP:** the UGREEN official contest Skill requires official supported registered Expert use. Optional product-level connector must undergo separate capability, rights and user authorization checks; it is not part of this Round1 MVP. REA_APP is an internal research tool, not part of NAS package.

## Conditional readiness before spending 180-minute demo
1. Official Creator new FlowPilot evidence is genuine and source/checker + rights are reviewed (not yet achieved).
2. User has an issued account and knows exactly how its timer starts (not yet evidenced).
3. Genuine demo supports Uliya installed Skill, permissions and registered file-agent, otherwise **NO-GO**.
4. Nonsecret disposable folder and exact expected file manifest ready; keep real customer material out.
5. Owner approves actual activation. Then T+00–15 capability, +15–35 file metadata, +35–75 three paths, +75–105 actual defect fix, +105–120 repeat; hold remaining 60 min for emergencies only.

**No real NAS, active coupon, official Creator, paid resource or Devpost submission used** by G60. Current Skill SHA256 remains `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b`. G60 expected 416+13=429 full repository regression tests; this is a TARGET pending same-source CI. The general demo and separate finalist NAS are not equivalent.
