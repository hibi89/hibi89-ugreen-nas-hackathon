# G28 — Editorially corrected official-Creator Round 1 draft (2026-10-25 KST)

**Decision:** Create a separate, immutable-source-preserving G28 release-candidate PREVIEW. This is not the previously validated G22 Skill and is NOT approved for submission. Run the new exact-SHA official Uliya checker on G28 before any sign-off. No direct NAS / Expert Agent calls, real customer data, license grant or Devpost submission.

## Verified first-party basis
UGREEN Round 1 permits exactly one Markdown entry point SKILL.md, the English ten-question PDF with no more than 500 substantive answer words, a ZIP under 10 MB, and no real NAS runtime demo. Official Creator usage is required, and later edits are expected to be rechecked where possible. The source initially came from the pinned official Creator review branch; the earlier disclosure-augmented G22 candidate was reported by the participant to pass the installed official checker with exact SHA, 0 errors/warnings/info. Details: G27, including full checker JSON. The release team cannot transfer that checker result to a newer edited SHA.

## Risk corrected
Two fully populated one-line commands marked SYNTHETIC EXAMPLE ONLY remain in G22. They are not proved prohibited, but UGREEN SkillHub publishing standards on left-over examples make them unnecessary editorial review risk. The G22 provenance paragraph also still says the disclosure-augmented Skill has not been rechecked, contradicted by the participant's G27 official receipt. Do not mutate the already-checked G22 source or reviewed Creator source.

## Implementation
- New tools/round1_editorial_release_preview.py reads the pinned G22 Skill and *participant-provided* G27 checker JSON. Enforce actual SHA-256 equality of the original checked member and exact static-pass 0/0/0 target schema.
- Fail closed unless the audited sample-command block and stale verification sentence match exact expected delimiters. Remove only two example commands and substitute a complete prose-only runtime construction procedure for file-agent and document-agent with scope, permissions, result evidence and stopping conditions. Require actual dynamically injected owner-approved paths/references/questions; prohibit any generic placeholder or fallback.
- Correct only the staged disclosure: G22 participant-reported official static-pass is now acknowledged, but **G28 further edited candidate has never been officially checked**.
- Generate a new isolated ten-answer English proposal using existing PDF utilities. Q8 distinguishes G22 static pass from G28 unvalidated edit and from missing Expert Agent/NAS run. Preserve canonical old proposal, older PDF/ZIP and original Creator outputs.
- Package exactly one projectready-nas/SKILL.md via existing deterministic ZIP builder and record new candidate SHA, ZIP and PDF digests, source SHA, word count, new checker NOT_RUN, owner rights/consent pending and Devpost NOT_SUBMITTED.
- New offline tests include source and receipt pinning, no example remnants, exact stale text replacement, refusal on unknown input changes, no repo writes, proposal word limits and repeatable ZIP bytes.
- New .github/workflows/round1-editorial-release-preview.yml generates an **artifacts-only** draft. Workflow does not download or execute first-party NAS tools, and does not submit to Devpost. Artifact retained for 7 days. No user secrets/NAS data are included.

## Acceptance and remaining gates
1. GitHub test suite and G28 workflow MUST pass, with a concrete resulting candidate SHA and no unapproved ZIP members. If failing, preserve G22 and repair G28 only.
2. Participant extracts the G28 one-member ZIP and checks its **new SHA** with the installed official Uliya checker, returns real JSON, exit code and pre/post SHA evidence. Prior G27 pass is not enough.
3. Editor/entrant reviews correct publication wording, original work and third-party/UGOS/SkillHub rights, user-folder authorization, unknown remote/local model processing, and mandatory Devpost PDF fields.
4. Only after verified new checker evidence and explicit human approval of final PDF+ZIP may Devpost submission begin. Real NAS/Expert Agent effective permissions are separate Round 2 risks. Mark as UNVERIFIED and don't claim tested.

## Schedule truthfulness
Associate editorial packaging with the already-PARTIAL original 2026-11-08 UGR-D16 and license/policy review with UGR-D17 (2026-11-09), both **advance work actually performed 2026-10-25**. Do not mark them DONE, inflate percentages, or erase 2026-10-25 UGR-D02 still BLOCKED G1 official CLI/Agent runtime gate. 24-day states remain **2 DONE / 12 PARTIAL / 3 BLOCKED / 7 NOT_STARTED**. October24 daily 100% completed originally assigned tasks, real elapsed hours NOT_MEASURED. October25 G1 base 1.5h, separate reserve 1.5h; external ETA unknown. Initial state of G28 CI is PENDING until actual URL/result verified. No production or Devpost changes.
