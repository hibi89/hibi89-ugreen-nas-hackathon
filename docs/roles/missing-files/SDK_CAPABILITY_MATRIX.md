# UGR-001 — Uliya SDK Capability Matrix

Checked: 2026-10-24 KST. Branch: `feature/missing-files`. Dispatch revision: 1. Baseline SHA: `9b3052bf82ad1a8a4844b1aeee699c0b759251dc`.

**Definitions:** CONFIRMED = directly documented by official public source (not runtime validated); UNSUPPORTED = explicitly forbidden by official rule; UNVERIFIED = no package-specific evidence or execution. **Important:** The official Starter Kit §6 says the contents of the creation-tool archive take precedence over its public capability examples. Package contents were not retrieved here.

## First-party evidence register

- **S1**: [UGREEN Hackathon Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit), §2 assistant support, §3 archive download, §5 Skill design, §6 capabilities, §7 test, §8 compliance.
- **R1**: [Official Devpost Rules](https://ugreenhackathon.devpost.com/rules), §4 Project Requirements, Round 1 and Round 2 Submission Requirements, §6 Judging.
- **R2**: [Official Devpost Overview](https://ugreenhackathon.devpost.com/), Round 1 ZIP limits; the Rules take precedence where wording differs.
- **P1**: [UGREEN SkillHub Safety & Publishing Standards](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec), Articles 2–8 and 10.
- **P2**: [SkillHub User Agreement](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-user-agreement), Articles 7–9; absent licenses do not imply redistribution permission.
- **P3**: [SkillHub Privacy Policy](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-privacy-policy), §§I–III; this documents SkillHub, not model inference locality.

## Capability evidence matrix

| Subject | Status | Evidence, exact limitation, and gate |
|---|---|---|
| SDK/tool name | CONFIRMED | S1 §3: **UGOS Skill Creation Tool**; extracted folder *usually* `uliya-skill-kit`. This is not a CLI command. |
| Package exact filename / version / manifest / SHA256 / license | UNVERIFIED | Official archive bytes not fetched. No package version/hash asserted; do not publish the archive in Public GitHub. |
| Download link | CONFIRMED | S1 §3 has a Shopify CDN archive link, but downloadable ZIP contents remain UNVERIFIED in this environment. |
| Authoring assistants | CONFIRMED | S1 §2 explicitly lists WorkBuddy, Claude, Codex. Other tool environments may lack features. |
| Skill standard | CONFIRMED | R1 Round 1: `SKILL.md` required with `name` (lowercase hyphenated, 2–64 chars), `description` (≤1,024 chars), user goal, inputs, supported CLI/expert orchestration, success and failure handling. |
| References and package layout | CONFIRMED | R1 allows Markdown under `references/`, directly linked from `SKILL.md`. S1 shows optional README as a development suggestion, NOT confirmed as allowed submission ZIP content; exclude README from contest ZIP absent clarification. |
| ZIP limits | CONFIRMED | R1: compressed ZIP ≤10 MB; R2 adds decompressed ≤10 MB, each file ≤1 MB, ≤100 files. P1 Art.5 prohibits ZIP slip, symlink escape, unsafe archives. |
| File category | CONFIRMED | S1 §6 lists find, browse, organize, deduplicate, tag. **Category only**, not precise callable command or output type. |
| Document category | CONFIRMED | S1 §6 lists read, answer questions, extract, translate, reconcile. Supported formats/OCR/read result schema UNVERIFIED. |
| Chained workflow | CONFIRMED | S1 §§5–6 permits chaining actual supported capabilities, using previous step's true output and explicit no-results handling. |
| Registered Expert Agent requirement | CONFIRMED | R1 Project Requirements explicitly requires supported UGOS CLI through registered expert agents. |
| Agent registry, invocation syntax, exact CLI commands | UNVERIFIED | S1/R1 give no verified command names, flags, agent IDs, argument types, return JSON or error codes. **Do not substitute unrelated UGOS native-app `ugcli` commands.** |
| NAS files: path, search, listing output, paging | UNVERIFIED | S1 provides high-level capability but no parameter/response schema, authorized directory ID format, ACL enforcement, pagination or errors. |
| File version/mtime/hash/etag | UNVERIFIED | No first-party evidence guaranteeing version or checksum metadata. Version-conflict feature cannot depend on imagined fields. |
| Authorization/consent API details | UNVERIFIED | P1 Art.4 requires minimal user-authorized scope and consent, but does not give the Skill CLI permission grant schema. |
| File delete/move/overwrite without confirmation | UNSUPPORTED | S1 §5 and P1 Art.4 require explicit confirmation before high-risk actions. Proposed UGR-001 use remains read-only. |
| Arbitrary scripts/runtimes/direct NAS access | UNSUPPORTED | R1 Project Requirements expressly excludes custom executables, general-purpose runtimes and unauthorized direct NAS resource access. |
| Probing secret paths, files of others, .env/keys | UNSUPPORTED | P1 Articles 4 and 7 prohibit unauthorized private data access and secret file discovery. |
| Local AI model option | CONFIRMED | R1 encourages NAS local model but does not require it. Exact runtime model IDs, inference endpoint, quota and prices UNVERIFIED. |
| Third-party model option | CONFIRMED | R1 permits properly authorized external models subject to data rights, terms and disclosure; P1 Arts.4,6 require consent before transmission. Specific API availability/cost UNVERIFIED. |
| PII handling and external transmission | CONFIRMED | P1 Arts.4,6,10: scope minimization, clear disclosure/permission, no covert external transmission. **UNVERIFIED** whether chosen Skill processing stays local; P3 alone cannot prove local inference. |
| Rate limit, SDK usage price, model token billing | UNVERIFIED | R1 says hackathon entry and finalists' assigned NAS test are free; no promise of free unlimited external API usage. New cash spending budget: 0 KRW. |
| Official kit validator, actual NAS, Sandbox | UNVERIFIED | S1 §7 mandates tool check; finalists only get real NAS access. No command, official validator, NAS device, or API was exercised in this task. |

## Access attempts and test evidence

1. Read `lead/ugreen` CURRENT_TASK revision 1, target branch records, verified feature HEAD equals `9b3052bf82ad1a8a4844b1aeee699c0b759251dc`.
2. Loaded first-party Starter Kit, official Devpost rules and SkillHub policy pages. These are **document inspection PASS**, not SDK/API test passes.
3. Official S1 §3 archive hyperlink located. Page extraction returned an internal error on the binary hyperlink; isolated runtime HTTP request failed because of DNS resolution for `ai.ugreen.com`. No ZIP archive data was received. This is a **tool/environment limitation**, not evidence UGREEN's download is broken.
4. SDK validator: **NOT RUN**; CLI commands: **0 executed**; real NAS: **NOT AVAILABLE**; model API calls: **0**; package SHA/hash: **NOT MEASURED**. Security-sensitive data published: **none**. Additional spend: **0 KRW**.

## Competing designs (not implementation)

| Criterion | Option A: checklist vs authorized file names | Option B: AI-assisted document analysis |
|---|---|---|
| Flow | User selects authorized root and required relative paths → *officially confirmed* file enumeration → compare → present/missing/inaccessible with evidence | Same plus *officially confirmed* document read + AI inference |
| Cost | Target zero paid external APIs; actual NAS usage unverified | Model/token cost unknown |
| Performance | Less data read, not measured | More I/O and inference, not measured |
| Privacy | Metadata-only, no external transfer, read-only | Document content and PII exposure controls needed |
| Maintainability | Small deterministic contract | Extra agent/model/data dependencies |
| Recommendation | **Option A pending exact CLI verification and lead approval** | Defer |

**Proposed logical fields only (NOT SDK schema):** authorized_root, expected_relative_paths, seen_paths, missing_paths, inaccessible_paths, checked_at, error_codes, evidence.

## BLOCKED gate and free recovery

**UGR-001 is BLOCKED for package-level CLI/Agent validation.** Public capability/regulatory investigation is documented, but do not claim an operational NAS Skill. No UGR-002 work authorized.

1. Preferred 0 KRW route: an authorized participant/lead obtains the official archive privately, inspects its license, command catalog, registered-agent definitions, input/output examples, validator and hashes. Upload only an owned summary or permitted reference excerpts to Public GitHub, never the unverified proprietary archive or credentials.
2. Fallback: ask official UGREEN community/support for official public text references to permitted CLI commands and Agent registry.
3. Require first-party proof of exact list/read commands, permissions, failure semantics and model/data flow before any real Skill orchestration. User/lead approval required before any content externalization, scope expansion or expense.
