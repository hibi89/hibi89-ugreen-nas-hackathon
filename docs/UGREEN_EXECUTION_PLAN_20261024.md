> **본선 진출 시 조건부 작업표 (2026-10-24 KST 공시)**: [11/17~12/01 일별 보수적 예상시간·별도 예비·T/T+1 단일 NAS 24시간 창](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/UGREEN_FINALIST_DAILY_PLAN_20261024.md). **진출·배정 미확인 / 현재 ACTIVE 아님**. 예선 시간표 [별도 유지](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/UGREEN_DAILY_EFFORT_PLAN_20261024.md). 기본 32h+예비 20.5h=최대 52.5h, NAS 배정일은 2일 일반 시간을 **교체**해 54.5~58.5h 상한. 원격 할당은 11/22~28 PT 중 1일, 한국시간 통상 배정일 17:00~다음 날 16:59, 실제 이메일이 우선. 실 NAS 촬영 필요, 최종 공식 12/01 16:45 KST, 자체 목표 11/30 20:00 KST. 시간표는 완료 가능성 보장이 아니며 SDK/NAS 런타임은 현재 미검증.

> **2026-10-24 KST 최신 시간 예산 공시:** 사용자의 요청으로 기존 작업 일정에 일별 보수적 예상시간을 추가했다. **[날짜별 작업시간·예비·완료 기준](UGREEN_DAILY_EFFORT_PLAN_20261024.md)**이 시간 산정에 우선하며, 아래 과거 worker 일정/고정 G0~G8 날짜는 *작업 범위 이력*이다. 현재 UGREEN은 SDK CLI 미검증 차단 상태다. 11/10 내부 조기 제출은 조건부이며 안전 달성으로 약속하지 않는다. 공식 11/16 16:45 KST는 변경 없다.

# ProjectReady NAS — APPROVED UGREEN DELIVERY PLAN
2026-10-24 KST | Status: user-approved PRODUCT/PLAN, not a tested implementation.
Owner: UGREEN lead, lead/ugreen. Other hackathon schedules intentionally excluded.

## Product fixed by the user
ProjectReady NAS (working title), one Uliya AI Skill, track: Automate Your Workflow.
Target user: a freelancer or small production team preparing a project folder for customer delivery.
User request: "Is this project ready to deliver?"
Distinctive value: compare a specified client delivery contract/checklist against actual permitted NAS files/documents, attach evidence for each requirement, explain blockers, and give a Go/No-Go decision. Not just a generic duplicate-file cleaner.

Flow: user grants folder scope and supplies mandatory deliverables -> supported registered Expert Agents and UGOS CLI read permitted files/documents -> missing deliverables, competing versions, and permitted information-disclosure concerns are checked -> evidence-based READY / BLOCKED / NEEDS_REVIEW report.
Every required criterion has PASS, FAIL, REVIEW or NOT_CHECKED status and a file/document reference or explanation. A required NOT_CHECKED must never produce READY. Read-only by default; never auto-delete, move, upload, share, or expose user data. No calls to undocumented CLI. Hash comparison, deep content inspection, local AI and PII detection are conditional on real Starter Kit support.

Data contract to refine at G2: input {authorized_folder, required_deliverables, scan_scope}; observation {requirement_id, supported_capability, evidence_refs, observed_value, confidence_or_uncertainty}; output {requirement_id, check_type, verdict, evidence_refs, limitation, next_action}. Not actual Uliya API syntax.
Separate reads from writes: v1 stores no new customer data and has no permanent custom DB. Repeat reads should not mutate or widen privileges. Partial failures return NOT_CHECKED and explicit next actions.

## [LATEST APPROVED EXECUTION POLICY — 2026-10-24 KST]

**Parallel across competitions; sequential inside each competition.** UGREEN has exactly one active feature worker at a time. Current active worker: **NONE**. The older three-worker concurrent-development plan is superseded. W1 Oct 28-29 -> W2 Oct 30-31 -> W3 Nov 1-2, with lead verification before each handoff; lead integration Nov 3-5. No change to the Nov 10 early submission or the Nov 16 official deadline. See docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md.

