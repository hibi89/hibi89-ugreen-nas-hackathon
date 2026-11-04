# G267 — new optional documents-only duplicate-candidate review Skill (owner-private)

2026-11-05 KST. A distinct, downloadable **private candidate** built from the exact unchanged G226 owner source using the official Uliya Skill Kit 0.7.3's authoring instructions. This was composed in ChatGPT and statically checked locally; it is **NOT** proof of officially supported WorkBuddy/Claude/Codex Creator invocation, live registered Expert operation, NAS readback, a SkillHub upload, rights clearance or release approval.

## Design alternatives and chosen new capability

A) Keep G226's existing `REVIEW_VERSIONS` filename/stat/hash comparison only. Zero new maintenance, but it cannot request the published dedupe-scanner's own candidate evidence. B) Add a **separate opt-in read-only `REVIEW_DUPLICATES`** mode mapping `ug-filemgr scan-dedupe` to registered `file-agent` on exactly one owner-selected `documents` folder, with explicit same-session duplicate scan approval. Choose B for **INTERNAL technical candidate evaluation only**, retaining immutable G226 as the fallback; no overwrite or participant final-release selection.

Authentic Kit catalog v2.0.0 lists `ug-filemgr` → `file-agent`, `scan-dedupe` effect `read`, required repeatable `path`, optional `scope=all|documents|images|videos|audio`. This Skill only permits `scope=documents`. The catalog does **not** declare `limit` or `max-depth` for this action. Therefore the Skill must **NOT delegate** without independently binding an exact owner folder, effective runtime rights, separately approved scan coverage and safe bounded operation; in unknown cases return `NOT_CHECKED`. No broad fallback, mutation, content read, save, auto-select or delete. A duplicate candidate is not an authoritative version decision. This adds a real Skill source-level supported read-only operation, not actual proof of NAS availability.

## Original sources, exact generated artifact and checker evidence

- G226 original immutable candidate ZIP SHA256: `fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803`
- Official untouched Kit 0.7.3 SHA256: `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`
- G267 **new alternative not submitted** ZIP SHA256: `fc87f625350e51e9d00122c89c2b6d92424759135e116c06ff0e67aa2d700feb`, filename `UGREEN_G267_READONLY_DUPLICATE_REVIEW_ALTERNATIVE_NOT_SUBMITTED.zip`, 12,109 bytes, exact four Markdown entries, zero executable/vendor Kit files:
  - `flowpilot-3/SKILL.md` SHA256 `b4d2f772b56670fc7f317ff12ef788a8131f1374953cdd9530998bfc98ac6b52`
  - `flowpilot-3/references/failure-and-disclosure.md` SHA256 `8d36e299119d6020c2e3045d2503e0a09e0a6fd70d00acdfbdf005fa00ad8165`
  - `flowpilot-3/references/modes-and-evidence.md` SHA256 `d7f327b974ab8efebffbff3b0724960cab380d3dfcf28eb2f3db465235f20678`
  - `flowpilot-3/references/workflow-council-and-repair.md` SHA256 `33aeff0f5d8531fd23861b34d4798efe988078bd2b2933ab78ce348ea03e6c19`
- **Actual bundled first-party** `node uliya-skill-kit/scripts/check-skill.mjs flowpilot-3/` against the new extracted G267 source: exit **0**, `static-pass`, errors **0**, warnings **0**, info **0**. Re-extracted **final produced ZIP** to a separate temporary folder, re-ran the first-party Checker exit 0 and checked every reported Markdown SHA256 against archive contents. Additional 13 source/catalog policy assertions passed and intentionally changing the no-depth-limit guard was rejected by a distinct local policy test, **not the vendor Checker**. Private evidence `UGREEN_G267_OPTIONAL_DUPLICATE_REVIEW_CHECK_EVIDENCE_PRIVATE.json` SHA256 `852a721831fa7fabb4bf2985aed40a8a83adc68e1f6db3637794caaa04ea8194`. No external service/NAS, private ZIP only local temporary container and linked conversation attachment; **not published to GitHub or automatically retained in Library**.

## Fixed total completion rubric and exclusions

G267 accepts **one distinct, previously missing official catalog-grounded Skill source capability**: safe opt-in documents-only duplicate candidate analysis in a new original G226-derived internal Skill alternative. The broader 15-point `Official Uliya Skill, Creator / first-party Checker and rights` category advances **11→12/15** based on direct new Skill authoring, bounded action contract, verified first-party static validation of the actual generated artifact, and preserved old fallback. Overall conservative internal management estimate **71→72/100**, not judge certification. Local six categories still **60/60**, real native Expert/NAS **0/20**, final release/Devpost **0/5**. Outstanding **28** comprises unproven supported Creator environment, final rights/license/participant sign-off **3**, native NAS **20**, and owner release/submission **5**. Do not count G267 again on later Checker runs or future asset copies.

New Skill source-level authoring and static Checker pass DO NOT establish that the `scan-dedupe` Expert is actually registered or will run, that any scan covers entire owner scope, or that rights/licensing, compliant Creator invocation, or NAS tests are complete. No production Vercel app in this project. **RELEASE HOLD / NAS NO-GO**.

## Rollback, original protection, future action

G226 original, G221 fallback, official Kit, old public canonical Skill and PDF remain intact. No private ZIP/Kit bytes placed in the public GitHub repo; only hashes, capability decisions and technical constraints. Invalidate the G267 management point by reverting this **documentation-only** acceptance commit if the original G267 private artifact cannot be retained or fails independent review. The user should retain/download the G267 alternative, or request an explicit private Library save; do not assume transient container storage is durable. Supported official Creator provenance and actual live NAS require independently authorized environment and evidence. Do not activate 3h NAS trial, upload, submit or claim official license.

