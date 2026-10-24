# G6 preliminary Markdown Skill candidate (2026-10-24 KST)

**Status: OFFLINE_CANDIDATE / OFFICIAL_VALIDATOR_NOT_RUN / NAS_NOT_RUN / NOT_SUBMITTED.**

## Design comparison and approved-scope decision
A) Markdown-only read-only Files/Documents Skill candidate: free, consistent with first-party public high-level features and Round 1 Markdown packaging, small maintenance surface. B) Python adapter bundled with Skill: could give deterministic checks but not permitted in the Round 1 ZIP and cannot yet be mapped to verified Uliya CLI. **Chosen A, only as provisional offline draft.** This does not reduce the requirement for official tool validation before submitting.

## Work
- `skill/projectready-nas/SKILL.md` describes owner-authorized scope, exact file checking, complete pagination, version ambiguity, separately authorized document reading and privacy NOT_CHECKED rules.
- `skill/projectready-nas/references/decision-policy.md` is the sole directly linked Markdown reference.
- `tests/test_skill_candidate.py` adds 6 offline structural/safety assertions. These tests never invoke Uliya, NAS, PII scanning or the official creation-tool checker.
- Public sources: https://ai.ugreen.com/pages/hackathon-starter-kit §§3,5–7; https://ugreenhackathon.devpost.com/rules ; https://ugreenhackathon.devpost.com/resources .
- No official CLI names/registered Expert Agent IDs or file I/O schemas inferred. Exact tool compatibility, validator and license text remain G1 **BLOCKED**.
- Intended original target of Markdown integration 11/03–04; actual draft produced early 10/24. Official integration, SDK checker and real NAS checks are still pending. Day 10/24 already closed at 100% of its fixed deliverables; this advance is separately recorded. Actual developer time not measured, cash spend 0.
