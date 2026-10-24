# G31 — G29 official-checker warning; revised standard-delegation candidate

**2026-10-25 KST. State:** G29 first-party checker **static-pass-needs-target-validation** (participant report); corrected G31 candidate **OFFICIAL_CHECKER_NOT_RUN**; NAS NOT_RUN; NOT_SUBMITTED.

## True G29 official checker result (no normalization to static-pass)

The participant ran the installed first-party `uliya-skill-kit/scripts/check-skill.mjs` on exactly `projectready-nas/SKILL.md`. Before/after SHA256 matched **c29317909544676b407e8c9cb92ab9c5ed80d2003a54d2e33c31ff4ffcb53764**. Process exit code **0**, but official JSON status **`static-pass-needs-target-validation`**, errors **0**, warnings **1**, info **0**, diagnostics **`DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE`**. The checker could not mechanically identify a standard `delegate` command and requests manual confirmation whether NAS expert delegation is necessary. Full participant-provided JSON was preserved in [G31_G29_PARTICIPANT_CHECKER_WARNING_20261025.json](evidence/G31_G29_PARTICIPANT_CHECKER_WARNING_20261025.json). This is a reported local execution, not a tool invocation from GitHub CI.

**Manual capability decision:** ProjectReady **does require** the declared `file-agent` (required folder evidence) and, upon separate owner approval, `document-agent` (optional document content). Claiming "no NAS expert required" would be false. The preceding G28 editorial removal of two example `delegate` calls left only prose procedure and is causally consistent with this exact warning. The original reviewed G22 SHA **770e08c6...** had a different participant-reported 0-warning result. Neither verdict transfers to another SHA.

## Isolated G31 repair, without dummy paths or unauthorized NAS calls

A new, **separately staged** `projectready-nas/SKILL.md` is retained at [checker_inputs/G31_20261025/projectready-nas/SKILL.md](checker_inputs/G31_20261025/projectready-nas/SKILL.md); previous G22 and G29 preserved.

- Exact G31 target **13,103 bytes**, SHA256 **cb69afb6525d1ca530f72b83ad26965c411ca02dfdbab97aa762d612d34d25a2**; Git blob SHA1 **6920557b80b4e3bf8bd4e575e4eff2e7c5290861**. Source bytes independently checked against the new Git blob.
- New one-Markdown ZIP **5,317 bytes** SHA256 **d916e01634c7f1f5a1cd29e7cd473c233dd10543d812c6bb4da844435682a965**, only `projectready-nas/SKILL.md`. These are local SHA and content tests, **not** a first-party static checker pass.
- The new Skill states canonical one-line syntax for both targets: `delegate --target file-agent --instruction` and `delegate --target document-agent --instruction`. Instruction symbols in command forms represent locally constructed **fully resolved runtime texts**, not literals or shell variables the expert can accept. Any input or reference left symbolic stops the dispatch. Never place demo paths or synthetic owner authorization into an actual command.
- Exact approved folder, checklist, candidate patterns, returned file references, document question, scope/read-only restrictions, separate document authorization, errors, completeness and permission state must be fully embedded in the instruction *before* delegation.
- Runtime ability to execute those commands, actual expert registration and effective permissions are still **unverified** and cannot be inferred from the checker outcome. If unavailable, stop as `NOT_CHECKED`. This repair is for documented orchestration and static recognizability, not a demonstrated NAS deployment.
- G29 10-question English proposal remains unchanged: 1 page, **362/500** answer words, PDF **5,136 bytes**, SHA256 **418a81aa56b47d8fe33a442414e2e76d711dc1bfd1cdb2a0df313073a8a5da77**. Delegation design and stated unknown live Agent permissions remain consistent with that Q7/Q8 proposal; do not rebundle or claim changed PDF.

## Before any submission

1. Provide the G31 one-file ZIP to participant Codex, extract the member and verify its exact G31 SHA. Run the **installed** official first-party checker only against G31 source and report full JSON, errors/warnings/info, exit, SHA before/after. If warning remains, evaluate on its merits; do not suppress diagnostics or fabricate success. Do not re-edit solely to chase a badge without safety benefit.
2. Check final SkillHub publication interpretation of runtime-composed command forms (the vendor forbids unresolved *static placeholders*) and original-work/third-party/tool/service licenses. Current command symbols are explicitly runtime variables, not static owner examples, but no independent legal/publication authorization is inferred.
3. Obtain human editorial, license, data-flow and exact PDF+ZIP release approval before Devpost. Real NAS / registered Expert Agent permissions remain for future runtime testing, not falsely certified for Round 1.

## Scheduling and evidence

The work maps to early work on 2026-10-25 for scheduled UGR-D16/D17 (Nov 8/9). Do not change their PARTIAL labels based solely on a draft checker fix. 24-day master still **DONE 2 / PARTIAL 12 / BLOCKED 3 / NOT_STARTED 7**, with 2026-10-25 UGR-D02 G1 real runtime BLOCKED (1.5h base + separate 1.5h reserve, ETA unknown). Earlier Oct24 finite work 100% completed, actual elapsed time not measured. Neither publication nor Devpost submission performed.