## Dated checkpoints — KST
| Date | Gate / work | Measurable acceptance |
|---|---|---|
| 10/24 | G0: product and budget fixed | This user-approved GitHub document exists; technical implementation not yet claimed |
| 10/25-26 | G1: official package capability study | Obtain and inspect actual UGREEN Skill Developer Package, supported commands, Expert Agent registration, allowed permissions, model/data-flow/price conditions; list confirmed vs unknown |
| 10/27 | G2: architecture freeze | Contract checklist-to-file-evidence-to-verdict, permissions, recovery and unsupported-function behavior defined using real supported capabilities |
| 10/28-29 | G3a: W1 missing-files ONLY | Evidence-based missing deliverables check and tests, lead-reviewed handoff |
| 10/30-31 | G3b: W2 version-conflicts ONLY | Candidate version conflict and uncertainty results; W1 inactive |
| 11/01-02 | G3c: W3 privacy ONLY | Supported security/data handling checks; W1/W2 inactive |
| 11/03-05 | G4: lead integrates one Skill | SKILL.md and directly referenced Markdown; trace synthetic contract -> evidence -> decision. No active feature worker |
| 11/04-06 | G5: validation | Official creation-tool checks if accessible; synthetic completed/missing/version/permission-denied/empty-result tests; record PASS/FAIL and untested |
| 11/07-08 | G6: English proposal | Ten required answers, <=500 English words (internal target 430-470), PDF <=1 MB; differentiate from existing file tools with clear real-world use |
| 11/09 | G7: release candidate | PDF/ZIP size, structure, AI/third-party disclosure, no secrets/PII, file checksum/backup verified |
| 11/10 | G8: early final submission | Create Devpost project, submit PDFs/ZIP, confirm final receipt not just draft; user retains ultimate decision |
| 11/11-16 | Buffer | Fix only evidenced problems, revalidate receipt before official deadline **2026-11-16 16:45 KST** |

The dates are execution targets when each AI chat is called, not unattended automation. If G1 is blocked, investigate cause, retry once with a materially better approach, then pivot to official free support or a supportable flow. Scope reduction, new cost, privacy/permission change requires user approval.

## Worker responsibilities
- feature/missing-files: map each explicit delivery requirement to actual authorized file evidence; distinguish absent from not searched and ambiguous rules.
- feature/version-conflicts: competing deliverable/version candidates; explain evidence and request user confirmation rather than assuming newest based on filename. Never invent hash or version-history APIs.
- feature/privacy: read permissions and unauthorized transmission guardrails; PII scanning only if officially supported. If not checked, state that clearly; never claim that a file is safe.
- lead/ugreen: official tool/capability evidence, input/output contract, integration, ZIP/PDF, 4 judging dimensions, Devpost receipt, reporting.
Assignments: docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md. **Workers operate strictly sequentially (one active at a time).** Each worker reads its own branch HANDOFF / STATUS / AGENTS / REQUIREMENTS / OPERATIONS, and returns results via TO_UGREEN_LEAD.md. No AI chat starts automatically.

## Tests and judging
CORE1: 7 mandatory deliverables present with usable evidence -> READY only if all required checks were performed.
CORE2: 2 missing deliverables plus 2 conflicting final versions -> BLOCKED or NEEDS_REVIEW with evidence and concrete action.
EDGE1: access denied, partial folder search, unsupported CLI, missing PII analyzer -> NOT_CHECKED, no fabricated completion.
Also check repeat execution leaves source unchanged. Assess each official 25% dimension: user value, meaningful differentiation, technical quality, NAS feature fit. Judge score or finalist probability is not yet known.

