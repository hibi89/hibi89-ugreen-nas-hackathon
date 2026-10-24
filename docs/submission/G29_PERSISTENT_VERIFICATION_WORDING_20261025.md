# G29 — Persistent checker-provenance wording, not a self-expiring validation claim (2026-10-25)

**Decision:** Fix the already-CI-passing G28 editorial preview's final wording *before* requesting a participant to rerun the official checker. A sentence claiming "this new candidate has not been officially checked" would immediately become outdated after that check. It must not be embedded in a release Skill or a released proposal.

## Evidence already completed for first G28 iteration
- G28 build [CI 40109705431](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40109705431) PASS (8 offline unit cases, isolated ZIP/PDF generated and verified). Same-push original builder, offline, master and closeout CI PASS.
- GitHub artifact 12566141077 independent wrapper ZIP 12,237B SHA256 5a901b063c1ebe79b6b23a16f9f6d5bb2ad86dd7077cfc3aebf962e9fabc0f3e.
- Earlier, **superseded** G28 candidate Skill 11,207B SHA256 cfbee5563b84c82b75abc83a67568bd6b428dcdeb87353113a657f3e83e24705; one-markdown ZIP 4,611B SHA256 d2ada82aff96951d52f7faf9e424e7cf1cbd1f58aaaf58307c63f98037cdaa46.
- Earlier PDF 5,143B SHA256 b5399115ad56e28d41ba481221a2cf31cfc7ba6cb502c264304fc264f198e5d0, one page, ten fully rendered answers, 361/500 substantive words, separate disclosures and no clipping on 150-dpi visual check. These are only offline draft tests, not official checker evidence.

## Targeted G29 P1 correction
- In the Skill's provenance, replace the time-sensitive statement saying the *new* version has not been checked with a durable rule: the participant-reported G22 static-pass covers only the pinned G22 hash; later revisions require their **own exact SHA and separate official checker evidence**. This remains true after the new candidate is checked.
- In the PDF Q8, replace "this version needs its own recheck" with the version-stable factual rule "every edited Skill requires checker evidence tied to its exact SHA". Current lack of registered Agent/NAS runtime remains explicitly unverified.
- Keep **external staging-only manifest** truthful at this moment with new candidate official-checker status NOT_RUN_NEW_SHA; upon receiving the actual official receipt, update reporting/approval evidence **without changing the Skill or proposal bytes**.
- The source root G22 official-checked member SHA256 770e08c6eb5101785579eed7f2438547e0a0386d4c35aead860aab088e091169 and participant checker JSON remain untouched. No vendored SDK/NAS/customer-data/Devpost action.
- Update source, unit assertions, workflow cross-check, handoff and canonical 24-day JSON/rendered progress atomically. All new code CI checks are **PENDING until verified**, never described as passed from editing alone.

## After CI (hard gates)
1. Independently read the new GitHub artifact bytes, verify member list = one projectready-nas/SKILL.md, new exact SHA, manifest status, PDF page/500-word limit and actual page layout. The old G28 SHA is obsolete.
2. Participant may then run the installed Uliya official checker once against that **new exact SHA**. Return JSON, exit code, and before/after SHA. No further wording edits are needed solely to reflect checker PASS; update evidence files only.
3. Human still must approve third-party/original rights, applicable UGREEN/SkillHub rules and local/cloud model data-flow representations, and explicitly approve final PDF+ZIP before Devpost. G1 registered Expert Agent/CLI live permissions and NAS runtime remain separate externally BLOCKED/not tested.

## Timing and project status
Advance work dated October 25, with planned scope mapped to UGR-D16 (Nov 8) and UGR-D17 (Nov 9); those work items remain PARTIAL. 24-day master **2 DONE / 12 PARTIAL / 3 BLOCKED / 7 NOT_STARTED**. October 24 original-day 100%, observed time NOT_MEASURED. October 25 original G1 CLI/Agent gate still BLOCKED with 1.5h base + 1.5h separate reserve. No trustworthy actual completion ETA. Candidate NEVER submitted.
