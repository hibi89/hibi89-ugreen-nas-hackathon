# UGREEN NAS FlowPilot — FIXED REAL-WORLD TOOLCHAIN
2026-10-27 owner correction: exact programs/tools, no added pre-submission scope. ONE contest-native Skill, not n8n service. Initial Devpost deadline Nov16 16:45 KST; same project finalist device test and video if selected. New Skill must be newly authored during contest; old G36/G37 ProjectReady snapshots not overwritten.

## A. Submission tools
| Area | Concrete selected tool/program | Scope and gate |
| --- | --- | --- |
| Authoring | OFFICIAL UGREEN UGOS/Uliya Skill Creation Tool from https://ai.ugreen.com/pages/hackathon-starter-kit, using supported Codex editor/assistant | Official validation/capability reference; user's own original reviewed work and third-party licensing remain mandatory |
| Skill source | Markdown with YAML frontmatter SKILL.md and directly linked references/*.md only | Package cannot contain standalone scripts/manifest/README/bin or extra executable files |
| AI conversational runtime | Uliya platform built-in Agent dialogue and official Skill dispatcher | The agent asks for missing folder/checklist/content-consent in normal-language messages; no custom UI/JS code |
| NAS file tools | Registered file-agent, official catalog ug-filesystem ls/find/stat and optionally sha256sum | Only owner-authorized folder + actual installed capabilities, source references, no arbitrary shell |
| NAS document tools | Registered document-agent, catalog ug-document metadata/qa/extract/reconcile | Owner-approved exact selected files and real runtime permission; no browsing unrelated folders |
| Logic | Deterministic Markdown policy: authorized-folder scope, input-slot table, required file checklist, PRESENT/MISSING/NOT_CHECKED and READY/BLOCKED/NEEDS_REVIEW | One handoff audit workflow; no arbitrary general-purpose DAG builder |
| Offline source checks | Python 3.11+ stdlib unittest, pathlib, hashlib, zipfile, optional existing text assertions in repository | Scripts only developer-side, NEVER inside final Skill ZIP |
| Proposal PDF | ReportLab for new English 10-answer PDF rendering, pypdf for page/size inspection; final visual/human review | <=500 substantive English words, <=1 MB PDF, original compliant source and explicit AI/tool/licensing disclosure |
| ZIP package | Python stdlib zipfile + independent extract/list/size/path/reference/hash checks | <=10MB compressed+uncompressed; each file <=1MB, <=100 files; only SKILL.md and directly linked Markdown refs |
| Git/QA | Existing GitHub lead/ugreen, existing offline GitHub Actions QA | Old G36/G37 ProjectReady 269 pass is not NAS runtime / new FlowPilot pass |
| Submission | Devpost Round1 exact user-approved PDF+ZIP, stored hash and confirmed receipt | Actual NAS not required for Round1 |
| If finalist | UGREEN-issued temporary NAS iDX6011 Pro, official Uliya runtime and Skill validator, OBS Studio recording and public YouTube <3-minute real-device video, final ZIP | Only one assigned remote NAS day, same Skill; no faked NAS footage |

## B. What it builds
User asks "check my project handoff". Uliya asks exact user-authorized project folder, explicit checklist, optionally exact content-read consent; it previews a bounded sequence, uses actually registered file/document READ actions and shows item evidence, version conflicts, source completeness and READY/BLOCKED/NEEDS_REVIEW. Incomplete listing or unavailable permissions => not checked and no invented verdict. Restricted secret filenames are never expanded and untrusted content doesn't become instructions.

## C. NOT part of contest Skill
NO n8n Docker/REST/JSON wrapper; NO AX_FLOW scheduler/engine; NO generic Python/JS scripts in package; NO full SOVIA/DBVORA runtime; NO Ollama/Whisper/Immich/Flowise stack, external vector DB, unsanctioned local model integration, arbitrary file mutations, always-on notifications. These can be **postcontest NAS app research** only after sponsor capabilities, rights and hardware verified. UGREEN's official document says to use registered Expert Agents and Markdown Skill rather than general-purpose runtime. Do not promise an unsupported UI/feature.

## D. Rights/blockers
Official Skill Kit vendor terms and creator-output rights requested by user via email; response not verified. Must not assume cleared. This final-toolchain document does not certify runtime registration, generated-source originality, model local-only data flow, or an uploaded Devpost entry. Owner approves exact artifacts and legal disclosure. Keep G36/G37 originals.

Official: https://ugreenhackathon.devpost.com/rules and https://ai.ugreen.com/pages/hackathon-starter-kit .