## Submission contract
Round 1: English 10-answer PDF <=500 words and <=1 MB. One ZIP with SKILL.md and directly linked references/*.md only. Frontmatter name lowercase hyphenated length 2-64; description <=1024 characters. ZIP compressed/uncompressed each <=10 MB; each file <=1 MB; <=100 files. No separate scripts, executables, manifests, binaries. List AI tools, sources/licences, third-party components and external flows. No real credentials or personal data.
NAS hardware, code repository link and demo video are NOT required in Round 1. Only one project per individual/team.
Round 2 if invited (up to 30): Nov 21 PT invitation; one free remote NAS iDX6011 Pro testing day Nov 22-28 PT; install/test/record same Skill; submit final ZIP and <3-minute public YouTube demo with English narration or full English subtitles by Dec 1 16:45 KST. Take backups before remote access expires.

## Budget — zero new cash spend target
| Item | Additional planned cash |
|---|---:|
| Devpost entry and official dev resources | KRW 0 |
| Existing GitHub and available AI subscription | KRW 0 additional |
| New paid APIs, new hosting, domain, DB | KRW 0 (do not use) |
| PDF/ZIP creation with free tools | KRW 0 |
| Purchase of NAS / finalist free remote NAS | KRW 0 |
| Free screen recorder/editor and YouTube if finalist | KRW 0 |
| Total incremental payment target | **KRW 0** |

Existing subscriptions, electricity, internet, own labor, prize taxes/transfer fees excluded; actual model access and included quotas must be verified. No paid action without explicit approval.

## State and source
Verified: registration screen provided by entrant, official contest requirements, GitHub branches and original planning documents. Still UNVERIFIED: actual downloaded package internal CLI, PII/version functionality, API, skill running on NAS, Devpost project creation and final submission, CI and deployment.
Official rules: https://ugreenhackathon.devpost.com/rules
Official package: https://ai.ugreen.com/pages/hackathon-starter-kit


## [LATEST 2026-10-24 KST] Single reusable worker chat / rotating branch assignment
- Within UGREEN, ONE worker chat reads lead/ugreen/docs/dispatcher/CURRENT_TASK.md each turn and switches role/feature branch according to the one READY Task. Three worker roles do NOT require separate chat rooms.
- Current READY UGR-001, feature/missing-files, official Uliya Skill Kit evidence inventory by Oct 26. Then lead G2 architecture check; UGR-002 missing-files, UGR-003 version-conflicts, UGR-004 privacy are WAITING. The worker never executes BACKLOG just because the date arrives.
- Worker reports evidence/commit SHA in its own feature TO_UGREEN_LEAD, then lead reviews and issues next READY. The same worker chat can continue. No automatic alert, unattended execution or hard GitHub mutex.
- References: [worker start](WORKER_START_HERE.md) / [current task](dispatcher/CURRENT_TASK.md) / [backlog](dispatcher/BACKLOG.md). Schedule/internal 11/10 and official 11/16 unchanged.


## 2026-10-24 KST — 총괄·개발자 역할 통합 전면 개편(현행)
- 사용자 결정: 통합 총괄 1개 + UGREEN/KIC/PayPal 총괄 각각 1개, **전체 4개 채팅**. UGREEN 총괄이 단일 대화에서 직접 조사/설계/구현/테스트/검수/통합/제출 수행. 별도 순환 작업자 및 GitHub READY 디스패치 폐기.
- `lead/ugreen`은 향후 직접 개발·문서·검증의 기본 브랜치. 세 feature 브랜치는 원본 보존(삭제·force push 금지), 검증 후 선택적 소스 통합. `main`은 테스트 뒤 안정된 통합 기준으로 관리. 기존 `docs/dispatcher/CURRENT_TASK.md`, `BACKLOG.md`, `DISPATCH_PROTOCOL.md`, `docs/WORKER_START_HERE.md`는 읽기 전용 역사 기록이고 새 작업 호출 권한 없음.
- 기존 UGR-001 `feature/missing-files@4e74dc7b187e70ad72e906e042fdbf4c140940f8`: `SDK_CAPABILITY_MATRIX.md` 생성, `TO_UGREEN_LEAD.md`에 **BLOCKED(archive 내부 CLI/Expert Agent 등록·NAS 실 실행 미확인)** 보고. 공개 공식 문서 범위의 기술 표만 완료했고 SDK 런타임 성공 아님. 중복 다운로드 재시도 대신 공식 다운로드 가능 경로/지원팀/개인 소유 라이선스 문서 접근 등 다른 방법 검토. 다음 UGR-002 자동 착수 금지.
- 총괄 이전 기여: `docs/roles/lead/ROUND1_COMPLIANCE_AUDIT_20261024.md` 공식 공개 규정 점검. 새 `LEAD_ACTIVE_WORK.md`는 위 SDK 차단 해결·지원 CLI 증거 확보·G2 데이터 계약을 현재 1순위로 기록. 예선 기술 제약 검증 전 명령/버전/PII 기능 창작 금지.
- 내부 조기 제출 2026-11-10 KST, 공식 Round1 2026-11-16 16:45 KST. 실 NAS/CLI/CI/Devpost 제출 미완료. 추가 신규 지출 0원, 개인정보 외부 전송 승인 없음.
- 전환 전 기준 `lead/ugreen@b1a055911bf8a31d0643873507cdc52dccb67495`, `main@d8cd806cb2b3842a80a571fd09910ec370e2de17`. 새 커밋 SHA는 GitHub 원격 조회 결과를 최종 사용.
